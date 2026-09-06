# AI Network Agent User Guide

AI Network Agent is an AI-powered Network Operations Center dashboard.

Main areas:

```text
/dashboard       Network operations overview
/agent           AI Network Agent chat
/devices         Device inventory
/devices/:id     Device detail
/terminal        Interactive SSH terminal
/labs            Lab management
/gns3            GNS3 projects and templates
/topology        Saved/live topology view
/topology-builder Topology draft and builder
/configurations  Config deployment and dry run
/tasks           Automation task history
/backups         Config backups
/alerts          Alerts
/audit           Audit log
/settings        System and AI settings
```

Default guidance:

- Use `/dashboard` to see overall health.
- Use `/devices` to add or manage devices.
- Use `/agent` for natural-language inspection, planning, and guided execution.
- Use `/terminal` for direct SSH sessions through backend-managed terminal sessions.
- Use `/gns3` and `/topology-builder` for lab and topology work.

Example questions users can ask:

```text
cara tambah device Cisco?
cara cek interface R1?
cara cek service frigate di ubuntu?
cara connect terminal ke MK-1?
buatkan topologi GNS3 untuk routing BGP
kenapa command ini butuh approval?
cara backup config semua router?
```

