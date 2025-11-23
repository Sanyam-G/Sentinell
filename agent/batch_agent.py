"""
Batch agent that processes multiple issues and creates PRs for each.
"""

import os
import numpy as np
from typing import List, Dict, Any
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
        top_k=20,
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


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def cluster_issues(issues: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Cluster similar issues together using embeddings.
    
    Args:
        issues: List of issue dictionaries with 'text' field
        similarity_threshold: Minimum cosine similarity to consider issues as duplicates (0.0-1.0)
    
    Returns:
        List of clustered issues, where each cluster has:
        - 'representative': The main issue to process
        - 'similar_issues': List of similar/duplicate issues
        - 'cluster_size': Number of issues in this cluster
    """
    if not issues:
        return []
    
    print(f"\n🔗 Clustering {len(issues)} issues (similarity threshold: {similarity_threshold})...")
    
    # Create embeddings for all issues
    issue_texts = [issue['text'] for issue in issues]
    embeddings_response = openai_client.embeddings.create(
        input=issue_texts,
        model="text-embedding-3-large",
        dimensions=1024
    )
    embeddings = [np.array(emb.embedding) for emb in embeddings_response.data]
    
    # Assign embeddings to issues
    for i, issue in enumerate(issues):
        issue['embedding'] = embeddings[i]
    
    # Cluster issues using similarity
    clusters = []
    processed_indices = set()
    
    for i, issue in enumerate(issues):
        if i in processed_indices:
            continue
        
        # Start a new cluster with this issue
        cluster = {
            'representative': issue,
            'similar_issues': [],
            'cluster_size': 1
        }
        processed_indices.add(i)
        
        # Find all similar issues
        for j, other_issue in enumerate(issues[i+1:], start=i+1):
            if j in processed_indices:
                continue
            
            similarity = cosine_similarity(issue['embedding'], other_issue['embedding'])
            
            if similarity >= similarity_threshold:
                cluster['similar_issues'].append(other_issue)
                cluster['cluster_size'] += 1
                processed_indices.add(j)
        
        clusters.append(cluster)
    
    print(f"✅ Clustered into {len(clusters)} unique issue groups")
    for idx, cluster in enumerate(clusters, 1):
        if cluster['cluster_size'] > 1:
            print(f"   Cluster {idx}: {cluster['cluster_size']} similar issues")
            print(f"      Representative: {cluster['representative']['text'][:100]}...")
    
    return clusters


def process_all_issues():
    """Process all detected issues and create PRs for each."""
    print("=" * 60)
    print("Batch Issue Processing")
    print("=" * 60)
    
    # Find all issues
    print("\n🔍 Searching for issues in Pinecone...")
    issues = find_all_issues()
    print(f"Found {len(issues)} potential issues")
    
    if not issues:
        print("No issues found!")
        return
    
    # Cluster similar issues together
    clusters = cluster_issues(issues, similarity_threshold=0.85)
    
    if not clusters:
        print("No issues to process after clustering!")
        return
    
    print(f"\n📋 Processing {len(clusters)} unique issue clusters\n")
    
    # Build graph
    graph = build_agent_graph()
    
    # Process each cluster (only the representative issue)
    results = []
    for i, cluster in enumerate(clusters, 1):
        issue = cluster['representative']
        cluster_size = cluster['cluster_size']
        
        print("\n" + "=" * 60)
        print(f"Processing Cluster {i}/{len(clusters)}")
        if cluster_size > 1:
            print(f"⚠️  This cluster contains {cluster_size} similar issues (processing representative only)")
        print("=" * 60)
        print(f"Type: {issue['type']}")
        print(f"Text: {issue['text'][:200]}...")
        if cluster_size > 1:
            print(f"\nSimilar issues in this cluster:")
            for similar in cluster['similar_issues'][:3]:  # Show first 3 similar issues
                print(f"  - {similar['text'][:150]}...")
            if len(cluster['similar_issues']) > 3:
                print(f"  ... and {len(cluster['similar_issues']) - 3} more")
        print()
        
        # Initialize state with representative issue
        # If there are similar issues, we can optionally merge their text for context
        input_text = issue['text']
        if cluster['similar_issues']:
            # Add context about similar issues
            similar_texts = "\n".join([f"- {sim['text'][:200]}" for sim in cluster['similar_issues'][:2]])
            input_text = f"{issue['text']}\n\nNote: {cluster_size - 1} similar issue(s) detected:\n{similar_texts}"
        
        initial_state = AgentState(
            input_text=input_text,
            input_type=issue['type']
        )
        
        try:
            # Run agent
            final_state = graph.invoke(initial_state)
            
            # Check results
            if hasattr(final_state, 'pr_created') and final_state.pr_created:
                results.append({
                    'issue': issue['text'][:100],
                    'success': True,
                    'pr_url': final_state.pr_url if hasattr(final_state, 'pr_url') else None,
                    'branch': final_state.pr_branch if hasattr(final_state, 'pr_branch') else None,
                    'cluster_size': cluster_size
                })
                print(f"✅ PR created: {final_state.pr_url if hasattr(final_state, 'pr_url') else 'N/A'}")
                if cluster_size > 1:
                    print(f"   (This PR addresses {cluster_size} similar issues)")
            else:
                error = getattr(final_state, 'error', 'Unknown error') if hasattr(final_state, 'error') else 'Unknown error'
                results.append({
                    'issue': issue['text'][:100],
                    'success': False,
                    'error': error,
                    'cluster_size': cluster_size
                })
                print(f"❌ Failed: {error}")
        
        except Exception as e:
            print(f"❌ Error processing issue: {e}")
            results.append({
                'issue': issue['text'][:100],
                'success': False,
                'error': str(e),
                'cluster_size': cluster_size
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    successful = sum(1 for r in results if r['success'])
    total_issues_covered = sum(r.get('cluster_size', 1) for r in results if r['success'])
    print(f"✅ Successful: {successful}/{len(results)} clusters processed")
    print(f"📊 Total issues covered: {total_issues_covered} (from {len(issues)} original issues)")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    
    if successful > 0:
        print("\nCreated PRs:")
        for r in results:
            if r['success']:
                cluster_info = f" (covers {r.get('cluster_size', 1)} issue(s))" if r.get('cluster_size', 1) > 1 else ""
                print(f"  - {r['pr_url']}{cluster_info}")
    
    return results


if __name__ == "__main__":
    process_all_issues()

