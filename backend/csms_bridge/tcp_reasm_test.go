package main

import (
	"bytes"
	"encoding/binary"
	"testing"
)

func makeCrt(body []byte) []byte {
	hdr := make([]byte, 12)
	binary.LittleEndian.PutUint32(hdr[8:12], uint32(len(body)))
	return append(hdr, body...)
}

func makeSsms(body []byte) []byte {
	hdr := make([]byte, 20)
	binary.LittleEndian.PutUint32(hdr[16:20], uint32(len(body)))
	out := append(hdr, body...)
	return append(out, 0x0a)
}

func TestCrtCompleteFrame(t *testing.T) {
	r := newTCPReassembler()
	frame := makeCrt(make([]byte, 64))
	frames := r.feed(3307, "s->d", frame)
	if len(frames) != 1 {
		t.Fatalf("want 1 frame, got %d", len(frames))
	}
	if !bytes.Equal(frames[0], frame) {
		t.Fatalf("frame mismatch")
	}
}

func TestCrtSplitFrame(t *testing.T) {
	r := newTCPReassembler()
	frame := makeCrt(make([]byte, 64))
	if frames := r.feed(3307, "s->d", frame[:32]); len(frames) != 0 {
		t.Fatalf("want 0 frames before complete, got %d", len(frames))
	}
	frames := r.feed(3307, "s->d", frame[32:])
	if len(frames) != 1 {
		t.Fatalf("want 1 frame, got %d", len(frames))
	}
	if !bytes.Equal(frames[0], frame) {
		t.Fatalf("frame mismatch")
	}
}

func TestCrtMultipleFrames(t *testing.T) {
	r := newTCPReassembler()
	b1 := makeCrt(make([]byte, 32))
	b2 := makeCrt(make([]byte, 16))
	joined := append(append([]byte{}, b1...), b2...)
	frames := r.feed(3307, "s->d", joined)
	if len(frames) != 2 {
		t.Fatalf("want 2 frames, got %d", len(frames))
	}
	if !bytes.Equal(frames[0], b1) || !bytes.Equal(frames[1], b2) {
		t.Fatalf("frame mismatch")
	}
}

func TestSsmsFrameWithDelimiter(t *testing.T) {
	r := newTCPReassembler()
	f1 := makeSsms(make([]byte, 20))
	f2 := makeSsms(make([]byte, 30))
	joined := append(append([]byte{}, f1...), f2...)
	frames := r.feed(3302, "s->d", joined)
	if len(frames) != 2 {
		t.Fatalf("want 2 frames, got %d", len(frames))
	}
	if !bytes.Equal(frames[0], f1[:len(f1)-1]) || !bytes.Equal(frames[1], f2[:len(f2)-1]) {
		t.Fatalf("frame mismatch (newline not stripped)")
	}
}

func TestSsmsSplitAcrossSegments(t *testing.T) {
	r := newTCPReassembler()
	f := makeSsms(make([]byte, 40))
	if frames := r.feed(3303, "s->d", f[:25]); len(frames) != 0 {
		t.Fatalf("want 0 frames, got %d", len(frames))
	}
	frames := r.feed(3303, "s->d", f[25:])
	if len(frames) != 1 {
		t.Fatalf("want 1 frame, got %d", len(frames))
	}
	if !bytes.Equal(frames[0], f[:len(f)-1]) {
		t.Fatalf("frame mismatch")
	}
}

func TestFrameInfoOversizedBodySkips(t *testing.T) {
	buf := make([]byte, 12)
	binary.LittleEndian.PutUint32(buf[8:12], uint32(maxFrameBody)+1)
	fl, sk := frameInfo(3307, buf)
	if fl != 0 || sk != 1 {
		t.Fatalf("want skip=1, got frameLen=%d skip=%d", fl, sk)
	}
}

func TestFrameInfoIncomplete(t *testing.T) {
	buf := make([]byte, 12)
	binary.LittleEndian.PutUint32(buf[8:12], 100)
	fl, sk := frameInfo(3307, buf)
	if fl != 0 || sk != 0 {
		t.Fatalf("want need-more-data (0,0), got frameLen=%d skip=%d", fl, sk)
	}
}
