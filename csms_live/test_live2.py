import struct
import sys
import time
import math
from pathlib import Path

# ============================================================
# PATH PROJECT
# ============================================================

sys.path.insert(
    0,
    r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend"
)

from csms_client import CSMSClient, HDR


# ============================================================
# CONFIG
# ============================================================

HOST = "192.168.162.20"
PORT = 3302
TIMEOUT = 30

START_FREQ = 100e6
STOP_FREQ = 200e6
STEP_FREQ = 1e6
RBW = 100e3
DWELL_MS = 100
SWEEP_TYPE = 1

MEASURE_ID_START = 5590
MEASURE_ID_END = 5620

OUTPUT_DIR = Path("csms_dumps")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def hexdump(data, width=16, max_bytes=256):
    """
    Print hex dump sederhana.
    """

    data = data[:max_bytes]

    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]

        hex_part = " ".join(
            f"{b:02X}" for b in chunk
        )

        ascii_part = "".join(
            chr(b) if 32 <= b <= 126 else "."
            for b in chunk
        )

        print(
            f"{offset:04X}  "
            f"{hex_part:<{width * 3}} "
            f"{ascii_part}"
        )


def dump_uint32(data, max_bytes=128):
    """
    Interpret awal body sebagai little-endian uint32.
    """

    print("\n=== UINT32 ===")

    end = min(len(data), max_bytes)

    for off in range(0, end - 3, 4):
        value = struct.unpack_from(
            "<I",
            data,
            off
        )[0]

        print(
            f"0x{off:04X} "
            f"{off:4d}: "
            f"{value:12d} "
            f"0x{value:08X}"
        )


def dump_int32(data, max_bytes=128):
    """
    Interpret awal body sebagai signed int32.
    """

    print("\n=== INT32 ===")

    end = min(len(data), max_bytes)

    for off in range(0, end - 3, 4):
        value = struct.unpack_from(
            "<i",
            data,
            off
        )[0]

        print(
            f"0x{off:04X} "
            f"{off:4d}: "
            f"{value}"
        )


def dump_float32(data, max_bytes=128):
    """
    Interpret awal body sebagai float32.
    """

    print("\n=== FLOAT32 ===")

    end = min(len(data), max_bytes)

    for off in range(0, end - 3, 4):

        value = struct.unpack_from(
            "<f",
            data,
            off
        )[0]

        if math.isfinite(value):

            print(
                f"0x{off:04X} "
                f"{off:4d}: "
                f"{value:.10g}"
            )


def dump_float64(data, max_bytes=128):
    """
    Interpret awal body sebagai float64.
    """

    print("\n=== FLOAT64 ===")

    end = min(len(data), max_bytes)

    for off in range(0, end - 7, 8):

        value = struct.unpack_from(
            "<d",
            data,
            off
        )[0]

        if math.isfinite(value):

            print(
                f"0x{off:04X} "
                f"{off:4d}: "
                f"{value:.12g}"
            )


def search_known_values(data):
    """
    Cari nilai yang kita kenal dari request schedule
    di dalam response.
    """

    known_values = {
        "START_FREQ": START_FREQ,
        "STOP_FREQ": STOP_FREQ,
        "STEP_FREQ": STEP_FREQ,
        "RBW": RBW,
    }

    print("\n=== SEARCH KNOWN FLOAT VALUES ===")

    for name, expected in known_values.items():

        print(
            f"\n{name} = {expected}"
        )

        # float64
        pattern64 = struct.pack(
            "<d",
            expected
        )

        pos = data.find(pattern64)

        if pos >= 0:
            print(
                f"  float64 found at offset "
                f"{pos} / 0x{pos:X}"
            )
        else:
            print(
                "  float64 not found"
            )

        # float32
        pattern32 = struct.pack(
            "<f",
            expected
        )

        pos = data.find(pattern32)

        if pos >= 0:
            print(
                f"  float32 found at offset "
                f"{pos} / 0x{pos:X}"
            )
        else:
            print(
                "  float32 not found"
            )


