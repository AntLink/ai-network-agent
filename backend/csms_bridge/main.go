package main

import (
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"net/http"
	"os"
	"os/exec"
	"sort"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

var version = "0.3.0"

const (
	shmFlagReadOnly = 0x1000

	gpsdKey  = uint32(0x47505344)
	ntpKeys  = uint32(0x4E545030)
	ntpCount = 8
	gpsdSize = int64(26 * 1024)
	ntpSize  = int64(80)

	maxReadSize    = int64(1 << 20)
	minSweepPoints = 8
	minFreqHz      = 1e3
	maxFreqHz      = 20e9
	minPowerDbm    = -180.0
	maxPowerDbm    = 60.0

	udpRingSize      = 1000
	maxUDPPacketSize = 65507
)

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		log.Printf("json encode error: %v", err)
	}
}

type GPSData struct {
	Latitude   float64   `json:"latitude"`
	Longitude  float64   `json:"longitude"`
	Altitude   float64   `json:"altitude"`
	Satellites int       `json:"satellites"`
	Fix        bool      `json:"fix"`
	Timestamp  time.Time `json:"timestamp"`
}

type NTPData struct {
	Server   string    `json:"server"`
	OffsetMs float64   `json:"offset_ms"`
	DelayMs  float64   `json:"delay_ms"`
	Stratum  int       `json:"stratum"`
	Synced   bool      `json:"synced"`
	LastSync time.Time `json:"last_sync"`
}

type SystemData struct {
	Hostname   string    `json:"hostname"`
	UptimeSec  int64     `json:"uptime_sec"`
	CPULoadPct float64   `json:"cpu_load_pct"`
	MemTotalMB int       `json:"mem_total_mb"`
	MemFreeMB  int       `json:"mem_free_mb"`
	Version    string    `json:"version"`
	Timestamp  time.Time `json:"timestamp"`
}

type SharedSegment struct {
	Key   uint32 `json:"key"`
	Name  string `json:"name"`
	Shmid int    `json:"shmid"`
	Size  int64  `json:"size_bytes"`
}

type SweepPoint struct {
	FrequencyHz float64 `json:"frequency_hz"`
	PowerDbm    float64 `json:"power_dbm"`
}

func keyName(key uint32) string {
	b := []byte{byte(key >> 24), byte(key >> 16), byte(key >> 8), byte(key)}
	for _, c := range b {
		if c < 0x20 || c > 0x7e {
			return fmt.Sprintf("0x%08X", key)
		}
	}
	return string(b)
}

func knownSegments() []SharedSegment {
	segs := []SharedSegment{{Key: gpsdKey, Name: keyName(gpsdKey), Size: gpsdSize}}
	for i := 0; i < ntpCount; i++ {
		k := ntpKeys + uint32(i)
		segs = append(segs, SharedSegment{Key: k, Name: keyName(k), Size: ntpSize})
	}
	return segs
}

func procSegments() []SharedSegment {
	data, err := os.ReadFile("/proc/sysvipc/shm")
	if err != nil {
		return nil
	}
	var segs []SharedSegment
	for i, line := range strings.Split(string(data), "\n") {
		if i == 0 {
			continue
		}
		f := strings.Fields(line)
		if len(f) < 4 {
			continue
		}
		kv, err := strconv.ParseInt(f[0], 10, 64)
		if err != nil {
			continue
		}
		shmid, err := strconv.Atoi(f[1])
		if err != nil {
			continue
		}
		size, err := strconv.ParseInt(f[3], 10, 64)
		if err != nil {
			continue
		}
		key := uint32(int32(kv))
		segs = append(segs, SharedSegment{Key: key, Name: keyName(key), Shmid: shmid, Size: size})
	}
	return segs
}

