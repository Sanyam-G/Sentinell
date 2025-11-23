"""
Batch agent that processes multiple issues and creates separate PRs for each.
"""

import os
from agent_graph import build_agent_graph
from agent_state import AgentState
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX", "test-rag-index"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def find_all_issues():
    """Query Pinecone to find all recent errors and issues."""
    # Query for error logs
    error_query = "ERROR AUDIT FAILURE CRITICAL mismatch transaction balance"
    response = openai_client.embeddings.create(
        input=error_query,
        model="text-embedding-3-large",
        dimensions=1024
    )
    query_embedding = response.data[0].embedding
    
    results = index.query(
        vector=query_embedding,
        top_k=50,  # Get more issues
        include_metadata=True,
        filter={"type": {"$in": ["log", "chat"]}}  # Only logs and Slack messages
    )
    
    issues = []
    for match in results.matches:
        text = match.metadata.get('text', '')
        item_type = match.metadata.get('type', '')
        
        # Check if it's an actual error/issue
        if any(keyword in text.upper() for keyword in ['ERROR', 'FAILURE', 'BUG', 'ISSUE', 'PROBLEM', 'MISMATCH', 'INCREASED', 'DECREASED']):
            issues.append({
                'text': text,
                'type': item_type,
                'id': match.id,
                'score': match.score,
                'timestamp': match.metadata.get('timestamp', '')
            })
    
    return issues


def close_existing_prs():
    """Close all existing open PRs created by the agent."""
    try:
        from pr_agent import PRAgent
        agent = PRAgent()
        
        repo = agent.github.get_repo(f"{agent.owner}/{agent.repo_name}")
        prs = repo.get_pulls(state='open')
        
        closed_count = 0
        for pr in prs:
            # Check if PR title starts with "Fix:" (our agent's PRs)
            if pr.title.startswith("Fix:"):
                pr.edit(state='closed')
                print(f"  ✅ Closed PR: {pr.title} (#{pr.number})")
                closed_count += 1
        
        if closed_count > 0:
            print(f"\n✅ Closed {closed_count} existing PR(s)")
        else:
            print("\n✅ No existing PRs to close")
        
        return closed_count
    except Exception as e:
        print(f"⚠️  Could not close existing PRs: {e}")
        return 0


def process_all_issues():
    """Process all detected issues and create separate PRs for each."""
    print("=" * 60)
    print("Batch Issue Processing")
    print("=" * 60)
    
    # Close existing PRs first
    print("\n🧹 Cleaning up existing PRs...")
    close_existing_prs()
    
    # Find all issues
    print("\n🔍 Searching for issues in Pinecone...")
    issues = find_all_issues()
    print(f"Found {len(issues)} issues\n")
    
    if not issues:
        print("No issues found!")
        return []
    
    # Build graph
    graph = build_agent_graph()
    
    # Process each issue separately - create one PR per issue
    results = []
    for i, issue in enumerate(issues, 1):
        print("\n" + "=" * 60)
        print(f"Processing Issue {i}/{len(issues)}")
        print("=" * 60)
        print(f"Type: {issue['type']}")
        print(f"Text: {issue['text'][:200]}...")
        print()
        
        # Initialize state
        initial_state = AgentState(
            input_text=issue['text'],
            input_type=issue['type']
        )
        
        try:
            # Run agent
            final_state = graph.invoke(initial_state)
            
            # Helper to safely access state attributes (LangGraph may return dict or object)
            def get_attr(state, attr, default=None):
                if isinstance(state, dict):
                    return state.get(attr, default)
                return getattr(state, attr, default)
            
            # Get state values
            status = get_attr(final_state, 'status', 'unknown')
            error = get_attr(final_state, 'error')
            detected_issue = get_attr(final_state, 'detected_issue')
            code_changes = get_attr(final_state, 'code_changes', {})
            pr_created = get_attr(final_state, 'pr_created', False)
            pr_url = get_attr(final_state, 'pr_url')
            pr_branch = get_attr(final_state, 'pr_branch')
            
            # Debug output
            print(f"Status: {status}")
            if error:
                print(f"Error: {error}")
            if detected_issue:
                print(f"Detected issue: {detected_issue[:100]}...")
            if code_changes:
                print(f"Code changes: {len(code_changes)} file(s)")
            
            # Check results
            if pr_created:
                results.append({
                    'issue': issue['text'][:100],
                    'success': True,
                    'pr_url': pr_url,
                    'branch': pr_branch
                })
                print(f"✅ PR created: {pr_url or 'N/A'}")
            else:
                # Get detailed error message
                if error:
                    error_msg = error
                elif status == "done" and not pr_created:
                    error_msg = f"Process completed but no PR created. Status: {status}"
                elif code_changes:
                    error_msg = f"Code changes made but PR creation failed. Status: {status}"
                else:
                    error_msg = f"No code changes or PR created. Status: {status}"
                
                results.append({
                    'issue': issue['text'][:100],
                    'success': False,
                    'error': error_msg
                })
                print(f"❌ Failed: {error_msg}")
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Exception processing issue: {e}")
            print(f"Traceback:\n{error_details}")
            results.append({
                'issue': issue['text'][:100],
                'success': False,
                'error': f"Exception: {str(e)}"
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    successful = sum(1 for r in results if r['success'])
    print(f"✅ Successful: {successful}/{len(results)} PRs created")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    
    if successful > 0:
        print("\nCreated PRs:")
        for r in results:
            if r['success']:
                print(f"  - {r['pr_url']}")
    
    return results


if __name__ == "__main__":
    process_all_issues()
