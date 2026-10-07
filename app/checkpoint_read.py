from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver


class TestState(TypedDict):
    message: str
    step: int


def test_node(state: TestState):
    return state


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

    state = graph.get_state(config)

    print("\n========== CHECKPOINT RECOVERY ==========")

    if state.values:

        print("PASS: Previous state recovered.")
        print("Thread ID:", "task7-persistence-test")
        print("Recovered message:")
        print(state.values["message"])
        print("Recovered step:")
        print(state.values["step"])

    else:

        print("FAIL: No checkpoint found.")

    print("=========================================")