func ipcsSegments() []SharedSegment {
	out, err := exec.Command("ipcs", "-m").Output()
	if err != nil {
		return nil
	}
	var segs []SharedSegment
	for _, line := range strings.Split(string(out), "\n") {
		f := strings.Fields(line)
		if len(f) < 5 || !strings.HasPrefix(f[0], "0x") {
			continue
		}
		kv, err := strconv.ParseUint(strings.TrimPrefix(f[0], "0x"), 16, 64)
		if err != nil {
			continue
		}
		shmid, err := strconv.Atoi(f[1])
		if err != nil {
			continue
		}
		size, err := strconv.ParseInt(f[4], 10, 64)
		if err != nil {
			continue
		}
		key := uint32(kv)
		segs = append(segs, SharedSegment{Key: key, Name: keyName(key), Shmid: shmid, Size: size})
	}
	return segs
}

func mergeSegments(primary, fallback []SharedSegment) []SharedSegment {
	byKey := map[uint32]*SharedSegment{}
	var order []uint32
	add := func(s SharedSegment) {
		if ex, ok := byKey[s.Key]; ok {
			if ex.Shmid <= 0 {
				ex.Shmid = s.Shmid
			}
			if ex.Size <= 0 {
				ex.Size = s.Size
			}
			if ex.Name == "" || strings.HasPrefix(ex.Name, "0x") {
				ex.Name = s.Name
			}
			return
		}
		cp := s
		byKey[s.Key] = &cp
		order = append(order, s.Key)
	}
	for _, s := range primary {
		add(s)
	}
	for _, s := range fallback {
		add(s)
	}
	out := make([]SharedSegment, 0, len(order))
	for _, k := range order {
		out = append(out, *byKey[k])
	}
	sort.SliceStable(out, func(i, j int) bool { return out[i].Size > out[j].Size })
	return out
}

var (
	discoMu    sync.Mutex
	discoCache []SharedSegment
	discoAt    time.Time
)

func discoverSegments() []SharedSegment {
	discoMu.Lock()
	defer discoMu.Unlock()
	if discoCache != nil && time.Since(discoAt) < 15*time.Second {
		return discoCache
	}
	segs := procSegments()
	if len(segs) == 0 {
		segs = ipcsSegments()
	}
	discoCache = mergeSegments(segs, knownSegments())
	discoAt = time.Now()
	return discoCache
}

func sysvRead(shmid int, size int64) ([]byte, error) {
	if size <= 0 || size > maxReadSize {
		return nil, fmt.Errorf("invalid segment size %d", size)
	}
	addr, _, errno := syscall.Syscall(syscall.SYS_SHMAT, uintptr(shmid), 0, shmFlagReadOnly)
	if errno != 0 {
		return nil, fmt.Errorf("shmat(%d): %v", shmid, errno)
	}
	defer syscall.Syscall(syscall.SYS_SHMDT, addr, 0, 0)
	buf := make([]byte, int(size))
	copy(buf, unsafe.Slice((*byte)(unsafe.Pointer(addr)), int(size)))
	return buf, nil
}

func readSegment(seg SharedSegment) ([]byte, string, error) {
	if !strings.HasPrefix(seg.Name, "0x") {
		candidates := []string{
			"/dev/shm/" + seg.Name,
			"/dev/shm/" + strings.ToLower(seg.Name),
		}
		for _, p := range candidates {
			if st, err := os.Stat(p); err == nil && st.Mode().IsRegular() {
				data, err := os.ReadFile(p)
				if err == nil {
					if seg.Size > 0 && int64(len(data)) > seg.Size {
						data = data[:seg.Size]
					}
					return data, "file:" + p, nil
				}
			}
		}
	}
	shmid := seg.Shmid
	if shmid <= 0 {
		id, _, errno := syscall.Syscall(syscall.SYS_SHMGET, uintptr(seg.Key), 0, 0)
		if errno != 0 {
			return nil, "", fmt.Errorf("shmget(0x%08X): %v", seg.Key, errno)
		}
		shmid = int(id)
	}
	if seg.Size <= 0 {
		return nil, "", fmt.Errorf("segment %s has unknown size", seg.Name)
	}
	data, err := sysvRead(shmid, seg.Size)
	if err != nil {
		return nil, "", err
	}
	return data, fmt.Sprintf("sysv:shmid=%d", shmid), nil
}

