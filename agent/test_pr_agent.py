"""
Test script for the PR Agent.

This script demonstrates how to use the PR agent to create pull requests.
"""

import os
import sys
from pr_agent import PRAgent


def test_pr_creation():
    """Test creating a PR with changes."""
    print("=" * 60)
    print("Test 1: Creating PR with new branch and changes")
    print("=" * 60)
    
    # Check if we have a GitHub token
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN not set. Please set it first:")
        print("   export GITHUB_TOKEN=your_token_here")
        return False
    
    try:
        agent = PRAgent()
        
        # Create a test file to demonstrate changes
        test_file = "agent/test_file.txt"
        with open(test_file, "w") as f:
            f.write("This is a test file created by the PR agent.\n")
            f.write("This demonstrates automated PR creation.\n")
        
        print(f"✅ Created test file: {test_file}")
        
        instructions = """
        This is a test pull request created by the PR agent.
        
        Changes:
        - Added a test file to demonstrate PR creation
        - This is an automated test
        
        This PR can be safely closed after testing.
        """
        
        result = agent.create_pr(
            instructions=instructions,
            title="Test PR: Automated PR Agent Demo",
            description=instructions
        )
        
        if result["success"]:
            print(f"\n✅ PR created successfully!")
            print(f"   PR URL: {result['pr_url']}")
            print(f"   Branch: {result['branch_name']}")
            return True
        else:
            print(f"\n❌ Failed to create PR: {result.get('error')}")
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_pr_from_existing_branch():
    """Test creating a PR from an existing branch."""
    print("\n" + "=" * 60)
    print("Test 2: Creating PR from existing branch")
    print("=" * 60)
    
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN not set.")
        return False
    
    try:
        agent = PRAgent()
        
        # This test assumes you have a branch already created
        # You can modify this to use an actual branch name
        branch_name = input("Enter an existing branch name to test with (or press Enter to skip): ").strip()
        
        if not branch_name:
            print("⏭ Skipping test (no branch name provided)")
            return True
        
        instructions = """
        This PR was created from an existing branch.
        
        This demonstrates the use case where another agent or process
        has already made changes and pushed them to a branch, and this
        agent just creates the PR.
        """
        
        result = agent.create_pr_from_existing_branch(
            branch_name=branch_name,
            instructions=instructions,
            title="Test PR: From Existing Branch"
        )
        
        if result["success"]:
            print(f"\n✅ PR created successfully!")
            print(f"   PR URL: {result['pr_url']}")
            if "message" in result:
                print(f"   Note: {result['message']}")
            return True
        else:
            print(f"\n❌ Failed to create PR: {result.get('error')}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_agent_initialization():
    """Test agent initialization."""
    print("\n" + "=" * 60)
    print("Test 3: Agent Initialization")
    print("=" * 60)
    
    # Test without token (should fail)
    original_token = os.environ.get("GITHUB_TOKEN")
    if "GITHUB_TOKEN" in os.environ:
        del os.environ["GITHUB_TOKEN"]
    
    try:
        agent = PRAgent()
        print("❌ Should have failed without token")
        return False
    except ValueError as e:
        print(f"✅ Correctly failed without token: {e}")
    
    # Restore token
    if original_token:
        os.environ["GITHUB_TOKEN"] = original_token
    
    # Test with token
    if not os.getenv("GITHUB_TOKEN"):
        print("⏭ Skipping token test (GITHUB_TOKEN not set)")
        return True
    
    try:
        agent = PRAgent()
        print(f"✅ Agent initialized successfully")
        print(f"   Repository: {agent.owner}/{agent.repo_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PR Agent Test Suite")
    print("=" * 60)
    print("\nMake sure you have:")
    print("1. Set GITHUB_TOKEN environment variable")
    print("2. Made sure you're in the repository root")
    print("3. Have push access to the repository")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    results = []
    
    # Test initialization
    results.append(("Initialization", test_agent_initialization()))
    
    # Test PR creation (only if token is set)
    if os.getenv("GITHUB_TOKEN"):
        results.append(("PR Creation", test_pr_creation()))
        # Uncomment to test existing branch (requires manual input)
        # results.append(("PR from Existing Branch", test_pr_from_existing_branch()))
    else:
        print("\n⚠️  Skipping PR creation tests (GITHUB_TOKEN not set)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed.")


if __name__ == "__main__":
    main()

