"""Workflow state machine contract for backend-to-frontend agent events."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class WorkflowState(StrEnum):
    THINKING = "thinking"
    PLANNING = "planning"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


WORKFLOW_ORDER = [
    WorkflowState.THINKING,
    WorkflowState.PLANNING,
    WorkflowState.WAITING_APPROVAL,
    WorkflowState.RUNNING,
    WorkflowState.VERIFYING,
    WorkflowState.COMPLETED,
]

STATE_LABELS = {
    WorkflowState.THINKING: "Thinking",
    WorkflowState.PLANNING: "Planning",
    WorkflowState.WAITING_APPROVAL: "Waiting approval",
    WorkflowState.RUNNING: "Running",
    WorkflowState.VERIFYING: "Verifying",
    WorkflowState.COMPLETED: "Completed",
    WorkflowState.FAILED: "Failed",
}

STATE_DESCRIPTIONS = {
    WorkflowState.THINKING: "Backend sedang memahami request dan konteks sesi.",
    WorkflowState.PLANNING: "Agent menyusun rencana dan menentukan tool yang aman.",
    WorkflowState.WAITING_APPROVAL: "Perubahan berisiko menunggu approval user.",
    WorkflowState.RUNNING: "Backend menjalankan tool atau mengambil state perangkat.",
    WorkflowState.VERIFYING: "Agent memvalidasi hasil terhadap target request.",
    WorkflowState.COMPLETED: "Workflow selesai.",
    WorkflowState.FAILED: "Workflow gagal.",
}


@dataclass(frozen=True)
class WorkflowTransition:
    task_id: str
    state: WorkflowState
    detail: str = ""
    device_ids: tuple[str, ...] = ()
    session_id: str | None = None
    event_count: int = 0

    def to_event(self) -> dict[str, Any]:
        active_index = _state_index(self.state)
        return {
            "id": f"workflow-{self.task_id}-{self.state.value}",
            "taskId": self.task_id,
            "sessionId": self.session_id,
            "state": self.state.value,
            "label": STATE_LABELS[self.state],
            "detail": self.detail or STATE_DESCRIPTIONS[self.state],
            "deviceIds": list(self.device_ids),
            "activeIndex": active_index,
            "eventsCount": self.event_count,
            "steps": [
                {
                    "state": item.value,
                    "label": STATE_LABELS[item],
                    "status": _step_status(item, self.state),
                }
                for item in WORKFLOW_ORDER
            ],
            "createdAt": datetime.utcnow().isoformat(),
        }


def parse_workflow_state(value: str) -> WorkflowState:
    normalized = (value or "").strip().lower().replace("-", "_")
    for state in WorkflowState:
        if state.value == normalized:
            return state
    return WorkflowState.THINKING


def build_workflow_state_event(
    *,
    task_id: str,
    state: str | WorkflowState,
    detail: str = "",
    device_ids: list[str] | tuple[str, ...] | None = None,
    session_id: str | None = None,
    event_count: int = 0,
) -> dict[str, Any]:
    workflow_state = state if isinstance(state, WorkflowState) else parse_workflow_state(state)
    return WorkflowTransition(
        task_id=task_id,
        state=workflow_state,
        detail=detail,
        device_ids=tuple(device_ids or ()),
        session_id=session_id,
        event_count=event_count,
    ).to_event()


def _state_index(state: WorkflowState) -> int:
    try:
        return WORKFLOW_ORDER.index(state)
    except ValueError:
        return 0


def _step_status(step: WorkflowState, current: WorkflowState) -> str:
    if current == WorkflowState.FAILED:
        return "failed" if step == WorkflowState.COMPLETED else "completed"
    current_index = _state_index(current)
    step_index = _state_index(step)
    if step_index < current_index:
        return "completed"
    if step_index == current_index:
        return "active"
    return "pending"
