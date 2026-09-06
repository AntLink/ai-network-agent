import socket
import sys
import time

IAC = 255
DO = 253
WILL = 251
DONT = 254
WONT = 252


def negotiate(sock, data):
    clean = bytearray()
    index = 0
    while index < len(data):
        if data[index] != IAC or index + 2 >= len(data):
            clean.append(data[index])
            index += 1
            continue
        verb, option = data[index + 1], data[index + 2]
        if verb == WILL:
            sock.sendall(bytes([IAC, DO, option]))
        elif verb == DO:
            sock.sendall(bytes([IAC, WONT, option]))
        index += 3
    return bytes(clean)

host = sys.argv[1]
port = int(sys.argv[2])
commands = [b"\r\n", b"echo READY\r\n"]
sock = socket.create_connection((host, port), timeout=5)
sock.settimeout(1)
sock.sendall(bytes([IAC, WILL, 1, IAC, WILL, 3, IAC, WILL, 0]))
chunks = []
for command in commands:
    sock.sendall(command)
    time.sleep(1)
    while True:
        try:
            data = sock.recv(8192)
        except socket.timeout:
            break
        if not data:
            break
            print("RECV", repr(data), file=sys.stderr)
            clean = negotiate(sock, data)
            if clean:
                chunks.append(clean)
sock.close()
sys.stdout.buffer.write(b"".join(chunks)[-12000:])