func pickSpectrumSegment() (SharedSegment, bool) {
	segs := discoverSegments()
	for _, s := range segs {
		if !strings.HasPrefix(s.Name, "NTP") {
			return s, true
		}
	}
	if len(segs) > 0 {
		return segs[0], true
	}
	return SharedSegment{}, false
}

func byteOrder(little bool) binary.ByteOrder {
	if little {
		return binary.LittleEndian
	}
	return binary.BigEndian
}

func readFloat(order binary.ByteOrder, b []byte, width int) float64 {
	switch width {
	case 4:
		return float64(math.Float32frombits(order.Uint32(b)))
	default:
		return math.Float64frombits(order.Uint64(b))
	}
}

func decodeFloatRuns(data []byte, width int, little bool) []SweepPoint {
	order := byteOrder(little)
	var best []SweepPoint
	cur := make([]SweepPoint, 0, 4096)
	prev := math.NaN()
	flush := func() {
		if len(cur) > len(best) {
			best = append([]SweepPoint(nil), cur...)
		}
		cur = cur[:0]
	}
	for off := 0; off+width*2 <= len(data); off += width * 2 {
		f := readFloat(order, data[off:off+width], width)
		p := readFloat(order, data[off+width:off+2*width], width)
		valid := !math.IsNaN(f) && !math.IsInf(f, 0) && !math.IsNaN(p) && !math.IsInf(p, 0) &&
			f >= minFreqHz && f <= maxFreqHz &&
			p >= minPowerDbm && p <= maxPowerDbm &&
			(len(cur) == 0 || f > prev)
		if !valid {
			flush()
			prev = math.NaN()
			continue
		}
		cur = append(cur, SweepPoint{FrequencyHz: f, PowerDbm: p})
		prev = f
	}
	flush()
	return best
}

func extractSpectrum(data []byte) ([]SweepPoint, string) {
	bestPts, bestFmt := []SweepPoint{}, ""
	for _, width := range []int{4, 8} {
		for _, little := range []bool{true, false} {
			pts := decodeFloatRuns(data, width, little)
			if len(pts) > len(bestPts) {
				endian := "be"
				if little {
					endian = "le"
				}
				bestPts, bestFmt = pts, fmt.Sprintf("float%d-%s", width*8, endian)
			}
		}
	}
	if len(bestPts) < minSweepPoints {
		return nil, ""
	}
	return bestPts, bestFmt
}

func gpsHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, GPSData{
		Latitude:   52.5200,
		Longitude:  13.4050,
		Altitude:   34.0,
		Satellites: 9,
		Fix:        true,
		Timestamp:  time.Now().UTC(),
	})
}

func ntpHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, NTPData{
		Server:   "pool.ntp.org",
		OffsetMs: 1.23,
		DelayMs:  12.5,
		Stratum:  2,
		Synced:   true,
		LastSync: time.Now().UTC(),
	})
}

func systemHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, SystemData{
		Hostname:   "csms-bridge",
		UptimeSec:  86400,
		CPULoadPct: 12.5,
		MemTotalMB: 512,
		MemFreeMB:  256,
		Version:    version,
		Timestamp:  time.Now().UTC(),
	})
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"status":    "ok",
		"version":   version,
		"timestamp": time.Now().UTC(),
	})
}

func segmentsHandler(w http.ResponseWriter, r *http.Request) {
	type entry struct {
		SharedSegment
		Readable bool   `json:"readable"`
		Source   string `json:"source,omitempty"`
		Error    string `json:"error,omitempty"`
	}
	segs := discoverSegments()
	out := make([]entry, 0, len(segs))
	for _, s := range segs {
		e := entry{SharedSegment: s}
		if _, src, err := readSegment(s); err == nil {
			e.Readable = true
			e.Source = src
		} else {
			e.Error = err.Error()
		}
		out = append(out, e)
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"segments":  out,
		"timestamp": time.Now().UTC(),
	})
}

