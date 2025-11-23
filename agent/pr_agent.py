"""
GitHub Pull Request Agent

This agent creates pull requests on GitHub based on instructions.
It assumes changes have already been made to the codebase and just handles
the PR creation process.
"""

import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from github import Github
from github.GithubException import GithubException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PRAgent:
    """Agent that creates GitHub pull requests."""
    
    def __init__(
        self,
        repo_url: str = "https://github.com/Sanyam-G/Sentinell",
        github_token: Optional[str] = None
    ):
        """
        Initialize the PR agent.
        
        Args:
            repo_url: Full GitHub repository URL
            github_token: GitHub personal access token (or from GITHUB_TOKEN env var)
        """
        self.repo_url = repo_url
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        if not self.github_token:
            raise ValueError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable "
                "or pass it to the constructor."
            )
        
        # Extract owner and repo name from URL
        # Supports both https://github.com/owner/repo and git@github.com:owner/repo.git
        if "github.com" in repo_url:
            parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
            if len(parts) >= 2:
                self.owner = parts[0]
                self.repo_name = parts[1]
            else:
                raise ValueError(f"Invalid repository URL: {repo_url}")
        else:
            raise ValueError(f"Unsupported repository URL format: {repo_url}")
        
        # Initialize GitHub client
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(f"{self.owner}/{self.repo_name}")
    
    def create_pr(
        self,
        instructions: str,
        branch_name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a pull request based on instructions.
        
        Args:
            instructions: Description of what changes were made or what the PR is about
            branch_name: Name for the new branch (auto-generated if not provided)
            title: PR title (auto-generated if not provided)
            description: PR description (uses instructions if not provided)
            base_branch: Base branch to merge into (default: main)
        
        Returns:
            Dictionary with PR details including URL, number, and status
        """
        try:
            # Generate branch name if not provided
            if not branch_name:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                branch_name = f"pr-agent-{timestamp}"

                # Safety: never create a PR branch that is the same as the base branch
                if branch_name == base_branch:
                    return {
                        "success": False,
                        "error": (
                            f"Refusing to create PR from the base branch '{base_branch}'. "
                            "Please provide a different branch name."
                        ),
                        "branch_name": branch_name,
                    }
            
            # Generate title if not provided
            if not title:
                # Use first line of instructions or a default
                title = instructions.split("\n")[0][:100] if instructions else "Automated PR"
                if len(title) > 100:
                    title = title[:97] + "..."
            
            # Use instructions as description if not provided
            if not description:
                description = instructions
            
            # Check if we're in a git repository
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--git-dir"],
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                return {
                    "success": False,
                    "error": "Not in a git repository. Please run this from the repository root.",
                    "branch_name": branch_name
                }
            
            # Check current branch and status
            current_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True
            ).strip()
            
            # Check if there are uncommitted changes
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                text=True
            ).strip()
            
            if not status:
                return {
                    "success": False,
                    "error": "No changes detected. Please make changes to the codebase first.",
                    "current_branch": current_branch
                }
            
            # Create and checkout new branch
            try:
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                # Branch might already exist
                if "already exists" in str(e):
                    subprocess.run(
                        ["git", "checkout", branch_name],
                        check=True,
                        capture_output=True
                    )
                else:
                    raise
            
            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                check=True,
                capture_output=True
            )
            
            # Commit changes
            commit_message = f"Automated changes: {title}"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=True,
                capture_output=True
            )
            
            # Push branch to remote
            try:
                subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                return {
                    "success": False,
                    "error": f"Failed to push branch: {str(e)}",
                    "branch_name": branch_name,
                    "suggestion": "Make sure you have push access and the remote is configured."
                }
            
            # Create pull request using GitHub API
            try:
                pr = self.repo.create_pull(
                    title=title,
                    body=description,
                    head=branch_name,
                    base=base_branch
                )
                
                return {
                    "success": True,
                    "pr_number": pr.number,
                    "pr_url": pr.html_url,
                    "pr_title": pr.title,
                    "branch_name": branch_name,
                    "base_branch": base_branch,
                    "state": pr.state
                }
            
            except GithubException as e:
                return {
                    "success": False,
                    "error": f"Failed to create PR: {str(e)}",
                    "branch_name": branch_name,
                    "branch_pushed": True
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "type": type(e).__name__
            }
    
    def create_pr_from_existing_branch(
        self,
        branch_name: str,
        instructions: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a PR from an existing branch (useful if another agent made changes).
        
        Args:
            branch_name: Name of the existing branch
            instructions: Description of what the PR is about
            title: PR title (auto-generated if not provided)
            description: PR description (uses instructions if not provided)
            base_branch: Base branch to merge into (default: main)
        
        Returns:
            Dictionary with PR details
        """
        try:
            # Generate title if not provided
            if not title:
                title = instructions.split("\n")[0][:100] if instructions else "Automated PR"
                if len(title) > 100:
                    title = title[:97] + "..."
            
            if not description:
                description = instructions
            
            # Check if branch exists
            try:
                self.repo.get_branch(branch_name)
            except GithubException:
                return {
                    "success": False,
                    "error": f"Branch '{branch_name}' does not exist on remote.",
                    "branch_name": branch_name
                }

            # Safety: do not create a PR from the base branch on remote
            if branch_name == base_branch:
                return {
                    "success": False,
                    "error": (
                        f"Refusing to create PR from the base branch '{base_branch}'. "
                        "Provide a feature branch instead."
                    ),
                    "branch_name": branch_name,
                }
            
            # Check if PR already exists
            existing_prs = self.repo.get_pulls(
                state="open",
                head=f"{self.owner}:{branch_name}",
                base=base_branch
            )
            
            if existing_prs.totalCount > 0:
                pr = existing_prs[0]
                return {
                    "success": True,
                    "pr_number": pr.number,
                    "pr_url": pr.html_url,
                    "pr_title": pr.title,
                    "branch_name": branch_name,
                    "base_branch": base_branch,
                    "state": pr.state,
                    "message": "PR already exists for this branch"
                }
            
            # Create pull request
            pr = self.repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=base_branch
            )
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "pr_title": pr.title,
                "branch_name": branch_name,
                "base_branch": base_branch,
                "state": pr.state
            }
        
        except GithubException as e:
            return {
                "success": False,
                "error": f"Failed to create PR: {str(e)}",
                "branch_name": branch_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "type": type(e).__name__
            }


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create a GitHub pull request")
    parser.add_argument(
        "--instructions",
        type=str,
        required=True,
        help="Description of changes or instructions for the PR"
    )
    parser.add_argument(
        "--branch",
        type=str,
        help="Branch name (auto-generated if not provided)"
    )
    parser.add_argument(
        "--title",
        type=str,
        help="PR title (auto-generated from instructions if not provided)"
    )
    parser.add_argument(
        "--base",
        type=str,
        default="main",
        help="Base branch (default: main)"
    )
    parser.add_argument(
        "--existing-branch",
        action="store_true",
        help="Use existing branch instead of creating new one"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="https://github.com/Sanyam-G/Sentinell",
        help="Repository URL"
    )
    
    args = parser.parse_args()
    
    try:
        agent = PRAgent(repo_url=args.repo)
        
        if args.existing_branch:
            if not args.branch:
                print("Error: --branch is required when using --existing-branch")
                sys.exit(1)
            result = agent.create_pr_from_existing_branch(
                branch_name=args.branch,
                instructions=args.instructions,
                title=args.title,
                base_branch=args.base
            )
        else:
            result = agent.create_pr(
                instructions=args.instructions,
                branch_name=args.branch,
                title=args.title,
                base_branch=args.base
            )
        
        if result["success"]:
            print(f"\n✅ Successfully created PR!")
            print(f"   PR #{result['pr_number']}: {result['pr_title']}")
            print(f"   URL: {result['pr_url']}")
            print(f"   Branch: {result['branch_name']} -> {result['base_branch']}")
        else:
            print(f"\n❌ Failed to create PR: {result.get('error', 'Unknown error')}")
            if "suggestion" in result:
                print(f"   Suggestion: {result['suggestion']}")
            sys.exit(1)
    
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease set GITHUB_TOKEN environment variable:")
        print("  export GITHUB_TOKEN=your_token_here")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

