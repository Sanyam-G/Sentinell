"""
Test script for the code-fixing agent.
Uses pre-coded issues from the vector_db_payload.json.
"""

from run_agent import run_agent

# Test cases from the vector_db_payload.json

# Test 1: Slack message about balance issue
slack_issue = """URGENT: Ticket #9442. User claims they withdrew $500 but their 'Verified Balance' actually INCREASED by $500?"""

# Test 2: Log error
log_issue = """[2025-11-23T17:05:30] [ERROR] AUDIT FAILURE: Transaction History ($1000) != Calculated State ($2000). Mismatch detected."""

# Test 3: Another Slack message
slack_issue2 = """Wait, increased? That sounds like a sign flip error. Did we touch the ledger logic recently?"""

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        # Run batch processing
        from batch_agent import process_all_issues
        process_all_issues()
    else:
        # Test individual issues
        print("Testing Code-Fixing Agent v1\n")
        
        # Test with Slack message
        print("\n" + "="*60)
        print("TEST 1: Slack Message Issue")
        print("="*60)
        run_agent(slack_issue, "slack")
        
        # Test with log error
        print("\n" + "="*60)
        print("TEST 2: Log Error")
        print("="*60)
        run_agent(log_issue, "log")

