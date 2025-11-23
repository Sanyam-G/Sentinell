"""
Comprehensive test file for the code-fixing agent.

Usage:
    python test.py                    # Test with a single issue (interactive)
    python test.py --batch            # Test batch processing
    python test.py --issue "your issue text"  # Test with specific issue
    python test.py --check-env        # Check environment and dependencies
"""

import os
import sys
import argparse

# Check Python version (requires 3.8+)
if sys.version_info < (3, 8):
    print("❌ Python 3.8 or higher is required")
    print(f"   Current version: {sys.version}")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()


def test_single_issue(issue_text: str = None, input_type: str = "manual"):
    """Test the agent with a single issue."""
    from run_agent import run_agent
    
    if not issue_text:
        print("\n" + "=" * 60)
        print("Single Issue Test")
        print("=" * 60)
        print("\nEnter an issue description (or press Enter to use default example):")
        user_input = input().strip()
        
        if not user_input:
            issue_text = "User reports that their balance increased when they made a withdrawal. This seems like a sign error in the transaction processing."
            print(f"\nUsing example issue:\n{issue_text}\n")
        else:
            issue_text = user_input
    
    print("\n" + "=" * 60)
    print("Running Agent...")
    print("=" * 60)
    
    try:
        result = run_agent(issue_text, input_type)
        
        if result and hasattr(result, 'pr_created') and result.pr_created:
            print("\n" + "=" * 60)
            print("✅ SUCCESS - PR Created!")
            print("=" * 60)
            print(f"PR URL: {result.pr_url}")
            print(f"Branch: {result.pr_branch}")
            return True
        else:
            error = getattr(result, 'error', 'Unknown error') if result else 'No result returned'
            print("\n" + "=" * 60)
            print("❌ FAILED")
            print("=" * 60)
            print(f"Error: {error}")
            return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_processing():
    """Test batch processing of multiple issues."""
    from batch_agent import process_all_issues
    
    print("\n" + "=" * 60)
    print("Batch Processing Test")
    print("=" * 60)
    print("\nThis will:")
    print("1. Query Pinecone for all issues")
    print("2. Cluster similar issues together")
    print("3. Process each unique issue cluster")
    print("4. Create PRs for fixes")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return False
    
    try:
        results = process_all_issues()
        
        if results:
            successful = sum(1 for r in results if r.get('success', False))
            print(f"\n✅ Processed {successful}/{len(results)} issue clusters successfully")
            return successful > 0
        else:
            print("\n⚠️  No issues found or processed")
            return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pr_agent():
    """Test PR agent functionality (optional)."""
    if not os.getenv("GITHUB_TOKEN"):
        print("\n⚠️  GITHUB_TOKEN not set. Skipping PR agent test.")
        print("   Set GITHUB_TOKEN to test PR creation functionality.")
        return False
    
    print("\n" + "=" * 60)
    print("PR Agent Test")
    print("=" * 60)
    
    try:
        from pr_agent import PRAgent
    except ImportError as e:
        print(f"⚠️  PR Agent dependencies not installed: {e}")
        print("   Install with: pip install PyGithub")
        print("   Or activate the virtual environment: source venv/bin/activate")
        return False
    
    try:
        agent = PRAgent()
        print(f"✅ PR Agent initialized")
        print(f"   Repository: {agent.owner}/{agent.repo_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize PR agent: {e}")
        return False


