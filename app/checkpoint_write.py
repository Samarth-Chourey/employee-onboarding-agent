from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver


class TestState(TypedDict):
    message: str
    step: int


def test_node(state: TestState):
    return {
        "message": "Checkpoint saved successfully",
        "step": state["step"] + 1
    }


builder = StateGraph(TestState)

builder.add_node(
    "test",
    test_node
)

builder.add_edge(
    START,
    "test"
)

builder.add_edge(
    "test",
    END
)


with SqliteSaver.from_conn_string(
    "checkpoints.db"
) as checkpointer:

    graph = builder.compile(
        checkpointer=checkpointer
    )

    config = {
        "configurable": {
            "thread_id": "task7-persistence-test"
        }
    }

    result = graph.invoke(
        {
            "message": "Initial state",
            "step": 0
        },
        config
    )

    print("\n========== CHECKPOINT WRITE ==========")
    print("State saved to SQLite.")
    print("Thread ID:", "task7-persistence-test")
    print("Message:", result["message"])
    print("Step:", result["step"])
    print("======================================")