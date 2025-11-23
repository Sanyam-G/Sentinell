"""
Simple test file - finds all errors from Pinecone and creates PRs for each.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from batch_agent import process_all_issues

if __name__ == "__main__":
    print("=" * 60)
    print("Processing All Issues from Pinecone")
    print("=" * 60)
    print("\nFinding all errors and creating separate PRs for each...\n")
    
    process_all_issues()
