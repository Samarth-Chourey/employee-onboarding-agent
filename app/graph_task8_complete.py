import asyncio

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.types import interrupt
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

from langfuse.langchain import CallbackHandler

from app.state import OnboardingState
from app.mcp_client import discover_tools, call_tool
from app.hooks import execute_with_hooks
from app.compaction import compact_messages

from app.jsonrpc import (
    parse_jsonrpc_response,
    create_tool_response
)

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# LANGFUSE
# ============================================================

print("\n[LANGFUSE] Initializing telemetry...")

langfuse_handler = CallbackHandler()

print(
    "[LANGFUSE] Callback handler initialized."
)


# ============================================================
# GEMINI
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0,
    timeout=30,
)


# ============================================================
# TASK 2
# REASONING NODE
# ============================================================

def reasoning_node(state: OnboardingState):

    print("\n[REASONING] Discovering MCP tools...")

    mcp_tools = asyncio.run(
        discover_tools()
    )

    tools_description = ""

    for tool in mcp_tools:

        tools_description += (
            f"- {tool.name}: {tool.description}\n"
            f"  Parameters: {tool.input_schema}\n"
        )

    print(
        "[REASONING] MCP tools discovered:"
    )

    print(tools_description)


    # ========================================================
    # SYSTEM PROMPT
    # ========================================================

    system_prompt = """
You are the reasoning engine of an
Employee Onboarding Agent.

Your responsibility is ONLY to decide
what the agent should do next.

You MUST NOT execute tools yourself.

You have access to dynamically discovered
MCP tools.

When a tool is required, return a valid
JSON-RPC 2.0 tools/call request.

When no tool is required, return a concise
final text response.

Rules:

1. Analyze the current employee state.
2. Consider the current onboarding task.
3. Select the most appropriate available tool.
4. Use only tools provided in the MCP tool list.
5. Do not invent tool names.
6. Do not execute tools.
7. Return JSON-RPC 2.0 for tool calls.
8. Keep the decision rationale concise.
"""


    # ========================================================
    # CURRENT STATE
    # ========================================================

    human_prompt = f"""
Current employee state:

Employee ID:
{state["employee_id"]}

Employee Name:
{state["employee_name"]}

Role:
{state["role"]}

Department:
{state["department"]}

Current Task:
{state["current_task"]}

Completed Tasks:
{state["completed_tasks"]}

Pending Tasks:
{state["pending_tasks"]}

Available MCP tools:

{tools_description}

If a tool is required, return ONLY JSON
in this format:

{{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {{
        "name": "tool_name",
        "arguments": {{
            "employee_id": "{state["employee_id"]}"
        }}
    }}
}}

If no tool is required, return ONLY
the final text response.

Do not use markdown.
Do not add extra text around JSON.
"""


    # ========================================================
    # CALL GEMINI
    # ========================================================

    print(
        "[REASONING] Sending system prompt + "
        "state to Gemini..."
    )

    response = llm.invoke(
        [
            SystemMessage(
                content=system_prompt
            ),
            HumanMessage(
                content=human_prompt
            )
        ]
    )

    print(
        "[REASONING] Gemini response received."
    )


    response_text = response.content

    if isinstance(response_text, list):
        response_text = response_text[0]["text"]

    response_text = response_text.strip()


    # ========================================================
    # JSON-RPC TOOL REQUEST
    # ========================================================

    if response_text.startswith("{"):

        try:

            jsonrpc_request = (
                parse_jsonrpc_response(
                    response_text
                )
            )

            tool_name = (
                jsonrpc_request[
                    "params"
                ]["name"]
            )


            # ------------------------------------------------
            # DECISION RATIONALE
            # ------------------------------------------------

            decision_reason = (
                f"Gemini selected the "
                f"{tool_name} tool for the "
                f"current onboarding task."
            )


            if tool_name == "aws_access":

                decision_reason = (
                    "Gemini selected AWS access "
                    "because it is required for "
                    "the current onboarding task. "
                    "Because AWS access is a "
                    "high-risk action, the request "
                    "must pass through human "
                    "approval before execution."
                )


            print(
                "\n[REASONING] JSON-RPC request:"
            )

            print(jsonrpc_request)


            print(
                "[REASONING] Decision rationale:"
            )

            print(decision_reason)


            # ------------------------------------------------
            # Add request to messages
            # ------------------------------------------------

            new_message = {
                "role": "assistant",
                "type": "jsonrpc_tool_request",
                "content": jsonrpc_request
            }


            return {

                "current_task": tool_name,

                "tool_result": "",

                "final_response": "",

                "decision_reason": (
                    decision_reason
                ),

                "approval_required": (
                    tool_name == "aws_access"
                ),

                "approval_status": "",

                "messages": (
                    state["messages"]
                    + [new_message]
                )
            }


        except Exception as error:

            print(
                "\n[REASONING] "
                "Invalid JSON-RPC:"
            )

            print(error)


            return {

                "errors": (
                    state["errors"]
                    + [str(error)]
                ),

                "decision_reason": (
                    "Gemini returned an "
                    "invalid JSON-RPC request."
                ),

                "final_response": (
                    "Gemini returned an "
                    "invalid JSON-RPC request."
                )
            }


    # ========================================================
    # FINAL TEXT RESPONSE
    # ========================================================

    print(
        "\n[REASONING] "
        "Gemini returned final text."
    )


    new_message = {

        "role": "assistant",

        "type": "final_text",

        "content": response_text
    }


    return {

        "decision_reason": (
            "Gemini determined that no "
            "tool execution was required."
        ),

        "final_response": response_text,

        "messages": (
            state["messages"]
            + [new_message]
        )
    }


