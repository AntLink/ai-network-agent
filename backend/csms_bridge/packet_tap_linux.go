//go:build linux

package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"syscall"
	"time"
)

const (
	ethPAll  = 0x0003
	ethPIP   = 0x0800
	ethPIPv6 = 0x86dd

	ipProtoTCP = 6
	ipProtoUDP = 17
)

var tapPorts = map[uint16]bool{
	18331: true,
	5060:  true,
	3302:  true,
	3303:  true,
	3307:  true,
}

func htons(v uint16) uint16 {
	return (v<<8)&0xff00 | v>>8
}

func tapPortOf(srcPort, dstPort uint16) (uint16, bool) {
	if tapPorts[srcPort] {
		return srcPort, true
	}
	if tapPorts[dstPort] {
		return dstPort, true
	}
	return 0, false
}

func startPacketTap() {
	go func() {
		fd, err := syscall.Socket(syscall.AF_PACKET, syscall.SOCK_RAW, int(htons(ethPAll)))
		if err != nil {
			log.Printf("packet tap disabled: %v", err)
			return
		}
		defer syscall.Close(fd)

		if err := syscall.Bind(fd, &syscall.SockaddrLinklayer{Protocol: htons(ethPAll)}); err != nil {
			log.Printf("packet tap bind failed: %v", err)
			return
		}

		log.Printf("packet tap enabled for ports 18331, 5060, 3302, 3303, 3307")
		buf := make([]byte, maxUDPPacketSize)
		for {
			n, _, err := syscall.Recvfrom(fd, buf, 0)
			if err != nil {
				if err == syscall.EINTR {
					continue
				}
				log.Printf("packet tap read error: %v", err)
				return
			}
			if n <= 0 {
				continue
			}
			for _, pkt := range extractFrames(buf[:n]) {
				udpRing.push(pkt)
				captureStats.record(pkt)
			}
		}
	}()
}

// extractFrames parses an Ethernet frame and returns zero or more captured
// packets. UDP datagrams are emitted directly; TCP payloads are reassembled
// into complete application frames.
func extractFrames(frame []byte) []*UDPPacket {
	if len(frame) < 14 {
		return nil
	}
	etherType := binary.BigEndian.Uint16(frame[12:14])
	switch etherType {
	case ethPIP:
		return extractIPv4(frame[14:])
	case ethPIPv6:
		return extractIPv6(frame[14:])
	default:
		return nil
	}
}

func extractIPv4(pkt []byte) []*UDPPacket {
	if len(pkt) < 20 {
		return nil
	}
	ihl := int(pkt[0]&0x0f) * 4
	if ihl < 20 || len(pkt) < ihl {
		return nil
	}
	total := int(binary.BigEndian.Uint16(pkt[2:4]))
	if total <= 0 || total > len(pkt) {
		total = len(pkt)
	}
	proto := pkt[9]
	src := net.IP(pkt[12:16]).String()
	dst := net.IP(pkt[16:20]).String()
	return extractLayer4(proto, src, dst, pkt[ihl:total])
}

func extractIPv6(pkt []byte) []*UDPPacket {
	if len(pkt) < 40 {
		return nil
	}
	payloadLen := int(binary.BigEndian.Uint16(pkt[4:6]))
	total := 40 + payloadLen
	if payloadLen <= 0 || total > len(pkt) {
		total = len(pkt)
	}
	proto := pkt[6]
	src := net.IP(pkt[8:24]).String()
	dst := net.IP(pkt[24:40]).String()
	return extractLayer4(proto, src, dst, pkt[40:total])
}

func extractLayer4(proto byte, srcIP, dstIP string, segment []byte) []*UDPPacket {
	switch proto {
	case ipProtoUDP:
		if len(segment) < 8 {
			return nil
		}
		srcPort := binary.BigEndian.Uint16(segment[0:2])
		dstPort := binary.BigEndian.Uint16(segment[2:4])
		if _, ok := tapPortOf(srcPort, dstPort); !ok {
			return nil
		}
		udpLen := int(binary.BigEndian.Uint16(segment[4:6]))
		if udpLen <= 8 || udpLen > len(segment) {
			udpLen = len(segment)
		}
		return []*UDPPacket{packetFromPayload("udp-tap", srcIP, srcPort, dstIP, dstPort, segment[8:udpLen])}
	case ipProtoTCP:
		if len(segment) < 20 {
			return nil
		}
		srcPort := binary.BigEndian.Uint16(segment[0:2])
		dstPort := binary.BigEndian.Uint16(segment[2:4])
		port, ok := tapPortOf(srcPort, dstPort)
		if !ok {
			return nil
		}
		dataOff := int(segment[12]>>4) * 4
		if dataOff < 20 || dataOff >= len(segment) {
			return nil
		}
		payload := segment[dataOff:]
		if len(payload) == 0 {
			return nil
		}
		key := fmt.Sprintf("%s:%d->%s:%d", srcIP, srcPort, dstIP, dstPort)
		frames := reasm.feed(port, key, payload)
		out := make([]*UDPPacket, 0, len(frames))
		protoName := fmt.Sprintf("tcp:%d", port)
		for _, f := range frames {
			out = append(out, packetFromPayload(protoName, srcIP, srcPort, dstIP, dstPort, f))
		}
		return out
	default:
		return nil
	}
}

func packetFromPayload(proto, srcIP string, srcPort uint16, dstIP string, dstPort uint16, payload []byte) *UDPPacket {
	return &UDPPacket{
		Source:    fmt.Sprintf("%s:%d", srcIP, srcPort),
		Dest:      fmt.Sprintf("%s:%d", dstIP, dstPort),
		Protocol:  proto,
		Length:    len(payload),
		Timestamp: time.Now().UTC(),
		data:      append([]byte(nil), payload...),
	}
}
