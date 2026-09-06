---
name: agent-intent-routing-policy
description: Define how AI Network Agent classifies user messages into software, Linux admin, network read-only, network change, GNS3 topology generation, device inventory, troubleshooting, and user-guide intents.
metadata:
  opencode/autoinvoke: "true"
---

# Agent Intent Routing Policy

Use this skill when implementing or changing how the `/agent` backend decides which tool family should handle a user message.

The classifier should return structured intent, not only prose.

Read `references/intent-routing.md` before changing agent routing.

