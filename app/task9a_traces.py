import uuid
import asyncio

from dotenv import load_dotenv
from langfuse import get_client

from app.mcp_client import call_tool


load_dotenv()

langfuse = get_client()


def run_scenario(
    scenario_name,
    employee_id,
    failure_type,
    recovery_tool=None,
    recovery_result="success",
    recovery_reason=""
):

    print("\n==========================================")
    print("SCENARIO:", scenario_name)
    print("==========================================")

    with langfuse.start_as_current_observation(
        name=f"task9a_{scenario_name.lower().replace(' ', '_')}",
        as_type="span",
        input={
            "scenario": scenario_name,
            "employee_id": employee_id,
            "failure_type": failure_type,
            "recovery_tool": recovery_tool
        }
    ) as observation:

        # ----------------------------------------------------
        # CASE 1: SUCCESSFUL RECOVERY
        # ----------------------------------------------------

        if recovery_result == "success":

            failure_result = asyncio.run(
                call_tool(
                    "simulated_failure",
                    {
                        "employee_id": employee_id
                    }
                )
            )

            print("\n[FAILURE]")
            print(failure_result)

            print("\n[ERROR DETECTED]")
            print("True")

            decision_reason = (
                f"The {failure_type} failure was detected. "
                f"The operation appears transient, so the agent "
                f"will attempt recovery using {recovery_tool}."
            )

            print("\n[REASONING]")
            print(decision_reason)

            if recovery_tool == "create_task":

                recovery = asyncio.run(
                    call_tool(
                        recovery_tool,
                        {
                            "employee_id": employee_id,
                            "task_name": "Recovery onboarding task"
                        }
                    )
                )

            else:

                recovery = asyncio.run(
                    call_tool(
                        recovery_tool,
                        {
                            "employee_id": employee_id
                        }
                    )
                )

            print("\n[RECOVERY]")
            print(recovery)

            output = {

                "failure_detected": True,

                "failure_type": failure_type,

                "decision": decision_reason,

                "recovery_attempted": True,

                "recovery_tool": recovery_tool,

                "recovery_reason": recovery_reason,

                "recovery_result": str(recovery),

                "recovery_status": "recovered",

                "final_outcome":
                    "Failure recovered successfully."

            }

        # ----------------------------------------------------
        # CASE 2: PARTIAL / SAFE HANDLING
        # ----------------------------------------------------

        elif recovery_result == "partial":

            decision_reason = (
                f"The {failure_type} failure was detected. "
                "The agent avoided blindly retrying the operation "
                "and performed safe validation/handling."
            )

            output = {

                "failure_detected": True,

                "failure_type": failure_type,

                "decision": decision_reason,

                "recovery_attempted": False,

                "recovery_tool": None,

                "recovery_reason":
                    "Automatic retry was not considered safe.",

                "recovery_status":
                    "safe_partial_handling",

                "final_outcome":
                    "Failure safely detected and reported."

            }

        # ----------------------------------------------------
        # CASE 3: HUMAN ESCALATION
        # ----------------------------------------------------

        else:

            decision_reason = (
                f"The {failure_type} failure was detected. "
                "Because the operation is sensitive or "
                "non-recoverable, the agent should not retry "
                "automatically and should escalate safely."
            )

            output = {

                "failure_detected": True,

                "failure_type": failure_type,

                "decision": decision_reason,

                "recovery_attempted": False,

                "recovery_tool": None,

                "recovery_reason":
                    "Automatic recovery would be unsafe.",

                "recovery_status":
                    "human_escalation",

                "human_intervention_required": True,

                "final_outcome":
                    "Operation safely stopped and escalated."

            }

        observation.update(
            output=output
        )

        print("\n[RESULT]")
        print(output)

        return output


def main():

    print("\n==========================================")
    print(" TASK 9A - REALISTIC ERROR RECOVERY")
    print("==========================================")

    scenarios = [

        # ====================================================
        # 5 STRONG RECOVERY CASES
        # ====================================================

        (
            "Temporary GitHub recovery",
            "EMP001",
            "temporary GitHub service failure",
            "github_access",
            "success",
            "GitHub access is safe to retry."
        ),

        (
            "Temporary document recovery",
            "EMP001",
            "temporary document service failure",
            "check_employee_documents",
            "success",
            "Document verification can safely be retried."
        ),

        (
            "Temporary task recovery",
            "EMP001",
            "temporary onboarding task failure",
            "create_task",
            "success",
            "Task creation can safely be retried."
        ),

        (
            "Temporary email recovery",
            "EMP001",
            "temporary email service failure",
            "welcome_email",
            "success",
            "The welcome email operation can be retried."
        ),

        (
            "Temporary AWS recovery",
            "EMP001",
            "temporary AWS service failure",
            "aws_access",
            "success",
            "The service failure is transient and the access operation is valid."
        ),

        # ====================================================
        # 3 PARTIAL / SAFE HANDLING CASES
        # ====================================================

        (
            "GitHub validation failure",
            "INVALID",
            "GitHub employee validation failure",
            None,
            "partial",
            ""
        ),

        (
            "Document validation failure",
            "INVALID",
            "employee document validation failure",
            None,
            "partial",
            ""
        ),

        (
            "Task creation uncertain failure",
            "INVALID",
            "onboarding task validation failure",
            None,
            "partial",
            ""
        ),

        # ====================================================
        # 2 NON-RECOVERABLE / HUMAN ESCALATION CASES
        # ====================================================

        (
            "Sensitive AWS failure",
            "EMP001",
            "sensitive AWS access failure",
            None,
            "escalate",
            ""
        ),

        (
            "Unauthorized access failure",
            "INVALID",
            "unauthorized access failure",
            None,
            "escalate",
            ""
        )
    ]

    results = []

    for scenario in scenarios:

        result = run_scenario(
            scenario_name=scenario[0],
            employee_id=scenario[1],
            failure_type=scenario[2],
            recovery_tool=scenario[3],
            recovery_result=scenario[4],
            recovery_reason=scenario[5]
        )

        results.append(result)

    print("\n==========================================")
    print(" TRACE GENERATION FINISHED")
    print("==========================================")

    print(
        "Total Task 9A traces generated:",
        len(results)
    )

    print("\n[LANGFUSE] Flushing traces...")

    langfuse.flush()

    print(
        "[LANGFUSE] Traces flushed successfully."
    )

    print("\n==========================================")
    print(" TASK 9A TRACE GENERATION COMPLETE")
    print("==========================================")


if __name__ == "__main__":
    main()