def find_float32_power_regions(data):
    """
    Cari daerah yang terlihat seperti array power/dBm float32.

    Range dibuat cukup luas:
    -250 sampai +100 dB/dBm.
    """

    print("\n=== SEARCH FLOAT32 POWER ARRAYS ===")

    candidates = []

    # Scan alignment 4-byte
    for start in range(0, len(data) - 400, 4):

        values = []

        pos = start

        while pos + 4 <= len(data):

            value = struct.unpack_from(
                "<f",
                data,
                pos
            )[0]

            if not math.isfinite(value):
                break

            if not (-250 <= value <= 100):
                break

            values.append(value)

            pos += 4

            if len(values) >= 4096:
                break

        if len(values) >= 50:

            candidates.append(
                (
                    start,
                    len(values),
                    min(values),
                    max(values),
                    values[:10]
                )
            )

    # Hilangkan kandidat overlapping
    filtered = []

    last_end = -1

    for item in candidates:

        start, count, _, _, _ = item

        end = start + count * 4

        if start >= last_end:

            filtered.append(item)

            last_end = end

    if not filtered:
        print(
            "No obvious float32 power array found."
        )
        return

    for (
        start,
        count,
        min_val,
        max_val,
        first_values
    ) in filtered[:10]:

        print(
            f"\nCandidate:"
        )

        print(
            f"  offset : {start} / 0x{start:X}"
        )

        print(
            f"  count  : {count}"
        )

        print(
            f"  range  : "
            f"{min_val:.2f} .. {max_val:.2f}"
        )

        print(
            "  first 10:",
            [
                round(v, 2)
                for v in first_values
            ]
        )


def find_int16_power_regions(data):
    """
    Cari kemungkinan array level berupa int16.

    Banyak perangkat RF menyimpan level dalam:
        dBm * 10
        atau
        dBm * 100
    """

    print("\n=== SEARCH INT16 POWER ARRAYS ===")

    candidates = []

    for start in range(0, len(data) - 200, 2):

        values = []

        pos = start

        while pos + 2 <= len(data):

            value = struct.unpack_from(
                "<h",
                data,
                pos
            )[0]

            # range lebar untuk kemungkinan scaling
            if not (-30000 <= value <= 10000):
                break

            values.append(value)

            pos += 2

            if len(values) >= 10000:
                break

        if len(values) >= 100:

            candidates.append(
                (
                    start,
                    len(values),
                    min(values),
                    max(values),
                    values[:10]
                )
            )

    if not candidates:
        print(
            "No obvious int16 region found."
        )
        return

    # hanya tampilkan beberapa kandidat terbesar
    candidates.sort(
        key=lambda x: x[1],
        reverse=True
    )

    for item in candidates[:10]:

        (
            start,
            count,
            min_val,
            max_val,
            first_values
        ) = item

        print(
            f"\nCandidate:"
        )

        print(
            f"  offset : "
            f"{start} / 0x{start:X}"
        )

        print(
            f"  count  : {count}"
        )

        print(
            f"  range  : "
            f"{min_val} .. {max_val}"
        )

        print(
            f"  first 10: "
            f"{first_values}"
        )


def search_frequency_double_pairs(data):
    """
    Tetap cek kemungkinan format:

        double frequency
        double power

    tetapi ini hanya diagnostic.
    """

    print("\n=== SEARCH DOUBLE FREQ/POWER PAIRS ===")

    found = False

    for off in range(
        0,
        len(data) - 16,
        8
    ):

        try:

            freq = struct.unpack_from(
                "<d",
                data,
                off
            )[0]

            power = struct.unpack_from(
                "<d",
                data,
                off + 8
            )[0]

        except struct.error:
            continue

        if not (
            math.isfinite(freq)
            and math.isfinite(power)
            and 1e6 <= freq <= 3e9
            and -300 <= power <= 200
        ):
            continue

        points = []

        pos = off
        previous_freq = -math.inf

        while pos + 16 <= len(data):

            freq2, power2 = struct.unpack_from(
                "<dd",
                data,
                pos
            )

            if not (
                math.isfinite(freq2)
                and math.isfinite(power2)
                and 1e6 <= freq2 <= 3e9
                and freq2 > previous_freq
                and -300 <= power2 <= 200
            ):
                break

            points.append(
                (
                    freq2,
                    power2
                )
            )

            previous_freq = freq2

            pos += 16

        if len(points) >= 20:

            print(
                f"\nFound possible sweep "
                f"at offset {off} / 0x{off:X}"
            )

            print(
                f"points: {len(points)}"
            )

            print(
                "frequency:",
                f"{points[0][0] / 1e6:.3f}",
                "-",
                f"{points[-1][0] / 1e6:.3f}",
                "MHz"
            )

            powers = [
                p for _, p in points
            ]

            print(
                "power:",
                f"{min(powers):.2f}",
                "-",
                f"{max(powers):.2f}",
                "dBm"
            )

            print(
                "first 10:"
            )

            for freq2, power2 in points[:10]:

                print(
                    f"  "
                    f"{freq2 / 1e6:10.3f} MHz "
                    f"{power2:8.2f}"
                )

            found = True

            break

    if not found:
        print(
            "No double frequency/power sweep found."
        )


