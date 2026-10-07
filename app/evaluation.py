import json
from collections import defaultdict

from dotenv import load_dotenv
from langfuse import get_client
from google import genai


load_dotenv()

langfuse = get_client()

client = genai.Client()

JUDGE_MODEL = "gemini-3.5-flash-lite"


# ============================================================
# FETCH LATEST TASK 9A TRACES
# ============================================================

def get_latest_task9a_traces():

    print("\n[LANGFUSE] Fetching Task 9A historical traces...")

    response = langfuse.api.observations.get_many(
        fields="core,basic,io",
        limit=500
    )

    observations = response.data

    print(
        "Total observations fetched:",
        len(observations)
    )

    traces = defaultdict(list)

    for observation in observations:

        trace_id = getattr(
            observation,
            "trace_id",
            None
        )

        if trace_id:
            traces[trace_id].append(observation)

    candidates = []

    for trace_id, items in traces.items():

        task9a_items = [
            item
            for item in items
            if str(
                getattr(item, "name", "")
            ).startswith("task9a_")
        ]

        if not task9a_items:
            continue

        latest_item = max(
            task9a_items,
            key=lambda item: str(
                getattr(
                    item,
                    "start_time",
                    getattr(
                        item,
                        "created_at",
                        ""
                    )
                )
            )
        )

        candidates.append(
            {
                "trace_id": trace_id,
                "observations": items,
                "latest_time": str(
                    getattr(
                        latest_item,
                        "start_time",
                        getattr(
                            latest_item,
                            "created_at",
                            ""
                        )
                    )
                )
            }
        )

    print(
        "Task 9A traces found:",
        len(candidates)
    )

    candidates.sort(
        key=lambda x: x["latest_time"],
        reverse=True
    )

    selected = candidates[:10]

    print(
        "Latest Task 9A traces selected:",
        len(selected)
    )

    return selected


# ============================================================
# SERIALIZE OBSERVATION
# ============================================================

def serialize_observation(observation):

    return {
        "name": getattr(
            observation,
            "name",
            ""
        ),

        "type": getattr(
            observation,
            "type",
            ""
        ),

        "input": getattr(
            observation,
            "input",
            None
        ),

        "output": getattr(
            observation,
            "output",
            None
        ),

        "status_message": getattr(
            observation,
            "status_message",
            None
        )
    }


# ============================================================
# LLM JUDGE
# ============================================================

def judge_error_recovery(
    trace,
    trace_number
):

    trace_data = {
        "trace_id": trace["trace_id"],

        "observations": [
            serialize_observation(item)
            for item in trace["observations"]
        ]
    }

    trace_text = json.dumps(
        trace_data,
        indent=2,
        default=str
    )

    prompt = f"""
You are an expert evaluator for an
Intelligent Employee Onboarding Agent.

You are evaluating historical agent trace #{trace_number}.

Evaluate ONLY ERROR RECOVERY.

Use ONLY observable evidence contained
inside the historical trace.

Evaluate these six areas:

1. Error detection
2. Error identification
3. Reasoning
4. Recovery attempt OR safe handling
5. Recovery result
6. Final outcome

SCORING RUBRIC:

5/5:
Excellent recovery.

The agent detects the failure, reasons correctly,
selects an appropriate recovery action, and
successfully recovers.

4/5:
Good error handling.

The agent correctly detects the failure and
performs appropriate safe handling or partial
recovery, but the recovery is incomplete,
limited, or lacks one important step.

3/5:
Acceptable safety handling.

The agent correctly recognizes that the failure
should not be automatically retried and safely
stops or escalates the operation, but there is
limited actual recovery.

2/5:
Weak handling.

The failure is detected but the response,
reasoning, or recovery strategy is inadequate.

1/5:
No meaningful error handling evidence.

The trace does not provide enough evidence
of meaningful error recovery.

IMPORTANT:

- Do NOT score based only on the trace name.
- Do NOT invent events.
- Do NOT assume recovery happened.
- Do NOT reward blind retries.
- Sensitive or unauthorized operations should
  NOT automatically be retried.
- Correct human escalation or safe termination
  should receive credit.
- A perfect score is NOT required when the agent
  correctly chooses not to retry an unsafe operation.

Return EXACTLY:

Score: X/5
Reason: <short explanation>

Historical Trace:
{trace_text}
"""

    print(
        "\n[LLM JUDGE] Evaluating trace..."
    )

    try:

        response = client.models.generate_content(
            model=JUDGE_MODEL,
            contents=prompt
        )

        result = response.text

        if not result:
            result = (
                "Score: 1/5\n"
                "Reason: No judge response."
            )

        return result

    except Exception as e:

        print("\n[LLM JUDGE ERROR]")
        print(str(e))

        return (
            "Score: 1/5\n"
            f"Reason: Judge execution failed: {str(e)}"
        )


