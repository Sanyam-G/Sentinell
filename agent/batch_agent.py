"""
Batch agent that processes multiple issues and creates separate PRs for each.
"""

import os
import subprocess
from agent_graph import build_agent_graph
from agent_state import AgentState
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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


def reset_to_main():
    """Reset repo to main branch and clean working directory."""
    try:
        subprocess.run(["git", "checkout", "main"], check=True, capture_output=True, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True, capture_output=True, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "clean", "-fd"], check=True, capture_output=True, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def close_existing_prs():
    """Close all existing open PRs created by the agent."""
    try:
        from pr_agent import PRAgent
        agent = PRAgent()
        repo = agent.github.get_repo(f"{agent.owner}/{agent.repo_name}")
        prs = repo.get_pulls(state='open')
        
        closed_count = 0
        for pr in prs:
            if pr.title.startswith("Fix:"):
                pr.edit(state='closed')
                print(f"  ✅ Closed PR: {pr.title} (#{pr.number})")
                closed_count += 1
        
        print(f"\n✅ Closed {closed_count} existing PR(s)" if closed_count > 0 else "\n✅ No existing PRs to close")
        return closed_count
    except Exception as e:
        print(f"⚠️  Could not close existing PRs: {e}")
        return 0


def get_attr(state, attr, default=None):
    """Safely get attribute from state (handles dict or object)."""
    if isinstance(state, dict):
        return state.get(attr, default)
    return getattr(state, attr, default)

def process_all_issues():
    """Process all detected issues and create separate PRs for each."""
    print("=" * 60)
    print("Batch Issue Processing")
    print("=" * 60)
    
    print("\n🧹 Cleaning up...")
    close_existing_prs()
    reset_to_main()
    
    print("\n🔍 Searching for issues in Pinecone...")
    issues = find_all_issues()
    print(f"Found {len(issues)} issues\n")
    
    if not issues:
        print("No issues found!")
        return []
    
    graph = build_agent_graph()
    results = []
    
    for i, issue in enumerate(issues, 1):
        print("\n" + "=" * 60)
        print(f"Issue {i}/{len(issues)}: {issue['text'][:100]}...")
        print("=" * 60)
        
        # Reset to clean state before each issue
        reset_to_main()
        
        initial_state = AgentState(input_text=issue['text'], input_type=issue['type'])
        
        try:
            final_state = graph.invoke(initial_state)
            
            error = get_attr(final_state, 'error')
            code_changes = get_attr(final_state, 'code_changes', {})
            pr_created = get_attr(final_state, 'pr_created', False)
            pr_url = get_attr(final_state, 'pr_url')
            
            if pr_created:
                results.append({'success': True, 'pr_url': pr_url})
                print(f"✅ PR created: {pr_url}")
            else:
                error_msg = error or "No code changes generated"
                results.append({'success': False, 'error': error_msg})
                print(f"❌ Failed: {error_msg}")
        
        except Exception as e:
            results.append({'success': False, 'error': str(e)})
            print(f"❌ Exception: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    successful = sum(1 for r in results if r['success'])
    print(f"✅ {successful}/{len(results)} PRs created")
    
    if successful > 0:
        print("\nCreated PRs:")
        for r in results:
            if r['success']:
                print(f"  - {r['pr_url']}")
    
    return results


if __name__ == "__main__":
    process_all_issues()