func spectrumHandler(w http.ResponseWriter, r *http.Request) {
	seg, ok := pickSpectrumSegment()
	if !ok {
		writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{"error": "no shared memory segments found"})
		return
	}
	data, source, err := readSegment(seg)
	if err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{"error": err.Error()})
		return
	}
	points, format := extractSpectrum(data)
	resp := map[string]interface{}{
		"segment":     seg.Name,
		"key":         fmt.Sprintf("0x%08X", seg.Key),
		"source":      source,
		"size_bytes":  len(data),
		"format":      format,
		"point_count": len(points),
		"timestamp":   time.Now().UTC(),
	}
	if len(points) > 0 {
		resp["start_frequency_hz"] = points[0].FrequencyHz
		resp["end_frequency_hz"] = points[len(points)-1].FrequencyHz
	}
	resp["points"] = points
	writeJSON(w, http.StatusOK, resp)
}

func spectrumRawHandler(w http.ResponseWriter, r *http.Request) {
	segs := discoverSegments()
	var seg SharedSegment
	if want := strings.TrimSpace(r.URL.Query().Get("segment")); want != "" {
		found := false
		for _, s := range segs {
			if strings.EqualFold(s.Name, want) || strings.EqualFold(fmt.Sprintf("0x%08X", s.Key), want) {
				seg, found = s, true
				break
			}
		}
		if !found {
			writeJSON(w, http.StatusNotFound, map[string]interface{}{"error": "segment not found: " + want})
			return
		}
	} else {
		var ok bool
		seg, ok = pickSpectrumSegment()
		if !ok {
			writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{"error": "no shared memory segments found"})
			return
		}
	}
	data, source, err := readSegment(seg)
	if err != nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{"error": err.Error()})
		return
	}
	if maxBytes, err := strconv.Atoi(r.URL.Query().Get("max")); err == nil && maxBytes > 0 && maxBytes < len(data) {
		data = data[:maxBytes]
	}
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("X-Csms-Segment", seg.Name)
	w.Header().Set("X-Csms-Key", fmt.Sprintf("0x%08X", seg.Key))
	w.Header().Set("X-Csms-Source", source)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(data)
}

type UDPPacket struct {
	Seq       int64     `json:"seq"`
	Source    string    `json:"source"`
	Dest      string    `json:"dest,omitempty"`
	Protocol  string    `json:"protocol,omitempty"`
	Length    int       `json:"length_bytes"`
	Timestamp time.Time `json:"timestamp"`

	data []byte
}

type packetRing struct {
	mu    sync.Mutex
	buf   []*UDPPacket
	head  int
	count int
	seq   int64
}

var udpRing = newPacketRing(udpRingSize)

func newPacketRing(size int) *packetRing {
	return &packetRing{buf: make([]*UDPPacket, size)}
}

func (r *packetRing) push(p *UDPPacket) {
	r.mu.Lock()
	r.seq++
	p.Seq = r.seq
	r.buf[r.head] = p
	r.head = (r.head + 1) % len(r.buf)
	if r.count < len(r.buf) {
		r.count++
	}
	r.mu.Unlock()
}

func (r *packetRing) snapshot() []*UDPPacket {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]*UDPPacket, 0, r.count)
	for i := 0; i < r.count; i++ {
		idx := (r.head - r.count + i + len(r.buf)) % len(r.buf)
		out = append(out, r.buf[idx])
	}
	return out
}

func (r *packetRing) stats() (captured int64, buffered int) {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.seq, r.count
}

func decodeSplitArrays(data []byte) ([]SweepPoint, string) {
	n := len(data) / 8
	if n < minSweepPoints {
		return nil, ""
	}
	order := binary.LittleEndian
	base := n * 4
	pts := make([]SweepPoint, 0, n)
	prev := math.NaN()
	for i := 0; i < n; i++ {
		f := float64(math.Float32frombits(order.Uint32(data[i*4 : i*4+4])))
		p := float64(math.Float32frombits(order.Uint32(data[base+i*4 : base+i*4+4])))
		if math.IsNaN(f) || math.IsInf(f, 0) || math.IsNaN(p) || math.IsInf(p, 0) ||
			f < minFreqHz || f > maxFreqHz || p < minPowerDbm || p > maxPowerDbm ||
			(i > 0 && f <= prev) {
			return nil, ""
		}
		pts = append(pts, SweepPoint{FrequencyHz: f, PowerDbm: p})
		prev = f
	}
	return pts, "split-f32le"
}

