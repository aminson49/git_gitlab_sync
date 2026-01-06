#!/usr/bin/env python3
# Quick script to sync repos between GitHub and GitLab
# Works for code and issues, might add more later

import os
import subprocess
import sys
import json
import requests
from datetime import datetime

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
                subprocess.run(['git', 'clone', github_url, '.github_repo'], check=True)
            
            os.chdir('.github_repo')
            
            # Set git user config for commits (needed for merges)
            subprocess.run(['git', 'config', 'user.email', 'aminpriyam2499@gmail.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'Priyam Amin'], check=True)
            
            subprocess.run(['git', 'fetch', 'origin'], check=True)
            
            # Add gitlab remote (ignore error if it exists)
            subprocess.run(['git', 'remote', 'add', 'gitlab', gitlab_url], 
                         capture_output=True)
            subprocess.run(['git', 'remote', 'set-url', 'gitlab', gitlab_url])
            
            # Fetch from GitLab to see what's there
            print("Fetching from GitLab to check for conflicts...")
            subprocess.run(['git', 'fetch', 'gitlab'], capture_output=True)
            
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
                        reset_result = subprocess.run(
                            ['git', 'reset', '--hard', f'origin/{branch}'], 
                            capture_output=True, text=True, check=False
                        )
                        if reset_result.returncode != 0:
                            print(f"  Warning: Could not reset branch {branch}: {reset_result.stderr}")
                            continue
                    
                    gitlab_branch_exists = subprocess.run(
                        ['git', 'ls-remote', '--heads', 'gitlab', branch],
                        capture_output=True, text=True
                    ).stdout.strip()
                    
                    result = subprocess.run(['git', 'push', 'gitlab', branch], 
                                          capture_output=True, text=True, check=False)
                    
                    if result.returncode == 0:
                        print(f"  Synced branch: {branch}")
                    else:
                        error_msg = result.stderr or result.stdout
                        is_protected = 'protected branch' in error_msg or 'not allowed to force push' in error_msg
                        is_diverged = 'rejected' in error_msg and ('fetch first' in error_msg or 'non-fast-forward' in error_msg)
                        
                        if is_protected or is_diverged:
                            print(f"  Branch {branch} needs merge (protected or diverged)")
                            
                            if gitlab_branch_exists:
                                print(f"     Merging GitLab's changes into local branch...")
                                subprocess.run(['git', 'fetch', 'gitlab', branch], capture_output=True)
                                
                                merge_result = subprocess.run(
                                    ['git', 'merge', f'gitlab/{branch}', '--no-edit', '--no-ff', '--allow-unrelated-histories', '-X', 'ours'],
                                    capture_output=True, text=True, check=False
                                )
                                
                                if merge_result.returncode != 0:
                                    print(f"     Merge had conflicts, using GitHub version...")
                                    subprocess.run(['git', 'merge', '--abort'], capture_output=True)
                                    merge_result = subprocess.run(
                                        ['git', 'merge', f'gitlab/{branch}', '--no-edit', '--no-ff', '--allow-unrelated-histories', '-X', 'ours'],
                                        capture_output=True, text=True, check=False
                                    )
                                
                                if merge_result.returncode == 0:
                                    print(f"     Merge successful, pushing to GitLab...")
                                    push_result = subprocess.run(
                                        ['git', 'push', 'gitlab', branch],
                                        capture_output=True, text=True, check=False
                                    )
                                    if push_result.returncode == 0:
                                        print(f"  Synced branch: {branch} (merged and pushed)")
                                    else:
                                        push_error = push_result.stderr or push_result.stdout
                                        if 'protected branch' in push_error:
                                            print(f"  Error: Cannot sync branch {branch} - it's protected")
                                            print(f"     Unprotect the branch in GitLab or give token permission")
                                        else:
                                            print(f"  Warning: Push failed after merge: {push_error[:200]}")
                                else:
                                    print(f"  Warning: Could not merge GitLab changes: {merge_result.stderr[:200]}")
                            else:
                                if is_protected:
                                    print(f"  Error: Cannot create protected branch {branch}")
                                else:
                                    print(f"  Warning: Push failed: {error_msg[:200]}")
                        elif 'deny updating a hidden ref' in error_msg:
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
                subprocess.run(['git', 'clone', gitlab_url, '.gitlab_repo'], check=True)
            
            os.chdir('.gitlab_repo')
            
            # Set git user config for commits (needed for merges)
            subprocess.run(['git', 'config', 'user.email', 'aminpriyam2499@gmail.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'Priyam Amin'], check=True)
            
            subprocess.run(['git', 'fetch', 'origin'], check=True)
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
                    subprocess.run(['git', 'push', 'github', branch], check=True)
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
            response = requests.get(url, headers=self.github_headers, params={'state': 'all'})
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
                
                resp = requests.post(gitlab_issues_url, headers=self.gitlab_headers, json=data)
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
            response = requests.get(url, headers=self.gitlab_headers, params={'state': 'all'})
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
            response = requests.get(url, headers=self.gitlab_headers)
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

