#!/usr/bin/env python3
# Quick script to sync repos between GitHub and GitLab
# Works for code and issues, might add more later

import os
import subprocess
import sys
import json
import requests
from datetime import datetime

# Timeout for git operations (in seconds)
GIT_TIMEOUT = 300  # 5 minutes
API_TIMEOUT = 30   # 30 seconds for API calls

# Get tokens and repo names from env vars
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')  # username/repo format
GITLAB_REPO = os.getenv('GITLAB_REPO')  # username/repo format
GITHUB_API_BASE = 'https://api.github.com'
GITLAB_API_BASE = os.getenv('GITLAB_API_BASE', 'https://gitlab.com/api/v4')


class RepoSyncer:
    def __init__(self):
        # Set up API headers for requests
        if GITHUB_TOKEN:
            self.github_headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
        else:
            self.github_headers = {}
        
        if GITLAB_TOKEN:
            self.gitlab_headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}
        else:
            self.gitlab_headers = {}
    
    def sync_code(self, direction='both'):
        """Sync code between repos"""
        print(f"Syncing code ({direction})...")
        
        if direction in ['github-to-gitlab', 'both']:
            self._sync_to_gitlab()
        
        if direction in ['gitlab-to-github', 'both']:
            self._sync_to_github()
    
    def _sync_to_gitlab(self):
        """Push code from GitHub to GitLab"""
        if not GITHUB_REPO or not GITLAB_REPO:
            print("Error: Need to set GITHUB_REPO and GITLAB_REPO env vars")
            return
        
        print(f"Syncing {GITHUB_REPO} -> {GITLAB_REPO}")
        
        try:
            # Build URLs with tokens if we have them
            if GITHUB_TOKEN:
                github_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
            else:
                github_url = f"https://github.com/{GITHUB_REPO}.git"
            
            if GITLAB_TOKEN:
                gitlab_url = f"https://oauth2:{GITLAB_TOKEN}@gitlab.com/{GITLAB_REPO}.git"
            else:
                gitlab_url = f"https://gitlab.com/{GITLAB_REPO}.git"
            
            # Clone if needed
            if not os.path.exists('.github_repo'):
                print("Cloning GitHub repo...")
                subprocess.run(['git', 'clone', github_url, '.github_repo'], check=True, timeout=GIT_TIMEOUT)
            
            os.chdir('.github_repo')
            
            # Set git user config for commits (needed for merges)
            subprocess.run(['git', 'config', 'user.email', 'aminpriyam2499@gmail.com'], check=True, timeout=10)
            subprocess.run(['git', 'config', 'user.name', 'Priyam Amin'], check=True, timeout=10)
            
            # Configure git timeouts to prevent hanging
            subprocess.run(['git', 'config', 'http.timeout', '300'], check=False, timeout=10)
            subprocess.run(['git', 'config', 'http.postBuffer', '524288000'], check=False, timeout=10)
            
            print("Fetching from origin (GitHub)...")
            subprocess.run(['git', 'fetch', 'origin'], check=True, timeout=GIT_TIMEOUT)
            
            # Add gitlab remote (ignore error if it exists)
            subprocess.run(['git', 'remote', 'add', 'gitlab', gitlab_url], 
                         capture_output=True)
            subprocess.run(['git', 'remote', 'set-url', 'gitlab', gitlab_url])
            
            # Fetch from GitLab to see what's there
            print("Fetching from GitLab to check for conflicts...")
            subprocess.run(['git', 'fetch', 'gitlab'], capture_output=True, timeout=GIT_TIMEOUT)
            
            # Get only branches from origin (GitHub), not gitlab remote
            result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
            branches = []
            for b in result.stdout.split('\n'):
                b = b.strip()
                # Only get branches from origin (GitHub), ignore gitlab remote branches
                if b and 'HEAD' not in b and b.startswith('origin/'):
                    branch_name = b.replace('origin/', '')
                    # Skip common non-branch refs
                    if branch_name and not branch_name.startswith('gitlab/'):
                        branches.append(branch_name)
            
            print(f"Found {len(branches)} branch(es) to sync: {', '.join(branches)}")
            
            for branch in branches:
                try:
                    local_branch_check = subprocess.run(
                        ['git', 'branch', '--list', branch],
                        capture_output=True, text=True
                    )
                    if not local_branch_check.stdout.strip():
                        print(f"  Creating local branch {branch} from origin/{branch}...")
                        checkout_result = subprocess.run(
                            ['git', 'checkout', '-b', branch, f'origin/{branch}'], 
                            capture_output=True, text=True, check=False
                        )
                        if checkout_result.returncode != 0:
                            print(f"  Warning: Could not create branch {branch}: {checkout_result.stderr}")
                            continue
                    else:
                        checkout_result = subprocess.run(
                            ['git', 'checkout', branch], 
                            capture_output=True, text=True, check=False
                        )
                        if checkout_result.returncode != 0:
                            print(f"  Warning: Could not checkout branch {branch}: {checkout_result.stderr}")
                            continue
                    
                    # Always reset to match GitHub exactly (GitHub is source of truth)
                    reset_result = subprocess.run(
                        ['git', 'reset', '--hard', f'origin/{branch}'], 
                        capture_output=True, text=True, check=False
                    )
                    if reset_result.returncode != 0:
                        print(f"  Warning: Could not reset branch {branch}: {reset_result.stderr}")
                        continue
                    
                    gitlab_branch_exists = subprocess.run(
                        ['git', 'ls-remote', '--heads', 'gitlab', branch],
                        capture_output=True, text=True, timeout=30
                    ).stdout.strip()
                    
                    print(f"     Pushing {branch} to GitLab (timeout: {GIT_TIMEOUT}s)...")
                    result = subprocess.run(['git', 'push', 'gitlab', branch],
                                           capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT)
                    
                    if result.returncode == 0:
                        # Verify push actually worked
                        verify_push = subprocess.run(
                            ['git', 'ls-remote', '--heads', 'gitlab', branch],
                            capture_output=True, text=True, check=False, timeout=30
                        )
                        if verify_push.returncode == 0 and verify_push.stdout.strip():
                            print(f"  Synced branch: {branch}")
                        else:
                            print(f"  Warning: Push reported success but branch not found on GitLab")
                            print(f"     This might indicate a permission or repository access issue")
                    else:
                        error_msg = result.stderr or result.stdout
                        is_protected = 'protected branch' in error_msg or 'not allowed to force push' in error_msg
                        is_diverged = 'rejected' in error_msg and ('fetch first' in error_msg or 'non-fast-forward' in error_msg)
                        
                        if is_protected or is_diverged:
                            print(f"  Branch {branch} needs merge (protected or diverged)")
                            
                            if gitlab_branch_exists:
                                print(f"     Fetching from GitLab...")
                                subprocess.run(['git', 'fetch', 'gitlab', branch], capture_output=True)
                                
                                # First, ensure we're exactly at GitHub version
                                print(f"     Resetting to GitHub version...")
                                subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], capture_output=True)
                                
                                # Get list of files from GitHub
                                github_files_result = subprocess.run(
                                    ['git', 'ls-tree', '-r', '--name-only', 'HEAD'],
                                    capture_output=True, text=True, check=True
                                )
                                github_files = set()
                                for line in github_files_result.stdout.strip().split('\n'):
                                    if line.strip():
                                        github_files.add(line.strip())
                                
                                # Create a new commit that matches GitHub exactly
                                # This ensures we have a clean state
                                print(f"     Creating sync commit matching GitHub exactly...")
                                
                                # Remove all files first
                                subprocess.run(['git', 'rm', '-rf', '--ignore-unmatch', '.'], capture_output=True, cwd='.')
                                
                                # Checkout all files from GitHub
                                subprocess.run(['git', 'checkout', 'HEAD', '--', '.'], capture_output=True)
                                
                                # Add all files
                                subprocess.run(['git', 'add', '-A'], capture_output=True)
                                
                                # Check if there are changes
                                status_check = subprocess.run(
                                    ['git', 'status', '--porcelain'],
                                    capture_output=True, text=True, check=True
                                )
                                
                                if status_check.stdout.strip() or True:  # Always create commit to ensure sync
                                    commit_result = subprocess.run(
                                        ['git', 'commit', '-m', f'Sync from GitHub - exact match [skip sync]'],
                                        capture_output=True, text=True, check=False
                                    )
                                
                                # Now merge GitLab's branch to preserve history (but we'll keep our version)
                                print(f"     Merging GitLab history (keeping GitHub files)...")
                                merge_result = subprocess.run(
                                    ['git', 'merge', f'gitlab/{branch}', '--no-edit', '--no-ff', '--allow-unrelated-histories', '-X', 'ours'],
                                    capture_output=True, text=True, check=False
                                )
                                
                                # Handle merge conflicts explicitly
                                if merge_result.returncode != 0:
                                    merge_output = merge_result.stderr or merge_result.stdout
                                    
                                    # Check if we're in a merge conflict state
                                    conflict_check = subprocess.run(
                                        ['git', 'status', '--porcelain'],
                                        capture_output=True, text=True, check=True
                                    )
                                    
                                    if 'CONFLICT' in merge_output or 'conflict' in merge_output.lower() or '<<<<<<<' in conflict_check.stdout:
                                        print(f"     Merge conflicts detected, resolving by keeping GitHub version...")
                                        
                                        # Abort current merge
                                        subprocess.run(['git', 'merge', '--abort'], capture_output=True, check=False)
                                        
                                        # Reset to GitHub version
                                        subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], capture_output=True)
                                        
                                        # Create commit matching GitHub exactly
                                        subprocess.run(['git', 'add', '-A'], capture_output=True)
                                        subprocess.run(
                                            ['git', 'commit', '-m', f'Sync from GitHub - exact match [skip sync]'],
                                            capture_output=True, text=True, check=False
                                        )
                                        
                                        # Try merge again with ours strategy
                                        merge_result = subprocess.run(
                                            ['git', 'merge', f'gitlab/{branch}', '--no-edit', '--no-ff', '--allow-unrelated-histories', '-X', 'ours'],
                                            capture_output=True, text=True, check=False
                                        )
                                        
                                        # If still conflicts, explicitly resolve by keeping our version (GitHub)
                                        if merge_result.returncode != 0:
                                            conflict_status = subprocess.run(
                                                ['git', 'status', '--porcelain'],
                                                capture_output=True, text=True, check=True
                                            )
                                            
                                            if 'UU' in conflict_status.stdout or 'AA' in conflict_status.stdout or 'DD' in conflict_status.stdout:
                                                print(f"     Explicitly resolving conflicts by keeping GitHub version...")
                                                
                                                # Get list of conflicted files
                                                conflicted_files = subprocess.run(
                                                    ['git', 'diff', '--name-only', '--diff-filter=U'],
                                                    capture_output=True, text=True, check=True
                                                )
                                                
                                                # For each conflicted file, keep our version (GitHub)
                                                for file in conflicted_files.stdout.strip().split('\n'):
                                                    if file.strip():
                                                        print(f"       Resolving conflict in {file.strip()} (keeping GitHub version)")
                                                        subprocess.run(
                                                            ['git', 'checkout', '--ours', file.strip()],
                                                            capture_output=True, check=False
                                                        )
                                                        subprocess.run(['git', 'add', file.strip()], capture_output=True)
                                                
                                                # Complete the merge
                                                subprocess.run(
                                                    ['git', 'commit', '-m', f'Merge GitLab branch - resolved conflicts by keeping GitHub version [skip sync]'],
                                                    capture_output=True, text=True, check=False
                                                )
                                                merge_result.returncode = 0  # Mark as successful
                                            else:
                                                # If merge still failed for other reasons, abort and reset
                                                subprocess.run(['git', 'merge', '--abort'], capture_output=True, check=False)
                                                subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], capture_output=True)
                                                subprocess.run(['git', 'add', '-A'], capture_output=True)
                                                subprocess.run(
                                                    ['git', 'commit', '-m', f'Sync from GitHub - exact match [skip sync]'],
                                                    capture_output=True, text=True, check=False
                                                )
                                    else:
                                        # Merge failed for other reasons, abort and reset
                                        subprocess.run(['git', 'merge', '--abort'], capture_output=True, check=False)
                                        subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], capture_output=True)
                                        subprocess.run(['git', 'add', '-A'], capture_output=True)
                                        subprocess.run(
                                            ['git', 'commit', '-m', f'Sync from GitHub - exact match [skip sync]'],
                                            capture_output=True, text=True, check=False
                                        )
                                
                                # After merge, ensure files match GitHub exactly (but keep the merge commit)
                                print(f"     Ensuring files match GitHub exactly...")
                                
                                # Get all currently tracked files
                                current_files_result = subprocess.run(
                                    ['git', 'ls-files'],
                                    capture_output=True, text=True, check=True
                                )
                                current_files = set()
                                for line in current_files_result.stdout.strip().split('\n'):
                                    if line.strip():
                                        current_files.add(line.strip())
                                
                                # Remove all files from index first
                                if current_files:
                                    print(f"     Removing all files from index...")
                                    for file in current_files:
                                        subprocess.run(['git', 'rm', '--cached', '--ignore-unmatch', file], capture_output=True)
                                
                                # Remove untracked files
                                subprocess.run(['git', 'clean', '-fd'], capture_output=True)
                                
                                # Now checkout all files from GitHub (this adds them back)
                                print(f"     Checking out all files from GitHub...")
                                subprocess.run(['git', 'checkout', f'origin/{branch}', '--', '.'], capture_output=True)
                                
                                # Remove any files that still exist but aren't in GitHub
                                current_after = subprocess.run(
                                    ['git', 'ls-files'],
                                    capture_output=True, text=True, check=True
                                )
                                files_after = set()
                                for line in current_after.stdout.strip().split('\n'):
                                    if line.strip():
                                        files_after.add(line.strip())
                                
                                extra_files = files_after - github_files
                                if extra_files:
                                    print(f"     Removing {len(extra_files)} extra file(s) not in GitHub...")
                                    for file in extra_files:
                                        subprocess.run(['git', 'rm', '--cached', '--ignore-unmatch', file], capture_output=True)
                                        # Also remove from filesystem if it exists
                                        if os.path.exists(file):
                                            os.remove(file)
                                
                                # Add all files (this stages everything)
                                subprocess.run(['git', 'add', '-A'], capture_output=True)
                                
                                # Create final commit if there are changes
                                final_status = subprocess.run(
                                    ['git', 'status', '--porcelain'],
                                    capture_output=True, text=True, check=True
                                )
                                if final_status.stdout.strip():
                                    subprocess.run(
                                        ['git', 'commit', '-m', f'Sync from GitHub - ensure exact match [skip sync]'],
                                        capture_output=True, text=True, check=False
                                    )
                                
                                # Fetch latest from GitLab to ensure we're up to date
                                print(f"     Fetching latest from GitLab...")
                                subprocess.run(['git', 'fetch', 'gitlab', branch], capture_output=True)
                                
                                # Check if we're ahead or behind
                                behind_check = subprocess.run(
                                    ['git', 'rev-list', '--left-right', '--count', f'HEAD...gitlab/{branch}'],
                                    capture_output=True, text=True, check=True
                                )
                                behind_ahead = behind_check.stdout.strip().split()
                                if len(behind_ahead) == 2:
                                    behind = int(behind_ahead[0])
                                    ahead = int(behind_ahead[1])
                                    if behind > 0:
                                        print(f"     Still behind GitLab by {behind} commit(s), merging again...")
                                        merge_again = subprocess.run(
                                            ['git', 'merge', f'gitlab/{branch}', '--no-edit', '--no-ff', '-X', 'ours'],
                                            capture_output=True, text=True, check=False
                                        )
                                        
                                        # Handle conflicts in second merge attempt
                                        if merge_again.returncode != 0:
                                            conflict_check = subprocess.run(
                                                ['git', 'status', '--porcelain'],
                                                capture_output=True, text=True, check=True
                                            )
                                            
                                            if 'UU' in conflict_check.stdout or 'AA' in conflict_check.stdout:
                                                print(f"     Resolving conflicts in second merge (keeping GitHub version)...")
                                                conflicted_files = subprocess.run(
                                                    ['git', 'diff', '--name-only', '--diff-filter=U'],
                                                    capture_output=True, text=True, check=True
                                                )
                                                
                                                for file in conflicted_files.stdout.strip().split('\n'):
                                                    if file.strip():
                                                        subprocess.run(
                                                            ['git', 'checkout', '--ours', file.strip()],
                                                            capture_output=True, check=False
                                                        )
                                                        subprocess.run(['git', 'add', file.strip()], capture_output=True)
                                                
                                                subprocess.run(
                                                    ['git', 'commit', '-m', f'Merge GitLab branch - resolved conflicts [skip sync]'],
                                                    capture_output=True, text=True, check=False
                                                )
                                                merge_again.returncode = 0
                                        
                                        if merge_again.returncode == 0:
                                            # Ensure files still match GitHub exactly
                                            current_merge_files = subprocess.run(
                                                ['git', 'ls-files'],
                                                capture_output=True, text=True, check=True
                                            )
                                            merge_files_set = set()
                                            for line in current_merge_files.stdout.strip().split('\n'):
                                                if line.strip():
                                                    merge_files_set.add(line.strip())
                                            
                                            # Remove all files from index
                                            if merge_files_set:
                                                for file in merge_files_set:
                                                    subprocess.run(['git', 'rm', '--cached', '--ignore-unmatch', file], capture_output=True)
                                            
                                            # Remove untracked files
                                            subprocess.run(['git', 'clean', '-fd'], capture_output=True)
                                            
                                            # Checkout all files from GitHub
                                            subprocess.run(['git', 'checkout', f'origin/{branch}', '--', '.'], capture_output=True)
                                            
                                            # Remove any extra files
                                            after_merge_check = subprocess.run(
                                                ['git', 'ls-files'],
                                                capture_output=True, text=True, check=True
                                            )
                                            after_merge_set = set()
                                            for line in after_merge_check.stdout.strip().split('\n'):
                                                if line.strip():
                                                    after_merge_set.add(line.strip())
                                            
                                            extra_after_merge = after_merge_set - github_files
                                            if extra_after_merge:
                                                for file in extra_after_merge:
                                                    subprocess.run(['git', 'rm', '--cached', '--ignore-unmatch', file], capture_output=True)
                                                    if os.path.exists(file):
                                                        os.remove(file)
                                            
                                            subprocess.run(['git', 'add', '-A'], capture_output=True)
                                            status_after = subprocess.run(
                                                ['git', 'status', '--porcelain'],
                                                capture_output=True, text=True, check=True
                                            )
                                            if status_after.stdout.strip():
                                                subprocess.run(
                                                    ['git', 'commit', '-m', f'Sync from GitHub - exact match [skip sync]'],
                                                    capture_output=True, text=True, check=False
                                                )
                                
                                print(f"     Pushing to GitLab (timeout: {GIT_TIMEOUT}s)...")
                                push_result = subprocess.run(
                                    ['git', 'push', 'gitlab', branch],
                                    capture_output=True, text=True, check=False, timeout=GIT_TIMEOUT
                                )
                                
                                if push_result.returncode == 0:
                                    print(f"  Synced branch: {branch} (merged and pushed)")
                                else:
                                    push_error = push_result.stderr or push_result.stdout
                                    print(f"  Error: Push failed after merge")
                                    print(f"     Error: {push_error[:500]}")
                                    if 'protected branch' in push_error:
                                        print(f"     Branch is protected - unprotect it or give token permission")
                                    elif '403' in push_error or 'Forbidden' in push_error:
                                        print(f"     Token permission issue - check token has write_repository scope")
                                    elif '401' in push_error:
                                        print(f"     Authentication failed - check token is valid")
                            else:
                                # Branch doesn't exist on GitLab, just push
                                print(f"     Branch doesn't exist on GitLab, pushing...")
                                push_result = subprocess.run(
                                    ['git', 'push', 'gitlab', branch],
                                    capture_output=True, text=True, check=False
                                )
                                if push_result.returncode == 0:
                                    print(f"  Synced branch: {branch}")
                                else:
                                    push_error = push_result.stderr or push_result.stdout
                                    print(f"  Error: Push failed: {push_error[:500]}")
                        else:
                            # Not protected or diverged, but push failed for another reason
                            if 'deny updating a hidden ref' in error_msg:
                                print(f"  Skipping branch {branch} - hidden ref")
                            elif '403' in error_msg or 'Forbidden' in error_msg:
                                print(f"  Error: 403 Forbidden - check token permissions")
                            elif '401' in error_msg or 'Unauthorized' in error_msg:
                                print(f"  Error: Authentication failed - check token")
                            else:
                                print(f"  Warning: Failed to sync branch {branch}: {error_msg[:200]}")
                except subprocess.CalledProcessError as e:
                    print(f"  Warning: Failed to sync branch {branch}: {e}")
            
            os.chdir('..')
            print("Done syncing to GitLab")
            
        except Exception as e:
            print(f"Error: {e}")
    
    def _sync_to_github(self):
        """Push code from GitLab to GitHub"""
        if not GITHUB_REPO or not GITLAB_REPO:
            print("❌ Need to set GITHUB_REPO and GITLAB_REPO env vars")
            return
        
        print(f"Syncing {GITLAB_REPO} -> {GITHUB_REPO}")
        
        try:
            if GITHUB_TOKEN:
                github_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
            else:
                github_url = f"https://github.com/{GITHUB_REPO}.git"
            
            if GITLAB_TOKEN:
                gitlab_url = f"https://oauth2:{GITLAB_TOKEN}@gitlab.com/{GITLAB_REPO}.git"
            else:
                gitlab_url = f"https://gitlab.com/{GITLAB_REPO}.git"
            
            # Clone if needed
            if not os.path.exists('.gitlab_repo'):
                print("Cloning GitLab repo...")
                subprocess.run(['git', 'clone', gitlab_url, '.gitlab_repo'], check=True, timeout=GIT_TIMEOUT)
            
            os.chdir('.gitlab_repo')
            
            # Set git user config for commits (needed for merges)
            subprocess.run(['git', 'config', 'user.email', 'aminpriyam2499@gmail.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'Priyam Amin'], check=True)
            
            subprocess.run(['git', 'fetch', 'origin'], check=True, timeout=GIT_TIMEOUT)
            subprocess.run(['git', 'remote', 'add', 'github', github_url], 
                         capture_output=True)
            subprocess.run(['git', 'remote', 'set-url', 'github', github_url])
            
            # Push all branches
            result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
            branches = []
            for b in result.stdout.split('\n'):
                b = b.strip()
                if b and 'HEAD' not in b:
                    branches.append(b.replace('origin/', ''))
            
            for branch in branches:
                try:
                    subprocess.run(['git', 'checkout', branch], check=True, capture_output=True)
                    subprocess.run(['git', 'push', 'github', branch], check=True, timeout=GIT_TIMEOUT)
                    print(f"  Synced branch: {branch}")
                except subprocess.CalledProcessError as e:
                    print(f"  Warning: Failed to sync branch {branch}: {e}")
            
            os.chdir('..')
            print("Done syncing to GitHub")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def sync_issues(self, direction='both'):
        """Sync issues between the two platforms"""
        print(f"Syncing issues ({direction})...")
        
        if direction in ['github-to-gitlab', 'both']:
            self._sync_issues_to_gitlab()
        
        if direction in ['gitlab-to-github', 'both']:
            self._sync_issues_to_github()
    
    def _sync_issues_to_gitlab(self):
        """Copy issues from GitHub to GitLab"""
        if not GITHUB_REPO or not GITLAB_REPO:
            return
        
        print(f"Syncing issues: {GITHUB_REPO} -> {GITLAB_REPO}")
        
        try:
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/issues"
            response = requests.get(url, headers=self.github_headers, params={'state': 'all'}, timeout=API_TIMEOUT)
            if response.status_code != 200:
                print(f"Error: Failed to get GitHub issues: {response.status_code}")
                return
            issues = response.json()
            
            gitlab_project_id = self._get_gitlab_project_id()
            if not gitlab_project_id:
                print("Error: Couldn't find GitLab project")
                return
            
            gitlab_issues_url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/issues"
            
            for issue in issues:
                if 'pull_request' in issue:
                    continue
                
                existing = requests.get(gitlab_issues_url, headers=self.gitlab_headers,
                                      params={'search': issue['title']})
                if existing.json():
                    continue
                
                labels = ','.join([label['name'] for label in issue.get('labels', [])])
                data = {
                    'title': f"[GitHub] {issue['title']}",
                    'description': f"{issue.get('body', '')}\n\n---\n*Synced from GitHub: {issue['html_url']}*",
                    'labels': labels
                }
                
                resp = requests.post(gitlab_issues_url, headers=self.gitlab_headers, json=data, timeout=API_TIMEOUT)
                if resp.status_code == 201:
                    print(f"  Synced issue: {issue['title']}")
                else:
                    print(f"  Warning: Failed to sync issue: {issue['title']}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def _sync_issues_to_github(self):
        """Copy issues from GitLab to GitHub"""
        if not GITHUB_REPO or not GITLAB_REPO:
            return
        
        print(f"Syncing issues: {GITLAB_REPO} -> {GITHUB_REPO}")
        
        try:
            gitlab_project_id = self._get_gitlab_project_id()
            if not gitlab_project_id:
                return
            
            url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/issues"
            response = requests.get(url, headers=self.gitlab_headers, params={'state': 'all'}, timeout=API_TIMEOUT)
            if response.status_code != 200:
                print(f"Error: Failed to get GitLab issues: {response.status_code}")
                return
            issues = response.json()
            
            github_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/issues"
            
            for issue in issues:
                if '[GitHub]' in issue.get('title', ''):
                    continue
                
                data = {
                    'title': f"[GitLab] {issue['title']}",
                    'body': f"{issue.get('description', '')}\n\n---\n*Synced from GitLab: {issue['web_url']}*",
                    'labels': issue.get('labels', [])
                }
                
                resp = requests.post(github_url, headers=self.github_headers, json=data)
                if resp.status_code == 201:
                    print(f"  Synced issue: {issue['title']}")
                else:
                    print(f"  Warning: Failed to sync issue: {issue['title']}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def _get_gitlab_project_id(self):
        """Get the GitLab project ID - needed for API calls"""
        try:
            url = f"{GITLAB_API_BASE}/projects/{GITLAB_REPO.replace('/', '%2F')}"
            response = requests.get(url, headers=self.gitlab_headers, timeout=API_TIMEOUT)
            if response.status_code == 200:
                return str(response.json()['id'])
        except Exception as e:
            print(f"Couldn't get project ID: {e}")
        return None


def main():
    print("Starting sync...")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if not GITHUB_TOKEN or not GITLAB_TOKEN:
        print("Warning: Tokens not set. Some operations won't work.")
        print("Set GITHUB_TOKEN and GITLAB_TOKEN env vars\n")
    
    if not GITHUB_REPO or not GITLAB_REPO:
        print("Error: Need GITHUB_REPO and GITLAB_REPO env vars")
        print("Format: username/repository")
        sys.exit(1)
    
    syncer = RepoSyncer()
    
    sync_type = sys.argv[1] if len(sys.argv) > 1 else 'code'
    direction = sys.argv[2] if len(sys.argv) > 2 else 'both'
    
    if sync_type == 'code':
        syncer.sync_code(direction)
    elif sync_type == 'issues':
        syncer.sync_issues(direction)
    elif sync_type == 'all':
        syncer.sync_code(direction)
        syncer.sync_issues(direction)
    else:
        print(f"Unknown sync type: '{sync_type}'")
        print("Usage: python sync_repos.py [code|issues|all] [both|github-to-gitlab|gitlab-to-github]")
    
    print("\nDone!")


if __name__ == '__main__':
    main()

