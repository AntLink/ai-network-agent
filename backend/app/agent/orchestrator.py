"""Lightweight request analysis facade for the AI Network Agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.intent_classifier import AgentIntent, classify_intent
from app.agent.tool_registry import get_tool_descriptor


@dataclass(frozen=True)
class AgentRequestAnalysis:
    intent: AgentIntent
    tools: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.to_dict(),
            "tools": list(self.tools),
        }


def analyze_request(
    message: str,
    *,
    inventory: list[dict[str, Any]] | None = None,
    device_ids: list[str] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> AgentRequestAnalysis:
    intent = classify_intent(
        message,
        inventory=inventory or [],
        device_ids=device_ids or [],
        history=history or [],
    )
    tools = tuple(
        descriptor
        for name in intent.suggested_tools
        if (descriptor := get_tool_descriptor(name)) is not None
    )
    return AgentRequestAnalysis(intent=intent, tools=tools)
