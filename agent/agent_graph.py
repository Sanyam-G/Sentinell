"""
LangGraph structure for the code-fixing agent.
"""

from langgraph.graph import StateGraph, END
from agent_state import AgentState
from agent_nodes import (
    detect_issue,
    query_pinecone,
    analyze_code,
    make_code_changes,
    create_pr
)


def build_agent_graph():
    """
    Builds the LangGraph for the code-fixing agent.
    
    Flow:
    detect_issue → query_pinecone → analyze_code → make_code_changes → create_pr → END
    """
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("detect_issue", detect_issue)
    builder.add_node("query_pinecone", query_pinecone)
    builder.add_node("analyze_code", analyze_code)
    builder.add_node("make_code_changes", make_code_changes)
    builder.add_node("create_pr", create_pr)
    
    # Define flow
    builder.set_entry_point("detect_issue")
    builder.add_edge("detect_issue", "query_pinecone")
    builder.add_edge("query_pinecone", "analyze_code")
    builder.add_edge("analyze_code", "make_code_changes")
    builder.add_edge("make_code_changes", "create_pr")
    builder.add_edge("create_pr", END)
    
    return builder.compile()

