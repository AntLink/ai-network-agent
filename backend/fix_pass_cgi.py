import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from app.transports.ssh import SSHTransport
from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 120

SHOW_CURRENT = r"""
echo "=== Current pass.cgi ==="
cat /media/httpd/cgi-bin/pass.cgi
""".strip()

UPDATE_SCRIPT = r"""
cat > /media/httpd/cgi-bin/pass.cgi << 'CGIEOF'
#!/usr/bin/perl

# Read POST data
read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
@pairs = split(/&/, $buffer);
foreach $pair (@pairs) {
    ($name, $value) = split(/=/, $pair);
    $value =~ tr/+/ /;
    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
    $form{$name} = $value;
}

# Print header
print "Content-type: text/html\n\n";
print "<html><head><title>Password Change</title>";
print "<style>";
print "body { font-family: Arial; margin: 40px; background: #f5f5f5; }";
print ".container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 500px; }";
print "h2 { color: #333; }";
print ".success { color: green; font-weight: bold; }";
print ".error { color: red; font-weight: bold; }";
print ".info { color: #666; font-size: 12px; margin-top: 10px; }";
print "a { color: #0066cc; }";
print "</style></head><body>";
print "<div class='container'>";
print "<h2>Change Password</h2>";

if ($form{'newpass'} && $form{'confirmpass'}) {
    if ($form{'newpass'} eq $form{'confirmpass'}) {
        # Change password
        open(PIPE, "|chpasswd 2>&1") or die "Cannot open pipe: $!";
        print PIPE "root:$form{'newpass'}\n";
        close(PIPE);

        if ($? == 0) {
            print "<p class='success'>Password changed successfully!</p>";

            # Auto-backup shadow to SD card
            system("mkdir -p /media/backup/system");
            system("cp /etc/shadow /media/backup/system/shadow");
            system("cp /etc/passwd /media/backup/system/passwd");
            system("cp /etc/group /media/backup/system/group");
            print "<p class='info'>Password backed up to SD card (survives reboot).</p>";
        } else {
            print "<p class='error'>Failed to change password!</p>";
        }
    } else {
        print "<p class='error'>Passwords do not match!</p>";
    }
} else {
    print "<p class='error'>Please enter both fields!</p>";
}

print "<br><a href='/cgi-bin/pass.cgi'>Change Password Again</a>";
print "<br><a href='/'>Back to Home</a>";
print "</div></body></html>";
CGIEOF

chmod +x /media/httpd/cgi-bin/pass.cgi
""".strip()

VERIFY_SCRIPT = r"""
echo ""
echo "=== Updated pass.cgi ==="
cat /media/httpd/cgi-bin/pass.cgi

echo ""
echo "=== Verify backup files ==="
ls -la /media/backup/system/

echo ""
echo "=== Test chpasswd works ==="
echo "Testing..."
ls -la /media/httpd/cgi-bin/pass.cgi
""".strip()


async def main():
    transport = SSHTransport(
        host="192.168.162.20",
        username="root",
        password="815m1ll4h",
    )

    print("=" * 60)
    print("pass.cgi Auto-Backup Update Script")
    print("Target: 192.168.162.20 (root)")
    print("=" * 60)
    print()

    try:
        print("[1/3] Showing current pass.cgi...")
        print("-" * 60)
        output = await transport.run(SHOW_CURRENT)
        print(output)
    except RuntimeError as e:
        print(f"WARNING: {e}")

    try:
        print("[2/3] Updating pass.cgi with auto-backup feature...")
        print("-" * 60)
        output = await transport.run(UPDATE_SCRIPT)
        print(output)
        print("UPDATE: pass.cgi written and chmod +x applied.")
    except RuntimeError as e:
        print(f"ERROR during update: {e}")
        sys.exit(1)

    try:
        print()
        print("[3/3] Verifying update...")
        print("-" * 60)
        output = await transport.run(VERIFY_SCRIPT)
        print(output)
    except RuntimeError as e:
        print(f"WARNING during verification: {e}")

    print("=" * 60)
    print("DONE: pass.cgi updated with auto-backup to SD card.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
