# Agent Chat Guide

Route:

```text
/agent
```

The agent chat is for:

- read-only inspection,
- troubleshooting,
- planning configuration changes,
- generating dry runs,
- approving safe execution,
- explaining CLI output,
- checking Linux services and Docker,
- generating GNS3 topology drafts,
- software/code assistance when OpenHands SDK integration is enabled.

Useful prompts:

```text
cek interface R1
tampilkan routing table R1 dan R2
cek service frigate di ubuntu
cek docker di ubuntu
cek ip address MK-1
buatkan plan konfigurasi OSPF antara R1 dan R2
buatkan topologi GNS3 untuk BGP 2 Cisco dan 1 MikroTik
jelaskan output command ini
```

Expected behavior:

- Read-only checks return facts and evidence.
- Risky changes return a plan and approval request.
- The agent should preserve context in follow-up messages like `oke`, `lanjut`, or `maksudnya`.
- The agent should separate backend snapshot evidence from live command output.

Workflow states:

```text
Thinking
Planning
Waiting approval
Running
Verifying
Completed
Failed
```

If a response says data is not available, ask a more specific live check:

```text
jalankan live check service frigate di ubuntu
cek port 8554 dan docker container frigate di ubuntu
```

