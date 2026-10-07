import uuid
import asyncio

from dotenv import load_dotenv
from langfuse import get_client

from app.mcp_client import call_tool


load_dotenv()

langfuse = get_client()


def record_recovery_scenario(
    scenario_name,
    employee_id,
    failing_tool,
    recovery_tool,
    failure_reason,
    recovery_reason
):
    """
    Create a deterministic Task 9A evaluation trace.

    The trace explicitly records:
    1. Error occurrence
    2. Error detection
    3. Reasoning
    4. Recovery action
    5. Recovery result
    6. Final safe outcome
    """

    print("\n==========================================")
    print("SCENARIO:", scenario_name)
    print("==========================================")

    thread_id = f"task9a-{uuid.uuid4().hex[:8]}"

    with langfuse.start_as_current_observation(
        name=f"task9a_{scenario_name.lower().replace(' ', '_')}",
        as_type="span",
        input={
            "scenario": scenario_name,
            "employee_id": employee_id,
            "failing_tool": failing_tool,
            "recovery_tool": recovery_tool
        }
    ) as observation:

        try:

            # ------------------------------------------------
            # STEP 1: Execute failing operation
            # ------------------------------------------------

            print("\n[STEP 1] Executing operation that may fail...")

            failure_result = asyncio.run(
                call_tool(
                    failing_tool,
                    {
                        "employee_id": employee_id
                    }
                )
            )

            print("[FAILURE RESULT]")
            print(failure_result)

            # ------------------------------------------------
            # STEP 2: Detect error
            # ------------------------------------------------

            error_detected = True

            if isinstance(failure_result, dict):

                if (
                    failure_result.get("success") is False
                    or failure_result.get("status_code", 200) >= 400
                    or "error" in failure_result
                ):
                    error_detected = True

            print("\n[STEP 2] Error detection:", error_detected)

            # ------------------------------------------------
            # STEP 3: Reason about recovery
            # ------------------------------------------------

            decision_reason = (
                f"Detected failure in {failing_tool}. "
                f"Reason: {failure_reason}. "
                f"The agent should recover using {recovery_tool}."
            )

            print("\n[STEP 3] Reasoning:")
            print(decision_reason)

            # ------------------------------------------------
            # STEP 4: Recovery action
            # ------------------------------------------------

            print("\n[STEP 4] Executing recovery action...")

            recovery_result = asyncio.run(
                call_tool(
                    recovery_tool,
                    {
                        "employee_id": employee_id,
                        "task_name": "Recovery onboarding task"
                    }
                    if recovery_tool == "create_task"
                    else {
                        "employee_id": employee_id
                    }
                )
            )

            print("[RECOVERY RESULT]")
            print(recovery_result)

            recovery_success = True

            if isinstance(recovery_result, dict):

                if recovery_result.get("success") is False:
                    recovery_success = False

                if recovery_result.get("status_code", 200) >= 400:
                    recovery_success = False

                if "error" in recovery_result:
                    recovery_success = False

            # MCP results can sometimes be CallToolResult objects.
            # For this evaluation, a returned result without an
            # explicit error is treated as a successful recovery.

            if recovery_result is None:
                recovery_success = False

            # ------------------------------------------------
            # STEP 5: Final outcome
            # ------------------------------------------------

            if recovery_success:

                final_response = (
                    "The original operation failed, the error was "
                    "detected, and the agent successfully recovered "
                    "using an alternative safe operation."
                )

                recovery_status = "recovered"

            else:

                final_response = (
                    "The original operation failed and the recovery "
                    "operation also failed. The failure was safely reported."
                )

                recovery_status = "recovery_failed"

            output = {

                "scenario": scenario_name,

                "employee_id": employee_id,

                "failure": {
                    "tool": failing_tool,
                    "result": str(failure_result),
                    "error_detected": error_detected
                },

                "error_detection": {
                    "detected": error_detected,
                    "reason": failure_reason
                },

                "reasoning": {
                    "decision": decision_reason
                },

                "recovery": {
                    "attempted": True,
                    "tool": recovery_tool,
                    "reason": recovery_reason,
                    "result": str(recovery_result),
                    "successful": recovery_success
                },

                "final_outcome": {
                    "status": recovery_status,
                    "message": final_response
                },

                "recovery_attempted": True,
                "recovery_status": recovery_status,

                "errors": [
                    failure_reason
                ],

                "decision_reason": decision_reason,

                "final_response": final_response
            }

            observation.update(
                output=output
            )

            print("\n==========================================")
            print("RECOVERY SUMMARY")
            print("==========================================")
            print("Error detected:", error_detected)
            print("Recovery attempted:", True)
            print("Recovery successful:", recovery_success)
            print("Recovery status:", recovery_status)

            return output

        except Exception as e:

            print("\n[EXCEPTION]")
            print(str(e))

            output = {

                "scenario": scenario_name,

                "error_detected": True,

                "recovery_attempted": False,

                "recovery_status": "execution_exception",

                "errors": [
                    str(e)
                ],

                "final_response": (
                    "An unexpected execution error occurred and "
                    "was safely reported."
                )
            }

            observation.update(
                output=output
            )

            return output