func decodeUDPPacket(data []byte) ([]SweepPoint, string) {
	if pts, format := extractSpectrum(data); len(pts) >= minSweepPoints {
		return pts, format
	}
	if pts, format := decodeSplitArrays(data); len(pts) >= minSweepPoints {
		return pts, format
	}
	return nil, ""
}

func bytesPerPoint(format string) int {
	switch format {
	case "float64-le", "float64-be":
		return 16
	default:
		return 8
	}
}

// decodeConfidence returns 0..1, the fraction of the payload explained by a
// successful decode. Values near 1 mean the format is well understood; values
// near 0 signal an unknown (native CSMS) framing that still needs a decoder.
func decodeConfidence(format string, points, length int) float64 {
	if length <= 0 || points <= 0 {
		return 0
	}
	c := float64(points*bytesPerPoint(format)) / float64(length)
	if c > 1 {
		return 1
	}
	return c
}

const rateWindow = 10 * time.Second

type captureTracker struct {
	mu         sync.Mutex
	total      int64
	times      []time.Time
	lastSrc    string
	lastDst    string
	lastProto  string
	lastLen    int
	lastFormat string
	lastPoints int
	lastConf   float64
}

var captureStats = &captureTracker{}

func (t *captureTracker) record(p *UDPPacket) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.total++
	t.times = append(t.times, time.Now())
	if len(t.times) > 4096 {
		t.times = t.times[len(t.times)-4096:]
	}
	t.lastSrc = p.Source
	t.lastDst = p.Dest
	t.lastProto = p.Protocol
	t.lastLen = p.Length
	if pts, format := decodeUDPPacket(p.data); len(pts) > 0 {
		t.lastFormat = format
		t.lastPoints = len(pts)
		t.lastConf = decodeConfidence(format, len(pts), p.Length)
	} else {
		t.lastFormat = ""
		t.lastPoints = 0
		t.lastConf = 0
	}
}

func (t *captureTracker) snapshot() map[string]interface{} {
	t.mu.Lock()
	defer t.mu.Unlock()
	cutoff := time.Now().Add(-rateWindow)
	i := 0
	for i < len(t.times) && t.times[i].Before(cutoff) {
		i++
	}
	if i > 0 {
		t.times = t.times[i:]
	}
	rate := float64(len(t.times)) / rateWindow.Seconds()
	return map[string]interface{}{
		"captured_total":    t.total,
		"rate_per_sec":      rate,
		"rate_window_sec":   rateWindow.Seconds(),
		"last_source":       t.lastSrc,
		"last_dest":         t.lastDst,
		"last_protocol":     t.lastProto,
		"last_length_bytes": t.lastLen,
		"last_decode": map[string]interface{}{
			"format":      t.lastFormat,
			"point_count": t.lastPoints,
			"confidence":  t.lastConf,
		},
		"streams_tracked": reasm.streamCount(),
		"timestamp":       time.Now().UTC(),
	}
}

func spectrumStatusHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, captureStats.snapshot())
}

func parseLimit(r *http.Request, def, max int) int {
	v, err := strconv.Atoi(r.URL.Query().Get("limit"))
	if err != nil || v <= 0 {
		return def
	}
	if v > max {
		return max
	}
	return v
}

type livePacket struct {
	Seq        int64        `json:"seq"`
	Source     string       `json:"source"`
	Dest       string       `json:"dest,omitempty"`
	Protocol   string       `json:"protocol,omitempty"`
	Length     int          `json:"length_bytes"`
	Timestamp  time.Time    `json:"timestamp"`
	Format     string       `json:"format,omitempty"`
	PointCount int          `json:"point_count"`
	StartHz    float64      `json:"start_frequency_hz,omitempty"`
	EndHz      float64      `json:"end_frequency_hz,omitempty"`
	Points     []SweepPoint `json:"points,omitempty"`
}

