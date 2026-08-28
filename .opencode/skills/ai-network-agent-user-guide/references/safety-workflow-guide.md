# Safety Workflow Guide

The agent uses safety states:

```text
READ_ONLY
GUARDED
APPROVAL_REQUIRED
BLOCKED
```

Read-only actions:

```text
show commands
interface checks
routing checks
Linux service status
Docker status
journalctl read
GNS3 template listing
topology draft generation
workspace file read/search
lint/test/build
```

Approval-required actions:

```text
configure Cisco/MikroTik/Aruba
deploy config
restart Linux service
install packages
edit Linux system files
create/delete GNS3 project/node/link
start/stop/destroy lab
restore backup
delete inventory device
```

Standard change workflow:

```text
Request
Plan
Validate
Dry Run
Approval
Execute
Verify
Audit
```

When the user asks why approval is needed:

Answer that the action can change network state, service state, lab state, files, or inventory. Approval prevents accidental outages or data loss.

