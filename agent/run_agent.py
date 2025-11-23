"""
Main runner for the code-fixing agent.
Takes text input (Slack message or log) and processes it through the agent.
"""

import sys
from agent_graph import build_agent_graph
from agent_state import AgentState


def run_agent(input_text: str, input_type: str = "manual"):
    """
    Run the agent on input text.
    
    Args:
        input_text: The text to analyze (Slack message, log entry, etc.)
        input_type: Type of input ("slack", "log", or "manual")
    """
    print("=" * 60)
    print("Code-Fixing Agent v1")
    print("=" * 60)
    print(f"\nInput type: {input_type}")
    print(f"Input text:\n{input_text}\n")
    
    # Initialize state
    initial_state = AgentState(
        input_text=input_text,
        input_type=input_type
    )
    
    # Build and run graph
    graph = build_agent_graph()
    
    print("Running agent...\n")
    final_state = graph.invoke(initial_state)
    
    # Print results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    
    if final_state.error:
        print(f"❌ Error: {final_state.error}")
        return
    
    if final_state.detected_issue:
        print(f"✅ Issue detected: {final_state.detected_issue}")
        print(f"   Confidence: {final_state.issue_confidence}")
    
    if final_state.root_cause:
        print(f"\n🔍 Root cause: {final_state.root_cause}")
    
    if final_state.affected_files:
        print(f"\n📁 Files to fix: {', '.join(final_state.affected_files)}")
    
    if final_state.code_changes:
        print(f"\n✏️  Code changes made to {len(final_state.code_changes)} file(s)")
    
    if final_state.pr_created:
        print(f"\n🎉 Pull Request created!")
        print(f"   Branch: {final_state.pr_branch}")
        print(f"   URL: {final_state.pr_url}")
    else:
        print(f"\n⚠️  PR not created: {final_state.error or 'Unknown error'}")
    
    print(f"\nStatus: {final_state.status}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_agent.py <input_text> [input_type]")
        print("\nExample:")
        print('  python run_agent.py "User claims they withdrew $500 but balance increased" slack')
        print('  python run_agent.py "[ERROR] AUDIT FAILURE: Transaction History mismatch" log')
        sys.exit(1)
    
    input_text = sys.argv[1]
    input_type = sys.argv[2] if len(sys.argv) > 2 else "manual"
    
    run_agent(input_text, input_type)


if __name__ == "__main__":
    main()