func spectrumLiveHandler(w http.ResponseWriter, r *http.Request) {
	limit := parseLimit(r, 20, udpRingSize)
	pkts := udpRing.snapshot()
	if len(pkts) > limit {
		pkts = pkts[len(pkts)-limit:]
	}
	out := make([]livePacket, 0, len(pkts))
	for _, p := range pkts {
		lp := livePacket{
			Seq:       p.Seq,
			Source:    p.Source,
			Dest:      p.Dest,
			Protocol:  p.Protocol,
			Length:    p.Length,
			Timestamp: p.Timestamp,
		}
		if pts, format := decodeUDPPacket(p.data); len(pts) > 0 {
			lp.Format = format
			lp.PointCount = len(pts)
			lp.StartHz = pts[0].FrequencyHz
			lp.EndHz = pts[len(pts)-1].FrequencyHz
			lp.Points = pts
		}
		out = append(out, lp)
	}
	captured, buffered := udpRing.stats()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"captured_total": captured,
		"buffered":       buffered,
		"returned":       len(out),
		"packets":        out,
		"timestamp":      time.Now().UTC(),
	})
}

func spectrumRawUDPHandler(w http.ResponseWriter, r *http.Request) {
	limit := parseLimit(r, 10, udpRingSize)
	format := strings.ToLower(r.URL.Query().Get("format"))
	pkts := udpRing.snapshot()
	if len(pkts) > limit {
		pkts = pkts[len(pkts)-limit:]
	}
	switch format {
	case "text":
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		w.WriteHeader(http.StatusOK)
		for _, p := range pkts {
			fmt.Fprintf(w, "%d %s %d %s\n%s\n",
				p.Seq, p.Timestamp.UTC().Format(time.RFC3339Nano), p.Length,
				p.Source, hex.EncodeToString(p.data))
		}
	case "binary":
		if len(pkts) == 0 {
			writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{"error": "no udp packets captured yet"})
			return
		}
		last := pkts[len(pkts)-1]
		w.Header().Set("Content-Type", "application/octet-stream")
		w.Header().Set("X-Csms-Udp-Seq", strconv.FormatInt(last.Seq, 10))
		w.Header().Set("X-Csms-Udp-Source", last.Source)
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(last.data)
	default:
		type rawPacket struct {
			Seq       int64     `json:"seq"`
			Source    string    `json:"source"`
			Dest      string    `json:"dest,omitempty"`
			Protocol  string    `json:"protocol,omitempty"`
			Length    int       `json:"length_bytes"`
			Timestamp time.Time `json:"timestamp"`
			Hex       string    `json:"hex"`
		}
		out := make([]rawPacket, 0, len(pkts))
		for _, p := range pkts {
			out = append(out, rawPacket{
				Seq: p.Seq, Source: p.Source, Dest: p.Dest, Protocol: p.Protocol, Length: p.Length,
				Timestamp: p.Timestamp, Hex: hex.EncodeToString(p.data),
			})
		}
		captured, buffered := udpRing.stats()
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"captured_total": captured,
			"buffered":       buffered,
			"returned":       len(out),
			"packets":        out,
			"timestamp":      time.Now().UTC(),
		})
	}
}

func main() {
	for _, s := range discoverSegments() {
		log.Printf("shared memory segment: %s key=0x%08X shmid=%d size=%d", s.Name, s.Key, s.Shmid, s.Size)
	}

	startPacketTap()

	mux := http.NewServeMux()
	mux.HandleFunc("/gps", gpsHandler)
	mux.HandleFunc("/ntp", ntpHandler)
	mux.HandleFunc("/system", systemHandler)
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/segments", segmentsHandler)
	mux.HandleFunc("/spectrum", spectrumHandler)
	mux.HandleFunc("/spectrum/raw", spectrumRawHandler)
	mux.HandleFunc("/spectrum/live", spectrumLiveHandler)
	mux.HandleFunc("/spectrum/raw/udp", spectrumRawUDPHandler)
	mux.HandleFunc("/spectrum/raw/live", spectrumRawUDPHandler)
	mux.HandleFunc("/spectrum/status", spectrumStatusHandler)

	addr := ":8080"
	log.Printf("csms-bridge %s listening on %s", version, addr)
	if err := http.ListenAndServe(addr, corsMiddleware(mux)); err != nil {
		log.Fatal(err)
	}
}