# ============================================================
# TASK 6
# CONDITIONAL ROUTER
# ============================================================

def route_after_reasoning(
    state: OnboardingState
):

    tool_name = state["current_task"]


    print(
        "\n[ROUTER] Checking whether "
        "approval is required..."
    )


    # --------------------------------------------------------
    # HIGH-RISK TOOL
    # --------------------------------------------------------

    if tool_name == "aws_access":

        print(
            "[ROUTER] High-risk action detected."
        )

        print(
            "[ROUTER] Routing to HITL approval."
        )

        return "approval"


    # --------------------------------------------------------
    # NORMAL TOOL
    # --------------------------------------------------------

    print(
        "[ROUTER] Normal action detected."
    )

    print(
        "[ROUTER] Routing directly to "
        "tool execution."
    )

    return "tool_execution"


# ============================================================
# TASK 6
# HUMAN-IN-THE-LOOP APPROVAL
# ============================================================

def approval_node(
    state: OnboardingState
):

    print(
        "\n[HITL] AWS access requires "
        "human approval."
    )


    approval = interrupt({

        "type": "aws_access_approval",

        "employee_id": state["employee_id"],

        "employee_name": state["employee_name"],

        "tool": "aws_access",

        "message": (
            "AWS access requires "
            "human approval."
        )
    })


    # ========================================================
    # REJECT
    # ========================================================

    if approval == "reject":

        print(
            "\n[HITL] AWS access rejected."
        )


        return {

            "approval_required": True,

            "approval_status": "rejected",

            "final_response": (
                "AWS access was rejected "
                "by the human approver."
            ),

            "tool_result": (
                "Human rejected AWS access."
            )
        }


    # ========================================================
    # APPROVE
    # ========================================================

    print(
        "\n[HITL] AWS access approved."
    )


    return {

        "approval_required": True,

        "approval_status": "approved"
    }


# ============================================================
# TASK 3
# TOOL EXECUTION
# ============================================================

