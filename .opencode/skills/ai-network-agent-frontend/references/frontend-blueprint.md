# AI Network Agent Frontend Blueprint

This is the product blueprint for the frontend. Implement only the scope requested in the current task.

## Dashboard

Key widgets:

- Total Devices
- Online / Offline / Warning
- Active Labs by engine
- AI tasks today
- Network Health
- Network health chart
- Device status table
- Recent AI operations
- Alerts
- service connectivity

## Devices

List columns may include:

- Device
- Vendor
- Model
- Management IP
- Platform
- Status
- CPU
- Memory
- Latency
- Last Seen
- Actions

Useful actions:

- Open
- Terminal/SSH session via backend
- Run Command
- Configure
- Backup

## Device detail

Tabs:

- Overview
- Interfaces
- Routing
- Configuration
- Commands
- Backups
- Metrics
- Logs

## AI Agent

Core controls:

- prompt input
- device/lab context
- Run
- Dry Run
- Plan Only

The response area should be able to present:

- reasoning summary / plan
- state collected from devices
- candidate configuration
- warnings
- validation
- execution progress

Do not expose hidden model chain-of-thought; show concise plan/explanation produced for the user.

## Execution Plan

Show:

- task
- target devices
- planned actions
- risk
- candidate change summary
- backup plan
- verification plan

Actions:

- Approve & Execute
- Modify Plan
- Cancel

## Terminal

Show:

- selected device
- connection status
- streaming output
- command input/history
- reconnect
- clear
- copy
- save output
- fullscreen
- AI explanation

## Labs

List:

- name
- engine
- nodes
- state
- CPU/RAM if known
- created time

Actions:

- Open
- Start
- Stop
- Restart
- Delete/Destroy with confirmation

## Lab detail

Tabs:

- Topology
- Nodes
- Links
- Console
- Agent
- Logs

## Topology

Node categories:

- Cisco
- MikroTik
- Aruba
- Linux
- PC
- NAT
- Cloud

Show hostname/vendor/status and useful interface/link context.

## GNS3

Show:

- server/controller connectivity
- GNS3 VM connectivity
- project list
- node count/state
- start/stop actions

## Containerlab

Show:

- topology files
- active labs
- nodes
- images
- validate/deploy/destroy
- YAML editor if required

## Configurations

Modes may include:

- Raw CLI
- Structured
- AI Generated

Always provide dry-run/diff when backend supports it.

## Backups

Show:

- device
- time
- type
- size
- creator/source
- view
- compare
- restore
- download

Restore is a risky action and requires confirmation.

## Audit

Log:

- time
- actor
- source (`User`, `AI Agent`, `Automation`, `API`)
- action
- device/lab
- result
- details

## Alerts

Common types:

- Device Offline
- Interface Down
- High CPU
- High Memory
- Packet Loss
- SSH Failed
- Configuration Failed
- Routing Neighbor Down

Severity:

- Critical
- High
- Medium
- Low
- Info

## Discovery

Inputs may include:

- subnet
- ICMP/SSH/SNMP method
- credential profile reference

Results:

- IP
- hostname
- vendor
- platform
- protocol reachability
- add/import action

## Settings

Sections:

- General
- AI
- Devices
- SSH
- GNS3
- Containerlab
- Security
- Notifications

Useful AI safety toggles:

- Require approval before changes
- Backup before config
- Post-change validation
- Automatic rollback on failure
- Allow destructive commands (default OFF)
