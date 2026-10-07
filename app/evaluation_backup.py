import asyncio
import json

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import get_client

from app.tools import (
    get_employee,
    check_documents,
    create_onboarding_task,
    request_github_access,
    request_aws_access,
    send_welcome_email,
)

from app.hooks import pre_tool_hook

from app.jsonrpc import (
    create_tool_request,
    validate_jsonrpc_request,
)

from app.mcp_client import discover_tools


load_dotenv()


# ==================================================
# LANGFUSE
# ==================================================

langfuse = get_client()


# ==================================================
# LLM JUDGE
# ==================================================

judge_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
    timeout=30,
)


# ==================================================
# RUN ONE EVALUATION CASE
# ==================================================

def run_test(test_id, name, expected, test_function):

    print("\n------------------------------------------")
    print(f"TEST {test_id}: {name}")
    print("------------------------------------------")

    try:

        actual = test_function()

        result = {
            "test_id": test_id,
            "name": name,
            "expected": expected,
            "actual": actual,
            "status": "completed"
        }

        print("Expected:", expected)
        print("Actual:", actual)

    except Exception as e:

        result = {
            "test_id": test_id,
            "name": name,
            "expected": expected,
            "actual": f"ERROR: {str(e)}",
            "status": "failed"
        }

        print("ERROR:", e)


    # ------------------------------------------------
    # Create Langfuse trace for this evaluation case
    # ------------------------------------------------

    with langfuse.start_as_current_observation(
        name=f"evaluation_test_{test_id}",
        as_type="evaluator",
        input={
            "test_id": test_id,
            "name": name,
            "expected": expected
        },
    ) as observation:

        observation.update(
            output=result
        )


    return result


# ==================================================
# TEST FUNCTIONS
# ==================================================


def test_employee_lookup():

    return get_employee("EMP001")


def test_document_check():

    return check_documents("EMP001")


def test_create_task():

    return create_onboarding_task(
        "EMP001",
        "Complete security training"
    )


def test_github_access():

    return request_github_access("EMP001")


def test_aws_access():

    return request_aws_access("EMP001")


def test_welcome_email():

    return send_welcome_email("EMP001")


def test_invalid_github_employee():

    return pre_tool_hook(
        "github_access",
        {
            "employee_id": "INVALID"
        }
    )


def test_jsonrpc_request():

    request = create_tool_request(
        1,
        "aws_access",
        {
            "employee_id": "EMP001"
        }
    )

    validation = validate_jsonrpc_request(request)

    return {
        "request": request,
        "validation": validation
    }


def test_mcp_discovery():

    tools = asyncio.run(
        discover_tools()
    )

    return {
        "tool_count": len(tools),
        "tools": [
            tool.name
            for tool in tools
        ]
    }


def test_multiple_operations():

    employee = get_employee("EMP001")

    documents = check_documents("EMP001")

    task = create_onboarding_task(
        "EMP001",
        "Complete onboarding"
    )

    return {
        "employee": employee,
        "documents": documents,
        "task": task
    }


# ==================================================
# TEN EVALUATION CASES
# ==================================================

def run_all_tests():

    results = []


    results.append(
        run_test(
            1,
            "Employee lookup",
            "Employee EMP001 should be found successfully.",
            test_employee_lookup
        )
    )


    results.append(
        run_test(
            2,
            "Document verification",
            "Employee documents should be verified successfully.",
            test_document_check
        )
    )


    results.append(
        run_test(
            3,
            "Create onboarding task",
            "An onboarding task should be created successfully.",
            test_create_task
        )
    )


    results.append(
        run_test(
            4,
            "GitHub access",
            "GitHub access should be requested for a valid employee.",
            test_github_access
        )
    )


    results.append(
        run_test(
            5,
            "AWS access",
            "AWS access request should be processed for a valid employee.",
            test_aws_access
        )
    )


    results.append(
        run_test(
            6,
            "Welcome email",
            "Welcome email should be processed successfully.",
            test_welcome_email
        )
    )


    results.append(
        run_test(
            7,
            "Invalid GitHub employee",
            "Invalid employee ID should be rejected by the pre-tool hook.",
            test_invalid_github_employee
        )
    )


    results.append(
        run_test(
            8,
            "JSON-RPC request",
            "A valid JSON-RPC tools/call request should be generated and validated.",
            test_jsonrpc_request
        )
    )


    results.append(
        run_test(
            9,
            "MCP dynamic discovery",
            "MCP should dynamically discover the available tools.",
            test_mcp_discovery
        )
    )


    results.append(
        run_test(
            10,
            "Multiple onboarding operations",
            "Multiple onboarding operations should execute while returning valid results.",
            test_multiple_operations
        )
    )


    return results


# ==================================================
# LLM JUDGE
# ==================================================

def run_llm_judge(results):

    print("\n==========================================")
    print("             LLM JUDGE")
    print("==========================================")


    evaluation_text = json.dumps(
        results,
        indent=2,
        default=str
    )


    prompt = f"""
You are an expert evaluator for an
Intelligent Employee Onboarding Agent.

Evaluate the 10 test results below.

For each test:

1. Compare the expected behavior with the actual result.
2. Give a score from 0 to 10.
3. Mark it PASS or FAIL.
4. Give one short reason.

Then calculate:

Total Score
Average Score
Percentage
Overall Result

Use only the supplied test results.
Do not invent missing information.

Test Results:

{evaluation_text}
"""


    print("\n[JUDGE] Sending 10 test results to Gemini...")


    response = judge_llm.invoke(prompt)

    judge_result = response.content


    if isinstance(judge_result, list):

        judge_result = judge_result[0]["text"]


    print("\n==========================================")
    print("          LLM JUDGE RESULT")
    print("==========================================")

    print(judge_result)


    return judge_result


# ==================================================
# MAIN EVALUATION
# ==================================================

if __name__ == "__main__":

    print("\n")
    print("==========================================")
    print(" EMPLOYEE ONBOARDING AGENT EVALUATION")
    print("==========================================")


    results = run_all_tests()


    print("\n==========================================")
    print("10 TESTS COMPLETED")
    print("==========================================")


    judge_result = run_llm_judge(
        results
    )


    final_results = {

        "total_tests": len(results),

        "tests": results,

        "llm_judge": judge_result
    }


    with open(
        "evaluation_results.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_results,
            file,
            indent=4,
            ensure_ascii=False,
            default=str
        )


    # Make sure Langfuse sends everything
    # before the short-lived script exits.

    print("\n[LANGFUSE] Flushing evaluation traces...")

    langfuse.flush()

    print("[LANGFUSE] Evaluation traces flushed.")


    print("\n==========================================")
    print("EVALUATION COMPLETE")
    print("==========================================")

    print(
        "Results saved to: evaluation_results.json"
    )