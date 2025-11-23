"""
Nodes for the code-fixing agent graph.
"""

import os
import json
import re
from typing import Dict, Any
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from pinecone import Pinecone
from openai import OpenAI
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_state import AgentState
from pr_agent import PRAgent
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
llm = ChatAnthropic(model="claude-sonnet-4-20250514")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX", "test-rag-index"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def detect_issue(state: AgentState) -> AgentState:
    """Detect if the input text contains an issue that needs fixing."""
    state.status = "detecting"
    
    prompt = f"""You are analyzing a potential issue report. Determine if this needs a code fix.

Input text:
{state.input_text}

Input type: {state.input_type}

Analyze this and determine:
1. Is there a bug or issue that requires code changes?
2. What is the issue? (be specific)
3. Confidence level (0.0 to 1.0)

Respond with ONLY JSON:
{{
    "has_issue": true/false,
    "issue_description": "description of the issue",
    "confidence": 0.0-1.0
}}"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Extract JSON
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            result = json.loads(json_str)
            
            if result.get("has_issue", False):
                state.detected_issue = result.get("issue_description", "Unknown issue")
                state.issue_confidence = result.get("confidence", 0.5)
            else:
                state.status = "done"
                state.error = "No issue detected in input"
        else:
            raise ValueError("No JSON in response")
    
    except Exception as e:
        state.error = f"Error detecting issue: {str(e)}"
        state.status = "done"
    
    return state


def query_pinecone(state: AgentState) -> AgentState:
    """Query Pinecone for relevant commits, logs, and Slack messages."""
    state.status = "querying"
    
    if not state.detected_issue:
        state.error = "No issue detected, skipping Pinecone query"
        return state
    
    try:
        # Create query embedding
        query_text = f"{state.input_text}\n{state.detected_issue}"
        response = openai_client.embeddings.create(
            input=query_text,
            model="text-embedding-3-large",
            dimensions=1024
        )
        query_embedding = response.data[0].embedding
        
        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=10,
            include_metadata=True
        )
        
        # Categorize results
        for match in results.matches:
            metadata = match.metadata
            item_type = metadata.get('type', 'unknown')
            
            item = {
                'id': match.id,
                'score': match.score,
                'text': metadata.get('text', ''),
                'timestamp': metadata.get('timestamp', ''),
                'metadata': metadata
            }
            
            if item_type == 'code_change':
                state.relevant_commits.append(item)
            elif item_type == 'log':
                state.relevant_logs.append(item)
            elif item_type == 'chat':
                state.relevant_slack.append(item)
    
    except Exception as e:
        state.error = f"Error querying Pinecone: {str(e)}"
    
    return state


def analyze_code(state: AgentState) -> AgentState:
    """Analyze the code to find the root cause and determine what needs to be fixed."""
    state.status = "analyzing"
    
    # Build context from Pinecone results
    context_parts = []
    
    if state.relevant_commits:
        context_parts.append("=== Relevant Commits ===")
        for commit in state.relevant_commits[:5]:  # Top 5
            context_parts.append(f"\nCommit: {commit['id']}")
            # Extract the actual code diff from commit text
            commit_text = commit['text']
            if "diff --git" in commit_text:
                # Extract the file path and code changes
                context_parts.append(commit_text[:1000])  # First 1000 chars
            else:
                context_parts.append(commit_text[:500])
    
    if state.relevant_logs:
        context_parts.append("\n=== Relevant Logs ===")
        for log in state.relevant_logs[:3]:
            context_parts.append(f"\nLog: {log['text'][:300]}...")
    
    context = "\n".join(context_parts)
    
    prompt = f"""You are an expert code analyst. Analyze the issue and determine the exact code fix needed.

Issue: {state.detected_issue}

Context from codebase (commits, logs):
{context}

CRITICAL REQUIREMENTS:
1. Extract the file path from commit diffs - look for "diff --git a/path/to/file.py" patterns
2. The file_path MUST be a valid relative path (e.g., "account.py", "Madhacks-Inc/account.py")
3. The file_path MUST NOT be "Unable to determine" or similar - you MUST find it in the context
4. Copy the EXACT old_code from the file/diff
5. Provide the EXACT new_code with the fix

Your task:
1. Find which file(s) contain the bug by examining commit diffs
2. Determine the root cause
3. Identify the exact code that needs to be fixed
4. Provide the exact fix

If you cannot find a valid file path in the context, set code_fix to an empty object {{}}.

