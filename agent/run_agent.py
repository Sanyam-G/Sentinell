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
    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Print results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    
    # Safely access attributes
    def get_attr(state, attr, default=None):
        if isinstance(state, dict):
            return state.get(attr, default)
        return getattr(state, attr, default)
    
    error = get_attr(final_state, 'error')
    if error:
        print(f"❌ Error: {error}")
        return
    
    detected_issue = get_attr(final_state, 'detected_issue')
    issue_confidence = get_attr(final_state, 'issue_confidence')
    root_cause = get_attr(final_state, 'root_cause')
    affected_files = get_attr(final_state, 'affected_files', [])
    code_changes = get_attr(final_state, 'code_changes', {})
    pr_created = get_attr(final_state, 'pr_created', False)
    pr_branch = get_attr(final_state, 'pr_branch')
    pr_url = get_attr(final_state, 'pr_url')
    status = get_attr(final_state, 'status', 'unknown')
    
    if detected_issue:
        print(f"✅ Issue detected: {detected_issue}")
        if issue_confidence:
            print(f"   Confidence: {issue_confidence}")
    
    if root_cause:
        print(f"\n🔍 Root cause: {root_cause}")
    
    if affected_files:
        print(f"\n📁 Files to fix: {', '.join(affected_files)}")
    
    if code_changes:
        print(f"\n✏️  Code changes made to {len(code_changes)} file(s)")
    
    if pr_created:
        print(f"\n🎉 Pull Request created!")
        if pr_branch:
            print(f"   Branch: {pr_branch}")
        if pr_url:
            print(f"   URL: {pr_url}")
    else:
        print(f"\n⚠️  PR not created: {error or 'Unknown error'}")
    
    print(f"\nStatus: {status}")


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