def check_environment():
    """Check if required environment variables are set."""
    print("\n" + "=" * 60)
    print("Environment Check")
    print("=" * 60)
    
    required_vars = {
        "PINECONE_API_KEY": "Pinecone API key for vector database",
        "OPENAI_API_KEY": "OpenAI API key for embeddings",
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude LLM"
    }
    
    optional_vars = {
        "GITHUB_TOKEN": "GitHub token for PR creation (optional)",
        "PINECONE_INDEX": "Pinecone index name (defaults to 'test-rag-index')",
        "ANTHROPIC_MODEL": "Anthropic model name (defaults to 'claude-sonnet-4-20250514')",
        "OPENAI_EMBEDDING_MODEL": "OpenAI embedding model (defaults to 'text-embedding-3-large')"
    }
    
    all_good = True
    
    print("\nRequired variables:")
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing - {desc}")
            all_good = False
    
    print("\nOptional variables:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive tokens
            if "TOKEN" in var or "KEY" in var:
                masked = value[:10] + "..." if len(value) > 10 else "***"
                print(f"  ✅ {var}: {masked}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️  {var}: Not set (using default) - {desc}")
    
    # Show Python version
    print(f"\nPython version: {sys.version.split()[0]}")
    
    # Check Python dependencies
    print("\nPython dependencies:")
    try:
        import langchain_anthropic
        print("  ✅ langchain-anthropic: Installed")
    except ImportError:
        print("  ❌ langchain-anthropic: Missing - pip install langchain-anthropic")
        all_good = False
    
    try:
        import pinecone
        print("  ✅ pinecone-client: Installed")
    except ImportError:
        print("  ❌ pinecone-client: Missing - pip install pinecone-client")
        all_good = False
    
    try:
        import openai
        print("  ✅ openai: Installed")
    except ImportError:
        print("  ❌ openai: Missing - pip install openai")
        all_good = False
    
    try:
        from github import Github
        print("  ✅ PyGithub: Installed")
    except ImportError:
        print("  ⚠️  PyGithub: Missing (optional) - pip install PyGithub")
        print("     Note: Required for PR creation functionality")
    
    # Check if venv exists
    venv_path = os.path.join(os.path.dirname(__file__), "venv")
    if os.path.exists(venv_path):
        print(f"\n💡 Virtual environment found at: {venv_path}")
        print("   Activate it with: source venv/bin/activate")
        print("   Or install dependencies: pip install -r requirements.txt")
    
    return all_good


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test the code-fixing agent")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run batch processing test"
    )
    parser.add_argument(
        "--issue",
        type=str,
        help="Test with a specific issue text"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="manual",
        choices=["manual", "slack", "log"],
        help="Input type for the issue (default: manual)"
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Only check environment variables"
    )
    parser.add_argument(
        "--pr-agent",
        action="store_true",
        help="Test PR agent initialization"
    )
    
    args = parser.parse_args()
    
    # Check environment first
    env_ok = check_environment()
    
    if args.check_env:
        sys.exit(0 if env_ok else 1)
    
    if not env_ok:
        print("\n⚠️  Some required environment variables are missing.")
        print("   Please set them before running tests.")
        response = input("\nContinue anyway? (y/N): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    
    results = []
    
    # Test PR agent if requested
    if args.pr_agent:
        results.append(("PR Agent", test_pr_agent()))
    
    # Run tests based on arguments
    if args.batch:
        results.append(("Batch Processing", test_batch_processing()))
    elif args.issue:
        results.append(("Single Issue", test_single_issue(args.issue, args.type)))
    else:
        # Interactive mode
        print("\n" + "=" * 60)
        print("Code-Fixing Agent Test Suite")
        print("=" * 60)
        print("\nSelect test mode:")
        print("1. Single issue test (interactive)")
        print("2. Batch processing test")
        print("3. PR agent test")
        print("4. Run all tests")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            results.append(("Single Issue", test_single_issue()))
        elif choice == "2":
            results.append(("Batch Processing", test_batch_processing()))
        elif choice == "3":
            results.append(("PR Agent", test_pr_agent()))
        elif choice == "4":
            results.append(("PR Agent", test_pr_agent()))
            results.append(("Single Issue", test_single_issue()))
            results.append(("Batch Processing", test_batch_processing()))
        else:
            print("Invalid choice. Running single issue test...")
            results.append(("Single Issue", test_single_issue()))
    
    # Summary
    if results:
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