Respond with ONLY valid JSON:
{{
    "root_cause": "detailed explanation of the bug",
    "affected_files": ["list of file paths"],
    "fix_description": "what needs to be changed",
    "code_fix": {{
        "file_path": "relative path from repo root (MUST extract from diff, e.g. 'account.py')",
        "old_code": "exact code snippet with the bug",
        "new_code": "exact code snippet with the fix"
    }}
}}"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Extract JSON
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            result = json.loads(json_str)
            
            state.root_cause = result.get("root_cause", "Unknown")
            state.affected_files = result.get("affected_files", [])
            state.proposed_fix = result.get("fix_description", "")
            
            # Store code fix with both old and new code for proper patching
            code_fix = result.get("code_fix", {})
            if code_fix:
                file_path = code_fix.get("file_path", "").strip()
                old_code = code_fix.get("old_code", "").strip()
                new_code = code_fix.get("new_code", "").strip()
                
                # Validate file path
                if not file_path or len(file_path) > 200 or "Unable to determine" in file_path:
                    state.error = f"Invalid file path from analysis: {file_path}"
                    state.status = "done"
                    return state
                
                if not new_code:
                    state.error = "No new code provided in fix"
                    state.status = "done"
                    return state
                
                if file_path and new_code:
                    # Store as dict with old and new for proper replacement
                    state.code_changes[file_path] = {
                        "old": old_code,
                        "new": new_code
                    }
        else:
            raise ValueError("No JSON in response")
    
    except Exception as e:
        state.error = f"Error analyzing code: {str(e)}"
        state.status = "done"
    
    return state


def make_code_changes(state: AgentState) -> AgentState:
    """Actually make the code changes to files."""
    state.status = "fixing"
    
    if not state.code_changes:
        state.error = "No code changes to make"
        state.status = "done"
        return state
    
    # Validate code changes before proceeding
    for file_path in list(state.code_changes.keys()):
        if not file_path or len(file_path) > 200 or "Unable to determine" in file_path:
            state.error = f"Invalid file path: {file_path}"
            state.status = "done"
            return state
    
    try:
        # Get repo root (go up from agent/ to repo root)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        for file_path, change_data in state.code_changes.items():
            # Handle relative paths from repo root
            full_path = os.path.join(repo_root, file_path)
            
            # Create directory if needed
            if os.path.dirname(full_path):
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Read existing file if it exists
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    existing = f.read()
                
                # Apply the fix
                if isinstance(change_data, dict):
                    # Has old and new code - do replacement
                    old_code = change_data.get("old", "")
                    new_code = change_data.get("new", "")
                    
                    if old_code in existing:
                        # Simple string replacement
                        fixed = existing.replace(old_code, new_code)
                        with open(full_path, 'w') as f:
                            f.write(fixed)
                        print(f"✅ Fixed {file_path}: replaced '{old_code[:50]}...' with '{new_code[:50]}...'")
                    else:
                        # Try to find similar code (fuzzy match)
                        # For v1, we'll just append a comment if we can't find exact match
                        # In v2, use AST-based patching
                        print(f"⚠️  Could not find exact match in {file_path}, attempting fuzzy replacement...")
                        # Try line-by-line replacement
                        lines = existing.split('\n')
                        new_lines = []
                        replaced = False
                        for line in lines:
                            if old_code.strip() in line and not replaced:
                                new_lines.append(line.replace(old_code.strip(), new_code.strip()))
                                replaced = True
                            else:
                                new_lines.append(line)
                        
                        if replaced:
                            with open(full_path, 'w') as f:
                                f.write('\n'.join(new_lines))
                            print(f"✅ Fixed {file_path} (fuzzy match)")
                        else:
                            state.error = f"Could not find code to replace in {file_path}"
                            return state
                else:
                    # Just new code provided - write it (for new files)
                    with open(full_path, 'w') as f:
                        f.write(change_data)
                    print(f"✅ Created/updated {file_path}")
            else:
                # New file - create it
                new_code = change_data.get("new", change_data) if isinstance(change_data, dict) else change_data
                with open(full_path, 'w') as f:
                    f.write(new_code)
                print(f"✅ Created new file {file_path}")
        
        state.status = "creating_pr"
    
    except Exception as e:
        state.error = f"Error making code changes: {str(e)}"
        import traceback
        traceback.print_exc()
        state.status = "done"
    
    return state


def create_pr(state: AgentState) -> AgentState:
    """Create a pull request with the changes."""
    state.status = "creating_pr"
    
    if not state.code_changes:
        state.error = "No changes to create PR for"
        state.status = "done"
        return state
    
    try:
        pr_agent = PRAgent()
        pr_description = f"""## Issue Fixed
{state.detected_issue}

## Root Cause
{state.root_cause}

## Changes Made
{state.proposed_fix}

## Files Changed
{', '.join(state.affected_files) if state.affected_files else 'N/A'}

This PR was automatically generated by the code-fixing agent.
"""
        
        result = pr_agent.create_pr(
            instructions=pr_description,
            title=f"Fix: {state.detected_issue[:50] if state.detected_issue else 'Unknown issue'}",
            description=pr_description
        )
        
        if result.get("success"):
            state.pr_created = True
            state.pr_url = result.get("pr_url")
            state.pr_branch = result.get("branch_name")
            state.status = "done"
        else:
            state.error = result.get("error", "Failed to create PR")
            state.status = "done"
    
    except Exception as e:
        state.error = f"Error creating PR: {str(e)}"
        state.status = "done"
    
    return state