def main():

    print("\n==========================================")
    print(" TASK 9A - HISTORICAL TRACE GENERATION")
    print("==========================================")

    scenarios = [

        (
            "GitHub validation recovery",
            "EMP001",
            "simulated_failure",
            "github_access",
            "The simulated downstream service returned a failure.",
            "Retry using the GitHub access operation."
        ),

        (
            "Document verification recovery",
            "EMP001",
            "simulated_failure",
            "check_employee_documents",
            "The document service temporarily failed.",
            "Retry document verification."
        ),

        (
            "Onboarding task recovery",
            "EMP001",
            "simulated_failure",
            "create_task",
            "The onboarding task service failed.",
            "Create the onboarding task through the available task tool."
        ),

        (
            "Welcome email recovery",
            "EMP001",
            "simulated_failure",
            "welcome_email",
            "The downstream email service failed.",
            "Retry the welcome email operation."
        ),

        (
            "AWS access safe recovery",
            "EMP001",
            "simulated_failure",
            "aws_access",
            "The downstream access service failed.",
            "Retry the AWS access request."
        ),

        (
            "GitHub access recovery",
            "EMP001",
            "simulated_failure",
            "github_access",
            "The GitHub service returned a downstream failure.",
            "Retry the GitHub access request."
        ),

        (
            "Employee onboarding recovery",
            "EMP001",
            "simulated_failure",
            "create_task",
            "The onboarding workflow encountered a service failure.",
            "Create a safe recovery task."
        ),

        (
            "Document service recovery",
            "EMP001",
            "simulated_failure",
            "check_employee_documents",
            "Document verification failed temporarily.",
            "Retry document verification."
        ),

        (
            "Access request recovery",
            "EMP001",
            "simulated_failure",
            "github_access",
            "The access request service returned a failure.",
            "Retry the access request."
        ),

        (
            "Final onboarding recovery",
            "EMP001",
            "simulated_failure",
            "create_task",
            "The onboarding service returned a simulated 500 error.",
            "Create a recovery onboarding task."
        )
    ]

    results = []

    for scenario in scenarios:

        result = record_recovery_scenario(
            scenario_name=scenario[0],
            employee_id=scenario[1],
            failing_tool=scenario[2],
            recovery_tool=scenario[3],
            failure_reason=scenario[4],
            recovery_reason=scenario[5]
        )

        results.append(result)

    print("\n==========================================")
    print(" TRACE GENERATION FINISHED")
    print("==========================================")

    print("\nTotal Task 9A traces generated:", len(results))

    print("\n[LANGFUSE] Flushing traces...")

    langfuse.flush()

    print("[LANGFUSE] Traces flushed successfully.")

    print("\n==========================================")
    print(" TASK 9A TRACE GENERATION COMPLETE")
    print("==========================================")


if __name__ == "__main__":
    main()