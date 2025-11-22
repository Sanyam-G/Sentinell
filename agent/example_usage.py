"""
Simple example of using the PR Agent.

This script demonstrates a basic use case.
"""

import os
from pr_agent import PRAgent


def main():
    """Example: Create a PR with some changes."""
    
    # Check for token
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ Please set GITHUB_TOKEN environment variable")
        print("   export GITHUB_TOKEN=your_token_here")
        return
    
    # Initialize agent
    print("Initializing PR Agent...")
    agent = PRAgent()
    print(f"✅ Connected to repository: {agent.owner}/{agent.repo_name}\n")
    
    # Example: Create a simple test file
    test_content = """# Test File

This file was created by the PR Agent example script.

You can safely delete this file after testing.
"""
    
    test_file_path = "example_test_file.md"
    print(f"Creating test file: {test_file_path}")
    with open(test_file_path, "w") as f:
        f.write(test_content)
    print("✅ Test file created\n")
    
    # Create PR
    instructions = """
    Example PR created by PR Agent
    
    This demonstrates the PR agent functionality.
    The agent has created a test file and is now creating a PR for it.
    
    This is a test PR and can be safely closed after review.
    """
    
    print("Creating pull request...")
    result = agent.create_pr(
        instructions=instructions,
        title="Example: PR Agent Test",
        description=instructions
    )
    
    if result["success"]:
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"PR Number: #{result['pr_number']}")
        print(f"PR Title: {result['pr_title']}")
        print(f"PR URL: {result['pr_url']}")
        print(f"Branch: {result['branch_name']} → {result['base_branch']}")
        print("\nYou can now:")
        print("1. Review the PR on GitHub")
        print("2. Merge it if you want")
        print("3. Close it if it was just a test")
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print(f"Error: {result.get('error', 'Unknown error')}")
        if "suggestion" in result:
            print(f"Suggestion: {result['suggestion']}")


if __name__ == "__main__":
    main()

