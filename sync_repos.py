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
        print(f"🔄 Syncing code ({direction})...")
        
        if direction in ['github-to-gitlab', 'both']:
            self._sync_to_gitlab()
        
        if direction in ['gitlab-to-github', 'both']:
            self._sync_to_github()
    
    def _sync_to_gitlab(self):
        """Push code from GitHub to GitLab"""
        if not GITHUB_REPO or not GITLAB_REPO:
            print("❌ Need to set GITHUB_REPO and GITLAB_REPO env vars")
            return
        
        print(f"📤 Syncing {GITHUB_REPO} → {GITLAB_REPO}")
        
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
            subprocess.run(['git', 'fetch', 'origin'], check=True)
            
            # Add gitlab remote (ignore error if it exists)
            subprocess.run(['git', 'remote', 'add', 'gitlab', gitlab_url], 
                         capture_output=True)
            subprocess.run(['git', 'remote', 'set-url', 'gitlab', gitlab_url])
            
            # Get all branches and push them
            result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
            branches = []
            for b in result.stdout.split('\n'):
                b = b.strip()
                if b and 'HEAD' not in b:
                    branches.append(b.replace('origin/', ''))
            
            for branch in branches:
                try:
                    subprocess.run(['git', 'checkout', branch], check=True, capture_output=True)
                    subprocess.run(['git', 'push', 'gitlab', branch], check=True)
                    print(f"  ✅ Synced branch: {branch}")
                except subprocess.CalledProcessError as e:
                    print(f"  ⚠️  Failed to sync branch {branch}: {e}")
            
            os.chdir('..')
            print("✅ Done syncing to GitLab")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _sync_to_github(self):
        """Push code from GitLab to GitHub"""
        if not GITHUB_REPO or not GITLAB_REPO:
            print("❌ Need to set GITHUB_REPO and GITLAB_REPO env vars")
            return
        
        print(f"📤 Syncing {GITLAB_REPO} → {GITHUB_REPO}")
        
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
                    print(f"  ✅ Synced branch: {branch}")
                except subprocess.CalledProcessError as e:
                    print(f"  ⚠️  Failed to sync branch {branch}: {e}")
            
            os.chdir('..')
            print("✅ Done syncing to GitHub")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def sync_issues(self, direction='both'):
        """Sync issues between the two platforms"""
        print(f"🔄 Syncing issues ({direction})...")
        
        if direction in ['github-to-gitlab', 'both']:
            self._sync_issues_to_gitlab()
        
        if direction in ['gitlab-to-github', 'both']:
            self._sync_issues_to_github()
    
    def _sync_issues_to_gitlab(self):
        """Copy issues from GitHub to GitLab"""
        if not GITHUB_REPO or not GITLAB_REPO:
            return
        
        print(f"📋 Syncing issues: {GITHUB_REPO} → {GITLAB_REPO}")
        
        try:
            # Fetch GitHub issues
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/issues"
            response = requests.get(url, headers=self.github_headers, params={'state': 'all'})
            if response.status_code != 200:
                print(f"❌ Failed to get GitHub issues: {response.status_code}")
                return
            issues = response.json()
            
            # Need GitLab project ID
            gitlab_project_id = self._get_gitlab_project_id()
            if not gitlab_project_id:
                print("❌ Couldn't find GitLab project")
                return
            
            gitlab_issues_url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/issues"
            
            for issue in issues:
                # Skip pull requests
                if 'pull_request' in issue:
                    continue
                
                # Check if we already have this issue
                existing = requests.get(gitlab_issues_url, headers=self.gitlab_headers,
                                      params={'search': issue['title']})
                if existing.json():
                    continue  # Already exists
                
                # Create it in GitLab
                labels = ','.join([label['name'] for label in issue.get('labels', [])])
                data = {
                    'title': f"[GitHub] {issue['title']}",
                    'description': f"{issue.get('body', '')}\n\n---\n*Synced from GitHub: {issue['html_url']}*",
                    'labels': labels
                }
                
                resp = requests.post(gitlab_issues_url, headers=self.gitlab_headers, json=data)
                if resp.status_code == 201:
                    print(f"  ✅ Synced issue: {issue['title']}")
                else:
                    print(f"  ⚠️  Failed to sync issue: {issue['title']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _sync_issues_to_github(self):
        """Copy issues from GitLab to GitHub"""
        if not GITHUB_REPO or not GITLAB_REPO:
            return
        
        print(f"📋 Syncing issues: {GITLAB_REPO} → {GITHUB_REPO}")
        
        try:
            gitlab_project_id = self._get_gitlab_project_id()
            if not gitlab_project_id:
                return
            
            # Get GitLab issues
            url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/issues"
            response = requests.get(url, headers=self.gitlab_headers, params={'state': 'all'})
            if response.status_code != 200:
                print(f"❌ Failed to get GitLab issues: {response.status_code}")
                return
            issues = response.json()
            
            github_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/issues"
            
            for issue in issues:
                # Skip ones we already synced from GitHub
                if '[GitHub]' in issue.get('title', ''):
                    continue
                
                # Create in GitHub
                data = {
                    'title': f"[GitLab] {issue['title']}",
                    'body': f"{issue.get('description', '')}\n\n---\n*Synced from GitLab: {issue['web_url']}*",
                    'labels': issue.get('labels', [])
                }
                
                resp = requests.post(github_url, headers=self.github_headers, json=data)
                if resp.status_code == 201:
                    print(f"  ✅ Synced issue: {issue['title']}")
                else:
                    print(f"  ⚠️  Failed to sync issue: {issue['title']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
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
    print("🚀 Starting sync...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if we have tokens
    if not GITHUB_TOKEN or not GITLAB_TOKEN:
        print("⚠️  Warning: Tokens not set. Some stuff won't work.")
        print("Set GITHUB_TOKEN and GITLAB_TOKEN env vars\n")
    
    if not GITHUB_REPO or not GITLAB_REPO:
        print("❌ Need GITHUB_REPO and GITLAB_REPO env vars")
        print("Format: username/repository")
        sys.exit(1)
    
    syncer = RepoSyncer()
    
    # Parse args
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
        print(f"Don't know what '{sync_type}' means")
        print("Usage: python sync_repos.py [code|issues|all] [both|github-to-gitlab|gitlab-to-github]")
    
    print("\n✅ Done!")


if __name__ == '__main__':
    main()