# ============================================================
# EXTRACT SCORE
# ============================================================

def extract_score(result):

    for value in ["5", "4", "3", "2", "1"]:

        if f"Score: {value}/5" in result:
            return int(value)

    return None


# ============================================================
# RUN EVALUATION
# ============================================================

def run_evaluation():

    print("\n==========================================")
    print(" TASK 9A - ERROR RECOVERY EVALUATION")
    print("==========================================")

    traces = get_latest_task9a_traces()

    if len(traces) < 10:

        print(
            f"\nERROR: Only {len(traces)} "
            "Task 9A traces found."
        )

        print(
            "Task 9A requires 10 historical traces."
        )

        return

    print(
        "\nExactly 10 latest historical "
        "Task 9A traces selected."
    )

    results = []
    scores = []

    for index, trace in enumerate(
        traces,
        start=1
    ):

        print("\n------------------------------------------")
        print(
            f"TRACE {index}"
        )
        print("------------------------------------------")

        print(
            "Trace ID:",
            trace["trace_id"]
        )

        print(
            "Observation count:",
            len(trace["observations"])
        )

        judge_result = judge_error_recovery(
            trace,
            index
        )

        score = extract_score(
            judge_result
        )

        print("\nLLM Judge:")
        print(judge_result)

        if score is not None:
            scores.append(score)

        results.append(
            {
                "trace_number": index,
                "trace_id": trace["trace_id"],
                "score": score,
                "judge_result": judge_result
            }
        )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    print("\n==========================================")
    print(" FINAL ERROR RECOVERY EVALUATION")
    print("==========================================")

    if scores:

        average_score = (
            sum(scores) / len(scores)
        )

        percentage = (
            average_score / 5 * 100
        )

        print(
            "Historical traces evaluated:",
            len(scores)
        )

        print(
            "Scores:",
            scores
        )

        print(
            f"Average Error Recovery Score: "
            f"{average_score:.2f}/5"
        )

        print(
            f"Percentage: "
            f"{percentage:.2f}%"
        )

    else:

        average_score = 0
        percentage = 0

        print(
            "No valid scores extracted."
        )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    final_results = {

        "evaluation_type":
            "LLM-as-a-Judge",

        "metric":
            "Error Recovery",

        "scale":
            "1-5",

        "historical_traces_required":
            10,

        "historical_traces_evaluated":
            len(scores),

        "scores":
            scores,

        "average_score":
            average_score,

        "percentage":
            percentage,

        "trace_results":
            results
    }

    with open(
        "task9a_error_recovery_results.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            final_results,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\nResults saved to:"
        " task9a_error_recovery_results.json"
    )

    print(
        "\n[LANGFUSE] Flushing..."
    )

    langfuse.flush()

    print(
        "[LANGFUSE] Evaluation data flushed."
    )

    print("\n==========================================")
    print(" TASK 9A COMPLETE")
    print("==========================================")


if __name__ == "__main__":

    run_evaluation()