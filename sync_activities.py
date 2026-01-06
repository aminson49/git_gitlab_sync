#!/usr/bin/env python3
# Sync milestones, labels, comments etc between GitHub and GitLab
# This one's a bit experimental, might have bugs

import os
import sys
import requests
from datetime import datetime

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITLAB_REPO = os.getenv('GITLAB_REPO')
GITHUB_API_BASE = 'https://api.github.com'
GITLAB_API_BASE = os.getenv('GITLAB_API_BASE', 'https://gitlab.com/api/v4')


class ActivitySyncer:
    def __init__(self):
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
        
        self.gitlab_project_id = None
    
    def get_gitlab_project_id(self):
        """Get the GitLab project ID"""
        if self.gitlab_project_id:
            return self.gitlab_project_id
        
        try:
            url = f"{GITLAB_API_BASE}/projects/{GITLAB_REPO.replace('/', '%2F')}"
            response = requests.get(url, headers=self.gitlab_headers)
            if response.status_code == 200:
                self.gitlab_project_id = str(response.json()['id'])
                return self.gitlab_project_id
        except Exception as e:
            print(f"Error getting project ID: {e}")
        return None
    
    def sync_milestones(self):
        """Copy milestones from GitHub to GitLab"""
        print("📌 Syncing milestones...")
        
        gitlab_project_id = self.get_gitlab_project_id()
        if not gitlab_project_id:
            print("Need GitLab project ID")
            return
        
        try:
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/milestones"
            response = requests.get(url, headers=self.github_headers, params={'state': 'all'})
            if response.status_code != 200:
                print(f"Failed to get milestones: {response.status_code}")
                return
            milestones = response.json()
            
            gitlab_url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/milestones"
            
            for milestone in milestones:
                # Check if it already exists
                existing = requests.get(gitlab_url, headers=self.gitlab_headers,
                                      params={'search': milestone['title']})
                if existing.json():
                    continue
                
                # Create it
                due_date = None
                if milestone.get('due_on'):
                    due_date = milestone['due_on'][:10]  # Just the date part
                
                data = {
                    'title': milestone['title'],
                    'description': milestone.get('description', ''),
                    'due_date': due_date
                }
                
                resp = requests.post(gitlab_url, headers=self.gitlab_headers, json=data)
                if resp.status_code == 201:
                    print(f"  ✅ Synced milestone: {milestone['title']}")
                else:
                    print(f"  ⚠️  Failed: {milestone['title']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def sync_labels(self):
        """Copy labels from GitHub to GitLab"""
        print("🏷️  Syncing labels...")
        
        gitlab_project_id = self.get_gitlab_project_id()
        if not gitlab_project_id:
            return
        
        try:
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/labels"
            response = requests.get(url, headers=self.github_headers)
            if response.status_code != 200:
                print(f"Failed to get labels: {response.status_code}")
                return
            labels = response.json()
            
            gitlab_url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/labels"
            
            for label in labels:
                # Check if label already exists
                existing = requests.get(gitlab_url, headers=self.gitlab_headers,
                                      params={'search': label['name']})
                existing_labels = existing.json()
                if any(l['name'] == label['name'] for l in existing_labels):
                    continue
                
                # Create it
                color = label['color'].lstrip('#')  # GitLab doesn't want the #
                data = {
                    'name': label['name'],
                    'color': color,
                    'description': label.get('description', '')
                }
                
                resp = requests.post(gitlab_url, headers=self.gitlab_headers, json=data)
                if resp.status_code == 201:
                    print(f"  ✅ Synced label: {label['name']}")
                else:
                    print(f"  ⚠️  Failed: {label['name']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    def sync_comments(self, issue_number):
        """Copy comments for a specific issue"""
        print(f"💬 Syncing comments for issue #{issue_number}...")
        
        gitlab_project_id = self.get_gitlab_project_id()
        if not gitlab_project_id:
            return
        
        try:
            # Get comments from GitHub
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/issues/{issue_number}/comments"
            response = requests.get(url, headers=self.github_headers)
            if response.status_code != 200:
                print(f"Failed to get comments: {response.status_code}")
                return
            comments = response.json()
            
            # Find the matching GitLab issue
            gitlab_issues_url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/issues"
            gitlab_issues = requests.get(gitlab_issues_url, headers=self.gitlab_headers,
                                       params={'search': f'#{issue_number}'})
            
            if not gitlab_issues.json():
                print("Couldn't find matching GitLab issue")
                return
            
            gitlab_issue_iid = gitlab_issues.json()[0]['iid']
            gitlab_comments_url = f"{GITLAB_API_BASE}/projects/{gitlab_project_id}/issues/{gitlab_issue_iid}/notes"
            
            for comment in comments:
                data = {
                    'body': f"**{comment['user']['login']}** (from GitHub):\n\n{comment['body']}"
                }
                resp = requests.post(gitlab_comments_url, headers=self.gitlab_headers, json=data)
                if resp.status_code == 201:
                    print(f"  ✅ Synced comment from {comment['user']['login']}")
                else:
                    print(f"  ⚠️  Failed to sync comment")
        except Exception as e:
            print(f"  ❌ Error: {e}")


def main():
    print("🚀 Starting activity sync...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if not GITHUB_TOKEN or not GITLAB_TOKEN:
        print("❌ Need tokens set")
        sys.exit(1)
    
    if not GITHUB_REPO or not GITLAB_REPO:
        print("❌ Need repos set")
        sys.exit(1)
    
    syncer = ActivitySyncer()
    
    if len(sys.argv) > 1:
        activity_type = sys.argv[1]
        if activity_type == 'milestones':
            syncer.sync_milestones()
        elif activity_type == 'labels':
            syncer.sync_labels()
        elif activity_type == 'comments' and len(sys.argv) > 2:
            syncer.sync_comments(int(sys.argv[2]))
        else:
            print("Usage: python sync_activities.py [milestones|labels|comments <issue_number>]")
    else:
        # Default: sync milestones and labels
        syncer.sync_milestones()
        syncer.sync_labels()
    
    print("\n✅ Done!")


if __name__ == '__main__':
    main()

