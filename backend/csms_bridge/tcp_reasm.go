package main

import (
	"encoding/binary"
	"sync"
)

const (
	crtHeaderLen   = 12
	crtBodyLenOff  = 8
	ssmsHeaderLen  = 20
	ssmsBodyLenOff = 0x10

	maxFrameBody  = 8 << 20
	maxStreamSize = 16 << 20
	maxStreams    = 1024
)

// tcpReassembler accumulates per-direction TCP payloads and emits complete
// application frames using the known length-prefixed framing of the CSMS
// protocols:
//
//	TCP 3307 (CRealtimeNet): [12B header][bodyLen B], bodyLen is u32 LE at +8.
//	TCP 3302/3303 (SSmsMsg):  [20B header][bodyLen B][0x0a], bodyLen u32 LE at +0x10.
//
// It is self-synchronizing: invalid header bytes at the head of a stream are
// skipped one byte at a time until a plausible frame is found. Stream memory
// is bounded by maxStreamSize and maxStreams.
type tcpReassembler struct {
	mu      sync.Mutex
	streams map[string][]byte
}

func newTCPReassembler() *tcpReassembler {
	return &tcpReassembler{streams: make(map[string][]byte)}
}

var reasm = newTCPReassembler()

func (r *tcpReassembler) streamCount() int {
	r.mu.Lock()
	defer r.mu.Unlock()
	return len(r.streams)
}

// frameInfo returns the length of the next complete frame for the given port,
// or a positive skip length if the head of the buffer is not a valid header.
// Both zero means more data is needed.
func frameInfo(port uint16, buf []byte) (frameLen, skipLen int) {
	var hdrLen, bodyOff int
	switch port {
	case 3307:
		hdrLen, bodyOff = crtHeaderLen, crtBodyLenOff
	case 3302, 3303:
		hdrLen, bodyOff = ssmsHeaderLen, ssmsBodyLenOff
	default:
		return 0, 0
	}
	if len(buf) < hdrLen {
		return 0, 0
	}
	bodyLen := binary.LittleEndian.Uint32(buf[bodyOff : bodyOff+4])
	if bodyLen > maxFrameBody {
		return 0, 1
	}
	total := hdrLen + int(bodyLen)
	if len(buf) < total {
		return 0, 0
	}
	return total, 0
}

// feed appends a TCP segment payload for one connection direction and returns
// any complete frames extracted from that stream.
func (r *tcpReassembler) feed(port uint16, key string, payload []byte) [][]byte {
	if len(payload) == 0 {
		return nil
	}
	r.mu.Lock()
	defer r.mu.Unlock()

	buf := r.streams[key]
	if len(buf)+len(payload) > maxStreamSize {
		buf = nil
	}
	buf = append(buf, payload...)

	var frames [][]byte
	for {
		fl, sk := frameInfo(port, buf)
		if sk > 0 {
			if sk >= len(buf) {
				buf = nil
				break
			}
			buf = buf[sk:]
			continue
		}
		if fl == 0 {
			break
		}
		frame := make([]byte, fl)
		copy(frame, buf[:fl])
		frames = append(frames, frame)
		consumed := fl
		if port == 3302 || port == 3303 {
			if consumed < len(buf) && buf[consumed] == 0x0a {
				consumed++
			}
		}
		buf = buf[consumed:]
	}

	if len(buf) == 0 {
		delete(r.streams, key)
	} else {
		r.streams[key] = buf
		if len(r.streams) > maxStreams {
			for k := range r.streams {
				delete(r.streams, k)
				break
			}
		}
	}
	return frames
}