def tool_execution_node(
    state: OnboardingState
):

    # --------------------------------------------------------
    # REJECTED REQUEST
    # --------------------------------------------------------

    if state["approval_status"] == "rejected":

        print(
            "\n[TOOL EXECUTION] "
            "Skipped because approval "
            "was rejected."
        )


        return {

            "tool_result": (
                "Tool execution skipped."
            ),

            "final_response": (
                "AWS access was rejected "
                "by the human approver."
            )
        }


    print(
        "\n[TOOL EXECUTION] "
        "Processing JSON-RPC request..."
    )


    # ========================================================
    # FIND JSON-RPC REQUEST
    # ========================================================

    rpc_request = None


    for message in reversed(
        state["messages"]
    ):

        if (
            message.get("type")
            == "jsonrpc_tool_request"
        ):

            rpc_request = message["content"]

            break


    if rpc_request is None:

        return {

            "errors": (
                state["errors"]
                + [
                    "No JSON-RPC "
                    "tool request found."
                ]
            ),

            "final_response": (
                "No tool request was found."
            )
        }


    tool_name = (
        rpc_request[
            "params"
        ]["name"]
    )


    arguments = (
        rpc_request[
            "params"
        ]["arguments"]
    )


    request_id = rpc_request["id"]


    print(
        "\n[JSON-RPC] Method:",
        rpc_request["method"]
    )

    print(
        "[JSON-RPC] Tool:",
        tool_name
    )

    print(
        "[JSON-RPC] Arguments:",
        arguments
    )


    # ========================================================
    # LIFECYCLE HOOKS + MCP
    # ========================================================

    print(
        "\n[HOOKS] Executing tool..."
    )


    tool_result = asyncio.run(
        execute_with_hooks(
            tool_name,
            arguments,
            call_tool
        )
    )


    # ========================================================
    # SELF-CORRECTION
    # ========================================================

    if not tool_result["success"]:

        print(
            "\n[SELF-CORRECTION]"
        )

        print(
            "Tool failed:"
        )

        print(
            tool_result["error"]
        )


        correction_prompt = f"""
The previous JSON-RPC tool request failed.

Employee ID:
{state["employee_id"]}

Previous JSON-RPC request:
{rpc_request}

Error:
{tool_result["error"]}

Correct the request.

Return ONLY a valid JSON-RPC 2.0 request.

Format:

{{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {{
        "name": "correct_tool_name",
        "arguments": {{
            "employee_id": "{state["employee_id"]}"
        }}
    }}
}}
"""


        print(
            "[SELF-CORRECTION] "
            "Asking Gemini to correct "
            "the request..."
        )


        correction_response = llm.invoke(
            correction_prompt
        )


        corrected_request = (
            parse_jsonrpc_response(
                correction_response.content
            )
        )


        print(
            "[SELF-CORRECTION] "
            "Corrected JSON-RPC request:"
        )

        print(corrected_request)


        tool_name = (
            corrected_request[
                "params"
            ]["name"]
        )


        arguments = (
            corrected_request[
                "params"
            ]["arguments"]
        )


        request_id = (
            corrected_request["id"]
        )


        tool_result = asyncio.run(
            execute_with_hooks(
                tool_name,
                arguments,
                call_tool
            )
        )


    # ========================================================
    # JSON-RPC RESPONSE
    # ========================================================

    rpc_response = create_tool_response(
        request_id,
        tool_result
    )


    print(
        "\n[JSON-RPC] Tool response:"
    )

    print(rpc_response)


    # ========================================================
    # APPEND TOOL RESULT TO MESSAGE STATE
    # ========================================================

    result_message = {

        "role": "tool",

        "type": "jsonrpc_tool_response",

        "content": rpc_response
    }


    return {

        "tool_result": str(
            tool_result
        ),

        "completed_tasks": (
            state["completed_tasks"]
            + [state["current_task"]]
        ),

        "messages": (
            state["messages"]
            + [result_message]
        )
    }


# ============================================================
# TASK 7
# CONTEXT COMPACTION
# ============================================================

def compaction_node(
    state: OnboardingState
):

    print(
        "\n[COMPACTION NODE] "
        "Checking message count..."
    )


    messages = state["messages"]


    print(
        "[COMPACTION NODE] Current messages:",
        len(messages)
    )


    if len(messages) <= 10:

        print(
            "[COMPACTION NODE] "
            "No compaction required."
        )

        return {}


    compacted_messages = compact_messages(
        messages
    )


    return {

        "messages": compacted_messages

    }


# ============================================================
# LANGGRAPH BUILDER
# ============================================================

builder = StateGraph(
    OnboardingState
)


# ============================================================
# NODES
# ============================================================

builder.add_node(
    "reasoning",
    reasoning_node
)


builder.add_node(
    "approval",
    approval_node
)


builder.add_node(
    "tool_execution",
    tool_execution_node
)


builder.add_node(
    "compaction",
    compaction_node
)


# ============================================================
# START
# ============================================================

builder.add_edge(
    START,
    "reasoning"
)


# ============================================================
# CONDITIONAL EDGE
# ============================================================

builder.add_conditional_edges(

    "reasoning",

    route_after_reasoning,

    {

        "approval":
            "approval",

        "tool_execution":
            "tool_execution"
    }
)


# ============================================================
# APPROVAL → TOOL EXECUTION
# ============================================================

builder.add_edge(
    "approval",
    "tool_execution"
)


# ============================================================
# TOOL EXECUTION → COMPACTION
# ============================================================

builder.add_edge(
    "tool_execution",
    "compaction"
)


# ============================================================
# COMPACTION → END
# ============================================================

builder.add_edge(
    "compaction",
    END
)


# ============================================================
# TASK 7
# SQLITE CHECKPOINT
# ============================================================

checkpointer_context = (
    SqliteSaver.from_conn_string(
        "checkpoints.db"
    )
)


checkpointer = (
    checkpointer_context.__enter__()
)


# ============================================================
# COMPILE GRAPH
# ============================================================

compiled_graph = builder.compile(
    checkpointer=checkpointer
)


# ============================================================
# TASK 8
# LANGFUSE TELEMETRY
# ============================================================

graph = compiled_graph.with_config({

    "callbacks": [
        langfuse_handler
    ],

    "run_name":
        "employee-onboarding-agent"

})


print(
    "[LANGFUSE] LangGraph telemetry enabled."
)