from langgraph.graph import StateGraph, END
from state import SREState
from nodes.observe import observe
from nodes.reason import reason
from nodes.act import act
from nodes.evaluate import evaluate


def build_graph():
    """
    Builds the LangGraph state machine for the AI SRE agent.

    Flow:
    observe → reason → act → evaluate
                 ↑         |
                 └─────────┘   (loop until resolved)
    """
    builder = StateGraph(SREState)

    # Add nodes
    builder.add_node("observe", observe)
    builder.add_node("reason", reason)
    builder.add_node("act", act)
    builder.add_node("evaluate", evaluate)

    # Define linear flow
    builder.add_edge("observe", "reason")
    builder.add_edge("reason", "act")
    builder.add_edge("act", "evaluate")

    # Loop condition: if not resolved, go back to observe
    builder.add_conditional_edges(
        "evaluate",
        lambda s: s.resolved,
        {True: END, False: "observe"}
    )

    # Set entry point
    builder.set_entry_point("observe")

    return builder.compile()
