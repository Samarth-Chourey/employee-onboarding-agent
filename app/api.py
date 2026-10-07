from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from app.graph import graph
from langgraph.types import Command


app = FastAPI(
    title="Employee Onboarding Agent",
    description="Intelligent Employee Onboarding & Access Orchestration Agent",
    version="1.0.0"
)


class WebhookRequest(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    department: str
    task: str
    approval: Optional[str] = None


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Employee Onboarding Agent"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/webhook")
def webhook(request: WebhookRequest):

    initial_state = {
        "employee_id": request.employee_id,
        "employee_name": request.employee_name,
        "role": request.role,
        "department": request.department,
        "current_task": request.task,
        "completed_tasks": [],
        "pending_tasks": [],
        "errors": [],
        "approval_required": False,
        "approval_status": "",
        "tool_result": "",
        "decision_reason": "",
        "final_response": "",
        "messages": [],
    }

    config = {
        "configurable": {
            "thread_id": f"api-{request.employee_id}"
        }
    }

    result = graph.invoke(initial_state, config=config)

    if "__interrupt__" in result:
        return {
            "status": "approval_required",
            "employee_id": request.employee_id,
            "interrupt": str(result["__interrupt__"])
        }

    return {
        "status": "completed",
        "employee_id": request.employee_id,
        "decision_reason": result.get("decision_reason", ""),
        "tool_result": result.get("tool_result", ""),
        "final_response": result.get("final_response", ""),
        "errors": result.get("errors", [])
    }