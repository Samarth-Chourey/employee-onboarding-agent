from app.graph import graph
from langgraph.types import Command
from langfuse import get_client


# ==================================================
# INITIAL EMPLOYEE STATE
# ==================================================

initial_state = {
    "employee_id": "EMP001",
    "employee_name": "Rahul Sharma",
    "role": "Software Engineer",
    "department": "Engineering",

    "current_task": "AWS Access",

    "completed_tasks": [],

    "pending_tasks": [
        "AWS Access"
    ],

    "errors": [],

    "approval_required": False,
    "approval_status": "",

    "tool_result": "",
    "decision_reason": "",
    "final_response": "",
    "messages": []
}


# ==================================================
# LANGGRAPH THREAD CONFIGURATION
# ==================================================

config = {
    "configurable": {
        "thread_id": "onboarding-EMP001"
    }
}


try:

    # ==================================================
    # START THE ONBOARDING WORKFLOW
    # ==================================================

    print("\n========== STARTING AGENT ==========")

    result = graph.invoke(
        initial_state,
        config
    )


    # ==================================================
    # CHECK CURRENT GRAPH STATE
    # ==================================================

    state = graph.get_state(config)


    print("\n========== AGENT STATUS ==========")

    print("Employee:", initial_state["employee_name"])
    print("Role:", initial_state["role"])


    # ==================================================
    # HUMAN-IN-THE-LOOP
    # ==================================================

    if state.interrupts:

        print("\nSTATUS: WAITING FOR HUMAN APPROVAL")

        print("\nApproval request:")
        print(state.interrupts[0].value)


        choice = input(
            "\nEnter approval decision (approve/reject): "
        ).strip().lower()


        if choice not in ["approve", "reject"]:

            print("\nInvalid choice.")
            print("Please enter only: approve or reject.")

            raise SystemExit


        print(f"\nHuman decision: {choice}")


        # ==================================================
        # RESUME THE SAME PAUSED WORKFLOW
        # ==================================================

        resumed_result = graph.invoke(
            Command(resume=choice),
            config
        )


        print("\n========== RESUMED AGENT ==========")

        print(
            "Current Task:",
            resumed_result["current_task"]
        )

        print("\nGemini's Reasoning:")
        print(
            resumed_result["decision_reason"]
        )

        print("\nTool Result:")
        print(
            resumed_result["tool_result"]
        )


    else:

        # ==================================================
        # WORKFLOW COMPLETED WITHOUT APPROVAL
        # ==================================================

        print("\nSTATUS: COMPLETED")

        print(
            "Current Task:",
            result["current_task"]
        )

        print("\nGemini's Reasoning:")
        print(
            result["decision_reason"]
        )

        print("\nTool Result:")
        print(
            result["tool_result"]
        )


    print("\n==================================")


finally:

    # ==================================================
    # FLUSH LANGFUSE TELEMETRY
    # ==================================================

    try:

        langfuse = get_client()

        print("\n[LANGFUSE] Flushing telemetry...")

        langfuse.flush()

        print("[LANGFUSE] Telemetry flushed successfully.")

    except Exception as e:

        print(
            "[LANGFUSE] Flush warning:",
            e
        )
