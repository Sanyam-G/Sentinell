"""
Test script to run the AI SRE agent with Claude.
This will execute the full LangGraph loop.
"""

from state import SREState
from graph import build_graph
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def test_agent():
    """Test the full agent loop"""
    print("=== AI SRE Agent Test ===\n")
    print("Building graph...")
    graph = build_graph()
    print("✓ Graph built successfully\n")

    print("Starting agent execution...")
    print("-" * 60)

    # Create initial state
    initial_state = SREState()

    # Run the graph and collect all events
    print("\n🔄 Running agent loop...\n")

    try:
        # Use the synchronous stream to see each step
        for i, event in enumerate(graph.stream(initial_state), 1):
            print(f"\n📍 Step {i}: {list(event.keys())[0]}")
            print("-" * 60)

            # Get the node name and state
            node_name = list(event.keys())[0]
            node_state = event[node_name]

            # Print state details (node_state is a dict)
            print(f"Logs: {node_state.get('logs', None)}")
            print(f"Issue: {node_state.get('issue', None)}")
            print(f"Actions: {node_state.get('actions', [])}")
            print(f"Resolved: {node_state.get('resolved', False)}")

            # Safety limit to prevent infinite loops
            if i > 10:
                print("\n⚠️  Stopping after 10 iterations (safety limit)")
                break

        print("\n" + "=" * 60)
        print("✅ Agent execution completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()


def test_single_invocation():
    """Test with a single invocation (waits for completion)"""
    print("=== AI SRE Agent Single Invocation Test ===\n")

    graph = build_graph()
    initial_state = SREState()

    print("Running agent (this may take a moment)...\n")

    try:
        # This will run until completion or max iterations
        final_state = graph.invoke(initial_state, {"recursion_limit": 10})

        print("\n=== Final State ===")
        # final_state is a dict, not a SREState object
        print(f"Logs: {final_state.get('logs', None)}")
        print(f"Issue: {final_state.get('issue', None)}")
        print(f"Actions taken: {final_state.get('actions', [])}")
        print(f"Resolved: {final_state.get('resolved', False)}")
        print(f"Total actions: {len(final_state.get('actions', []))}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stream":
        # Run with streaming output to see each step
        test_agent()
    else:
        # Run with single invocation
        print("Run with --stream to see each step, or run without args for final result only\n")
        test_single_invocation()
