"""
Basic test script to verify the AI SRE agent setup.
This doesn't require an API key - just tests the graph structure.
"""

from state import SREState
from graph import build_graph


def test_graph_structure():
    """Test that the graph builds correctly"""
    print("Testing graph structure...")
    graph = build_graph()
    print("✓ Graph built successfully")
    print(f"✓ Graph type: {type(graph)}")
    return graph


def test_state_initialization():
    """Test that the state initializes correctly"""
    print("\nTesting state initialization...")
    state = SREState()
    assert state.logs is None
    assert state.issue is None
    assert state.actions == []
    assert state.resolved is False
    print("✓ State initialized correctly")
    print(f"  - logs: {state.logs}")
    print(f"  - issue: {state.issue}")
    print(f"  - actions: {state.actions}")
    print(f"  - resolved: {state.resolved}")


if __name__ == "__main__":
    print("=== AI SRE Agent Basic Tests ===\n")
    test_state_initialization()
    test_graph_structure()
    print("\n✓ All basic tests passed!")
