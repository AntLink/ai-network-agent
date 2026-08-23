"""
Parse frequency data from CSMS database BLOBs on the embedded Linux system.

Connects via SSH to 192.168.162.20 and runs a series of analysis commands
against /tmp/csmsdb.db (SQLite database with BLOB columns).
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# 1. Load dotenv from backend/.env
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

# Import after dotenv so settings pick up env vars if needed
from app.transports.ssh import SSHTransport  # noqa: E402
from app.core.config import settings  # noqa: E402

# Set command timeout to 120 seconds as required
settings.SSH_COMMAND_TIMEOUT = 120

HOST = "192.168.162.20"
USERNAME = "root"
PASSWORD = "815m1ll4h"

ANALYSIS_SCRIPT = r'''
echo "=========================================="
echo "  CSMS FREQUENCY BLOB ANALYSIS"
echo "=========================================="

echo ""
echo "=== 1. Copy database to local for analysis ==="
# Already copied to /tmp/csmsdb.db
ls -la /tmp/csmsdb.db

echo ""
echo "=== 2. Extract sample BLOBs ==="
# Use Perl to read SQLite and extract BLOBs
cat > /tmp/extract_blobs.pl << 'PERLEOF'
#!/usr/bin/perl
use strict;
use warnings;

# Read SQLite database and extract BLOBs
my $dbfile = "/tmp/csmsdb.db";
open(my $fh, '<:raw', $dbfile) or die "Cannot open $dbfile: $!";

# Read entire file
local $/;
my $content = <$fh>;
close($fh);

# Find BLOB patterns (look for frequency-like data)
# TCI protocol likely uses 4-byte or 8-byte frequency values
my @blobs;
while ($content =~ /([\x00-\xff]{16,})/g) {
    my $blob = $1;
    # Check if it contains frequency-like patterns
    if ($blob =~ /[\x00-\xff]{4}/) {
        push @blobs, $blob;
    }
}

print "Found " . scalar(@blobs) . " potential BLOBs\n";

# Analyze first few BLOBs
for my $i (0..9) {
    last if $i >= @blobs;
    my $blob = $blobs[$i];
    print "\n--- BLOB $i (length: " . length($blob) . ") ---\n";
    # Print hex dump of first 64 bytes
    my $hex = unpack("H*", substr($blob, 0, 64));
    print "Hex: $hex\n";
    # Try to extract readable strings
    my @strings = ($blob =~ /([\x20-\x7e]{4,})/g);
    if (@strings) {
        print "Strings: " . join(", ", @strings[0..2]) . "\n";
    }
}
PERLEOF
chmod +x /tmp/extract_blobs.pl
perl /tmp/extract_blobs.pl

echo ""
echo "=== 3. Check for frequency patterns in raw DB ==="
# Look for 4-byte frequency values (in Hz)
# Common frequencies: 100MHz = 0x05F5E100, 400MHz = 0x17D78400
strings /tmp/csmsdb.db | grep -E "^[0-9]{6,9}$" | head -20

echo ""
echo "=== 4. Check BLOB structure with hex dump ==="
# Extract a BLOB and hex dump it
cat > /tmp/hex_blobs.pl << 'PERLEOF2'
#!/usr/bin/perl
use strict;
use warnings;

my $dbfile = "/tmp/csmsdb.db";
open(my $fh, '<:raw', $dbfile) or die "Cannot open $dbfile: $!";
local $/;
my $content = <$fh>;
close($fh);

# Find all BLOBs (binary data between quotes in SQLite)
my $count = 0;
while ($content =~ /x'([0-9a-fA-F]+)'/g) {
    my $hex = $1;
    my $len = length($hex) / 2;
    next if $len < 8;

    print "\n--- BLOB $count (decoded length: $len bytes) ---\n";

    # Convert hex to binary
    my $binary = pack("H*", $hex);

    # Print first 128 bytes as hex
    my $print_len = ($len > 128) ? 128 : $len;
    print "Hex dump (first $print_len bytes):\n";
    for my $i (0..($print_len-1)) {
        printf "%02x ", ord(substr($binary, $i, 1));
        print "\n" if (($i+1) % 16 == 0);
    }
    print "\n";

    # Look for frequency values (4-byte little-endian integers)
    # Typical RF frequencies in Hz: 100MHz = 100000000 = 0x05F5E100
    for my $offset (0..($len-4)) {
        my $val = unpack("V", substr($binary, $offset, 4));
        if ($val > 80000000 && $val < 10000000000) {  # 80 MHz to 10 GHz
            my $mhz = $val / 1000000;
            printf "  Possible freq at offset %d: %d Hz (%.2f MHz)\n", $offset, $val, $mhz;
        }
    }

    $count++;
    last if $count >= 5;  # Only first 5 BLOBs
}
PERLEOF2
chmod +x /tmp/hex_blobs.pl
perl /tmp/hex_blobs.pl

echo ""
echo "=== 5. Check Schedule table ==="
cat > /tmp/read_schedule.pl << 'PERLEOF3'
#!/usr/bin/perl
use strict;
use warnings;

my $dbfile = "/tmp/csmsdb.db";
open(my $fh, '<:raw', $dbfile) or die "Cannot open $dbfile: $!";
local $/;
my $content = <$fh>;
close($fh);

# Find Schedule table entries
if ($content =~ /Schedule.*?MeasureId/s) {
    print "Schedule table found\n";
    # Extract text around Schedule
    my $idx = index($content, "Schedule");
    if ($idx >= 0) {
        my $context = substr($content, $idx, 500);
        print "Context: $context\n";
    }
}
PERLEOF3
perl /tmp/read_schedule.pl

echo ""
echo "=== 6. Check Results table ==="
cat > /tmp/read_results.pl << 'PERLEOF4'
#!/usr/bin/perl
use strict;
use warnings;

my $dbfile = "/tmp/csmsdb.db";
open(my $fh, '<:raw', $dbfile) or die "Cannot open $dbfile: $!";
local $/;
my $content = <$fh>;
close($fh);

# Find Results table entries
if ($content =~ /Results.*?MsgBody/s) {
    print "Results table found\n";
    my $idx = index($content, "Results");
    if ($idx >= 0) {
        my $context = substr($content, $idx, 500);
        print "Context: $context\n";
    }
}
PERLEOF4
perl /tmp/read_results.pl

echo ""
echo "=== 7. Try to find TCI message format ==="
strings /tmp/csmsdb.db | grep -iE "freq|power|dBm|MHz|GHz|signal|channel|band|scan|sweep" | head -30

echo ""
echo "SCRIPT_COMPLETE"
'''


async def main() -> None:
    transport = SSHTransport(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
    )

    print(f"[+] Connecting to {HOST} as {USERNAME} "
          f"(command timeout: {settings.SSH_COMMAND_TIMEOUT}s)")
    output = await transport.run(ANALYSIS_SCRIPT)

    print()
    print("=" * 60)
    print("FULL REMOTE OUTPUT")
    print("=" * 60)
    print(output)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"[!] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
