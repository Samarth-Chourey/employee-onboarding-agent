from typing import TypedDict, List, Any


class OnboardingState(TypedDict):
    # Employee information
    employee_id: str
    employee_name: str
    role: str
    department: str

    # Current workflow
    current_task: str

    completed_tasks: List[str]
    pending_tasks: List[str]

    # Error handling
    errors: List[str]

    # HITL
    approval_required: bool
    approval_status: str

    # Tool execution
    tool_result: str

    # Gemini decision explanation
    decision_reason: str

    # Final response
    final_response: str

    # Conversation memory
    messages: List[Any]
