import os

from dotenv import load_dotenv
from langfuse import get_client


load_dotenv()


langfuse = get_client()


def start_agent_trace(employee_id):
    return langfuse.start_as_current_span(
        name="employee-onboarding-agent",
        input={
            "employee_id": employee_id
        }
    )