def analyze_measurement(data, measure_id):
    """
    Analisis raw response.
    """

    print()
    print("=" * 70)
    print(
        f"ANALYSIS MEASURE ID {measure_id}"
    )
    print("=" * 70)

    print(
        f"Body length: {len(data)} bytes"
    )

    if len(data) >= 4:

        first_u32 = struct.unpack_from(
            "<I",
            data,
            0
        )[0]

        print(
            f"body[0:4] uint32 = "
            f"{first_u32}"
        )

    print("\n=== HEXDUMP FIRST 256 BYTES ===")

    hexdump(
        data,
        max_bytes=256
    )

    dump_uint32(
        data,
        max_bytes=128
    )

    dump_int32(
        data,
        max_bytes=128
    )

    dump_float32(
        data,
        max_bytes=128
    )

    dump_float64(
        data,
        max_bytes=128
    )

    search_known_values(data)

    search_frequency_double_pairs(data)

    find_float32_power_regions(data)

    find_int16_power_regions(data)


# ============================================================
# MAIN
# ============================================================

def main():

    c = CSMSClient(
        HOST,
        port=PORT,
        timeout=TIMEOUT
    )

    try:

        # ====================================================
        # CONNECT
        # ====================================================

        print(
            f"Connecting to "
            f"{HOST}:{PORT} ..."
        )

        c.connect()

        print(
            "TCP connected."
        )

        # ====================================================
        # GREETING
        # ====================================================

        print(
            "\nSending greeting..."
        )

        greeting = c.greeting()

        if not greeting:

            raise RuntimeError(
                "No greeting response"
            )

        print(
            "Greeting response:",
            greeting
        )

        if greeting.msg_type != 8566:

            raise RuntimeError(
                f"Unexpected greeting "
                f"type={greeting.msg_type}"
            )

        if len(c.token) != 4:

            raise RuntimeError(
                f"Invalid token length: "
                f"{len(c.token)}"
            )

        print(
            f"Token: {c.token.hex()}"
        )

        # ====================================================
        # SCHEDULE MEASUREMENT
        # ====================================================

        print(
            "\nScheduling measurement..."
        )

        schedule_params = struct.pack(
            "<ddddII",
            START_FREQ,
            STOP_FREQ,
            STEP_FREQ,
            RBW,
            DWELL_MS,
            SWEEP_TYPE
        )

        # Ini mengikuti request Anda yang
        # SUDAH mendapatkan response valid.
        schedule_body = (
            c.token
            +
            schedule_params
        )

        c.marker += 1

        schedule_marker = c.marker

        schedule_packet = HDR.pack(
            schedule_marker,
            0,          # field4
            27,         # msgType
            5,          # cmdVer - dipertahankan dari test berhasil
            2,          # respVer
            71000,      # ScheduleMeasurement
            len(schedule_body)
        ) + schedule_body

        print(
            f"Schedule marker: "
            f"{schedule_marker}"
        )

        print(
            f"Schedule bodyLen: "
            f"{len(schedule_body)}"
        )

        c.sock.sendall(
            schedule_packet
        )

        schedule_resp = c.recv()

        if not schedule_resp:

            raise RuntimeError(
                "No schedule response"
            )

        print(
            "\nSchedule response:"
        )

        print(
            schedule_resp
        )

        print(
            "type      :",
            schedule_resp.msg_type
        )

        print(
            "subtype   :",
            schedule_resp.subtype
        )

        print(
            "cmdVer    :",
            schedule_resp.cmd_ver
        )

        print(
            "respVer   :",
            schedule_resp.resp_ver
        )

        print(
            "marker    :",
            schedule_resp.marker
        )

        print(
            "bodyLen   :",
            schedule_resp.body_len
        )

        print(
            "body HEX  :",
            schedule_resp.body.hex(" ")
        )

        # Jangan lagi menyebut offset 24 sebagai taskId
        # sebelum format subtype 72000 benar-benar diketahui.

        # ====================================================
        # WAIT
        # ====================================================

        print(
            "\nWaiting for measurement "
            "to complete..."
        )

        time.sleep(3)

        # ====================================================
        # RETRIEVE
        # ====================================================

        print(
            "\nPolling measurement IDs..."
        )

        measurement_found = False

        for mid in range(
            MEASURE_ID_START,
            MEASURE_ID_END
        ):

            retrieve_body = struct.pack(
                "<I",
                mid
            )

            c.marker += 1

            marker = c.marker

            # Penting:
            # bodyLen=4 dan hanya measureId.
            #
            # Ini mengikuti packet Anda yang
            # sudah menghasilkan response 72002.
            packet = HDR.pack(
                marker,
                0,
                27,
                1,
                2,
                71002,
                len(retrieve_body)
            ) + retrieve_body

            c.sock.sendall(
                packet
            )

            resp = c.recv()

            if not resp:

                print(
                    f"mid={mid}: "
                    f"no response"
                )

                time.sleep(0.1)

                continue

            print(
                f"mid={mid}: "
                f"type={resp.msg_type} "
                f"sub={resp.subtype} "
                f"marker={resp.marker} "
                f"bodyLen={resp.body_len}"
            )

            # Response measurement result
            if (
                resp.msg_type == 27
                and
                resp.subtype == 72002
            ):

                print(
                    "\n*** MEASUREMENT RESPONSE FOUND ***"
                )

                print(
                    f"measureId requested: "
                    f"{mid}"
                )

                print(
                    f"bodyLen: "
                    f"{resp.body_len}"
                )

                # --------------------------------------------
                # Verify measureId body[0:4]
                # --------------------------------------------

                if resp.body_len >= 4:

                    returned_mid = (
                        struct.unpack_from(
                            "<I",
                            resp.body,
                            0
                        )[0]
                    )

                    print(
                        f"measureId in body: "
                        f"{returned_mid}"
                    )

                # --------------------------------------------
                # Status heuristic lama
                # --------------------------------------------

                if resp.body_len >= 8:

                    old_status_guess = (
                        int.from_bytes(
                            resp.body[-8:-4],
                            "little"
                        )
                    )

                    print(
                        f"status guess "
                        f"[-8:-4]: "
                        f"{old_status_guess}"
                    )

                # --------------------------------------------
                # ALWAYS SAVE RAW FILE
                # --------------------------------------------

                filename = (
                    OUTPUT_DIR
                    /
                    f"sweep_{mid}.bin"
                )

                with open(
                    filename,
                    "wb"
                ) as fp:

                    fp.write(
                        resp.body
                    )

                print(
                    f"Saved raw body:"
                )

                print(
                    filename.resolve()
                )

                # --------------------------------------------
                # ANALYZE
                # --------------------------------------------

                analyze_measurement(
                    resp.body,
                    mid
                )

                measurement_found = True

                break

            time.sleep(0.1)

        if not measurement_found:

            print(
                "\nNo subtype 72002 "
                "measurement response found."
            )

    except KeyboardInterrupt:

        print(
            "\nStopped by user."
        )

    except Exception as exc:

        print(
            "\nERROR:"
        )

        print(
            type(exc).__name__,
            exc
        )

        raise

    finally:

        print(
            "\nClosing CSMS connection..."
        )

        c.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()