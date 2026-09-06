---
name: assistant-ui-dashboard-layout
description: Design the AI Network Agent /agent page layout around assistant-ui, including ChatGPT-style composition, thread sidebar, context panel, sticky composer, and responsive dashboard integration.
metadata:
  opencode/autoinvoke: "true"
---

# Assistant UI Dashboard Layout

Use this skill when the task is about the page structure, spacing, and visual integration of assistant-ui inside the dashboard.

## Layout goals

- ChatGPT-like chat column.
- Session list sidebar.
- Context/risk panel.
- Sticky composer.
- Responsive mobile drawer for thread list.
- Preserve the existing shadcn dashboard shell.

## Visual rules

- Use the existing dashboard design system.
- Keep dark mode readable and calm.
- Use strong hierarchy and spacing.
- Avoid default generic chat app styling.
- Make the chat feel like part of the network operations console.

## Page anatomy

- Header with title, model, device selector, lab selector, and safety mode.
- Main thread viewport with message list.
- Composer docked at bottom.
- Secondary panel for plan, devices, and verification.

## Don't do

- Do not rebuild the entire app shell.
- Do not add a separate chatbot-only route without dashboard context.
- Do not hide critical operational state below the fold on desktop.

