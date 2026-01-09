# Jenkins and Python Sync Setup

Quick notes on how the Jenkins pipeline and Python sync script work together.

## Jenkinsfile

This is the Jenkins pipeline config. It runs automatically when you push to GitHub (webhook) or every 15 minutes as backup.

Basically it does:
1. Checks out the code from GitHub
2. Creates a Python venv and installs dependencies
3. Runs the sync script

The environment variables come from Jenkins credentials:
- `GITHUB_TOKEN` and `GITLAB_TOKEN` from credentials with IDs `github-token` and `gitlab-token`
- `GITHUB_REPO` is hardcoded to `aminson49/git_gitlab_sync`
- `GITLAB_REPO` is hardcoded to `poc-group1603702/gitlab_github_sync`

I use a virtual environment because newer Python versions complain about "externally-managed-environment" if you try to install packages system-wide. After each run Jenkins cleans up the workspace.

## sync_repos.py

This is the actual sync script. It does all the git operations and handles conflicts.

The script reads tokens and repo names from environment variables, sets up API headers for GitHub/GitLab, and can sync code or issues (or both).

### How it syncs code (GitHub → GitLab)

First it clones the GitHub repo if needed (into `.github_repo` directory), or just fetches if it already exists. Then it finds all branches from GitHub (ignores GitLab branches).

For each branch:
- Checks out the branch
- Resets to match GitHub exactly (GitHub is source of truth)
- Tries to push to GitLab

If the push fails (protected branch or branches diverged), it:
- Fetches latest from GitLab
- Resets to GitHub version again
- Merges GitLab's branch using `-X ours` strategy (keeps GitHub's files)
- If conflicts still happen, it finds all conflicted files and uses `git checkout --ours` to keep GitHub's version for each one
- Makes sure final state matches GitHub exactly
- Pushes the merged result

### Conflict resolution

The script handles merge conflicts automatically by always keeping GitHub's version. When branches diverge, it detects the conflict, merges GitLab's branch but keeps GitHub's files using `-X ours`. If that doesn't work, it explicitly finds all files with conflicts (`git diff --diff-filter=U`), runs `git checkout --ours` on each one to keep GitHub's version, stages and commits everything.

Final result: GitLab gets GitHub's code, but GitLab's commit history is preserved through merge commits. So you don't lose history from either side, but GitHub always wins when there are conflicts.

### Other stuff

- Skip sync commits: If a commit message has `[skip sync]`, the script won't create infinite loops
- Protected branches: Handles them by merging instead of force pushing
- Multiple branches: Syncs all branches, not just main
- Issue syncing: Can sync issues too but I mostly use it for code

## How they work together

You push code to GitHub → GitHub webhook triggers Jenkins (or Jenkins polls every 15 min) → Jenkins checks out code, sets up Python environment → Jenkins runs `sync_repos.py code github-to-gitlab` → Script syncs everything to GitLab, handling conflicts automatically → Jenkins cleans up.

It's all automated - just push to GitHub and GitLab gets updated.

## Environment variables

In Jenkins you need these credentials:
- `github-token` (Secret text) - GitHub personal access token
- `gitlab-token` (Secret text) - GitLab access token with `api` and `write_repository` scopes

Repo names are hardcoded in the Jenkinsfile, change them there if needed.

## Troubleshooting

If script fails with "externally-managed-environment": The Jenkinsfile handles this with a virtual environment.

Merge conflicts: Script handles them automatically by keeping GitHub's version. If you see conflict messages in logs, that's normal - it's resolving them.

Push fails: Check tokens have right permissions, make sure branch names match on both sides. Protected branches are handled automatically but might need token permissions.

Infinite sync loops: Script checks for `[skip sync]` in commit messages. Sync commits are marked with this to prevent loops.

## Code walkthrough

Here's what the Python script does, section by section:

### Imports and setup

```python
#!/usr/bin/env python3
```
Just tells the system to use Python 3.

```python
import os, subprocess, sys, json, requests
from datetime import datetime
```
- `os` for environment variables and file stuff
- `subprocess` to run git commands
- `sys` for command line args
- `json` for API responses
- `requests` for HTTP calls to GitHub/GitLab APIs
- `datetime` for timestamps

```python
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITHUB_REPO = os.getenv('GITHUB_REPO')
GITLAB_REPO = os.getenv('GITLAB_REPO')
```
Gets tokens and repo names from environment. Repo format is `username/repo` (no .git, no full URL).

```python
GITHUB_API_BASE = 'https://api.github.com'
GITLAB_API_BASE = os.getenv('GITLAB_API_BASE', 'https://gitlab.com/api/v4')
```
API base URLs. Defaults to public GitHub/GitLab but you can change for enterprise.

### RepoSyncer class

```python
class RepoSyncer:
    def __init__(self):
        if GITHUB_TOKEN:
            self.github_headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
```
Sets up HTTP headers for GitHub API. GitHub uses `token` prefix in Authorization header.

```python
if GITLAB_TOKEN:
    self.gitlab_headers = {'PRIVATE-TOKEN': GITLAB_TOKEN}
```
GitLab uses `PRIVATE-TOKEN` header (different from GitHub).

### Main sync function

```python
def sync_code(self, direction='both'):
```
Main entry point. Direction can be 'github-to-gitlab', 'gitlab-to-github', or 'both'.

### Syncing to GitLab

```python
def _sync_to_gitlab(self):
```
This is where the main sync happens.

```python
if GITHUB_TOKEN:
    github_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
```
Builds GitHub URL with token embedded. Format is `https://TOKEN@github.com/user/repo.git`.

```python
if GITLAB_TOKEN:
    gitlab_url = f"https://oauth2:{GITLAB_TOKEN}@gitlab.com/{GITLAB_REPO}.git"
```
GitLab uses `oauth2:` prefix before the token.

```python
if not os.path.exists('.github_repo'):
    subprocess.run(['git', 'clone', github_url, '.github_repo'], check=True)
```
Only clones if it doesn't exist (saves time on later runs). Creates hidden directory `.github_repo` to work in.

```python
os.chdir('.github_repo')
subprocess.run(['git', 'config', 'user.email', 'aminpriyam2499@gmail.com'], check=True)
subprocess.run(['git', 'config', 'user.name', 'Priyam Amin'], check=True)
```
Changes into the repo and sets git user info (needed for commits during merges).

```python
subprocess.run(['git', 'fetch', 'origin'], check=True)
```
Fetches latest from GitHub (origin = GitHub remote).

```python
subprocess.run(['git', 'remote', 'add', 'gitlab', gitlab_url], capture_output=True)
subprocess.run(['git', 'remote', 'set-url', 'gitlab', gitlab_url])
```
Adds GitLab as remote named 'gitlab'. `capture_output=True` ignores error if remote already exists. `set-url` updates it if it exists.

```python
subprocess.run(['git', 'fetch', 'gitlab'], capture_output=True)
```
Fetches from GitLab to see what's there (for conflict detection).

### Finding branches

```python
result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
branches = []
for b in result.stdout.split('\n'):
    b = b.strip()
    if b and 'HEAD' not in b and b.startswith('origin/'):
        branch_name = b.replace('origin/', '')
        if branch_name and not branch_name.startswith('gitlab/'):
            branches.append(branch_name)
```
Lists all remote branches. Only takes branches from `origin/` (GitHub), ignores `gitlab/` branches. Skips HEAD (not a real branch). Extracts branch name by removing `origin/` prefix.

### Processing each branch

```python
for branch in branches:
    local_branch_check = subprocess.run(['git', 'branch', '--list', branch], ...)
    if not local_branch_check.stdout.strip():
        subprocess.run(['git', 'checkout', '-b', branch, f'origin/{branch}'], ...)
```
Loops through each branch. Checks if local branch exists, creates it from GitHub if not.

```python
subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], ...)
```
Important: Resets branch to match GitHub exactly. `--hard` discards any local changes. This ensures GitHub is always the source of truth.

```python
gitlab_branch_exists = subprocess.run(['git', 'ls-remote', '--heads', 'gitlab', branch], ...)
```
Checks if branch exists on GitLab without cloning. `ls-remote` queries remote without downloading.

### Simple push

```python
result = subprocess.run(['git', 'push', 'gitlab', branch], ...)
if result.returncode == 0:
    verify_push = subprocess.run(['git', 'ls-remote', '--heads', 'gitlab', branch], ...)
```
Tries to push to GitLab. `returncode == 0` means success. Verifies push actually worked by checking if branch exists on GitLab - sometimes push reports success but fails silently.

### Conflict detection

```python
error_msg = result.stderr or result.stdout
is_protected = 'protected branch' in error_msg or 'not allowed to force push' in error_msg
is_diverged = 'rejected' in error_msg and ('fetch first' in error_msg or 'non-fast-forward' in error_msg)
```
Checks error message to figure out why push failed. `is_protected` means branch protection rules are blocking push. `is_diverged` means branches have different commits (can't fast-forward).

### Conflict resolution

```python
if is_protected or is_diverged:
    subprocess.run(['git', 'fetch', 'gitlab', branch], capture_output=True)
    subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], capture_output=True)
```
Enters conflict resolution mode. Fetches latest from GitLab, resets to GitHub version again (ensures clean state).

```python
github_files_result = subprocess.run(['git', 'ls-tree', '-r', '--name-only', 'HEAD'], ...)
github_files = set()
for line in github_files_result.stdout.strip().split('\n'):
    if line.strip():
        github_files.add(line.strip())
```
Gets list of all files in GitHub version. Stores in a set for easy comparison later. `ls-tree` lists files in git tree without checking out.

```python
subprocess.run(['git', 'rm', '-rf', '--ignore-unmatch', '.'], capture_output=True)
subprocess.run(['git', 'checkout', 'HEAD', '--', '.'], capture_output=True)
subprocess.run(['git', 'add', '-A'], capture_output=True)
subprocess.run(['git', 'commit', '-m', f'Sync from GitHub - exact match [skip sync]'], ...)
```
Removes all files from git index, checks out all files from current HEAD (GitHub version), stages everything. This creates a clean commit matching GitHub exactly. The `[skip sync]` tag prevents infinite loops.

```python
subprocess.run(['git', 'merge', f'gitlab/{branch}', '--no-edit', '--no-ff', '--allow-unrelated-histories', '-X', 'ours'], ...)
```
Merges GitLab's branch. `--no-edit` uses default merge message, `--no-ff` always creates merge commit (preserves history), `--allow-unrelated-histories` allows merging branches with no common ancestor, `-X ours` keeps our version (GitHub) when conflicts occur.

If merge fails:

```python
if merge_result.returncode != 0:
    conflict_check = subprocess.run(['git', 'status', '--porcelain'], ...)
    if 'CONFLICT' in merge_output or 'conflict' in merge_output.lower() or '<<<<<<<' in conflict_check.stdout:
```
Checks if we're in conflict state. `--porcelain` gives machine-readable status. Looks for conflict markers (`<<<<<<<`) in files.

```python
subprocess.run(['git', 'merge', '--abort'], capture_output=True, check=False)
subprocess.run(['git', 'reset', '--hard', f'origin/{branch}'], capture_output=True)
```
Aborts the failed merge, resets back to GitHub version.

```python
conflicted_files = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=U'], ...)
for file in conflicted_files.stdout.strip().split('\n'):
    if file.strip():
        subprocess.run(['git', 'checkout', '--ours', file.strip()], ...)
        subprocess.run(['git', 'add', file.strip()], capture_output=True)
```
Gets list of unmerged (conflicted) files. `--diff-filter=U` shows only unmerged files. For each conflicted file, `--ours` keeps our version (GitHub's version), then stages the resolved file.

```python
subprocess.run(['git', 'commit', '-m', f'Merge GitLab branch - resolved conflicts by keeping GitHub version [skip sync]'], ...)
merge_result.returncode = 0  # Mark as successful
```
Commits the resolved conflicts. Manually sets returncode to 0 to mark as success.

### Ensuring exact match

After merge, we need to make sure files match GitHub exactly:

```python
current_files_result = subprocess.run(['git', 'ls-files'], ...)
current_files = set()
for line in current_files_result.stdout.strip().split('\n'):
    if line.strip():
        current_files.add(line.strip())
```
Gets list of all files currently tracked by git.

```python
for file in current_files:
    subprocess.run(['git', 'rm', '--cached', '--ignore-unmatch', file], capture_output=True)
subprocess.run(['git', 'clean', '-fd'], capture_output=True)
subprocess.run(['git', 'checkout', f'origin/{branch}', '--', '.'], capture_output=True)
```
Removes all files from git index (but keeps them on disk). `--cached` removes from index only, not filesystem. `--ignore-unmatch` doesn't error if file doesn't exist. Removes untracked files and directories. Checks out all files from GitHub version. `--` separates paths from branch name, `.` means all files.

```python
extra_files = files_after - github_files
if extra_files:
    for file in extra_files:
        subprocess.run(['git', 'rm', '--cached', '--ignore-unmatch', file], capture_output=True)
        if os.path.exists(file):
            os.remove(file)
```
Finds files that exist but aren't in GitHub. Removes them from git and filesystem. Set subtraction (`files_after - github_files`) finds the difference.

```python
subprocess.run(['git', 'add', '-A'], capture_output=True)
final_status = subprocess.run(['git', 'status', '--porcelain'], ...)
if final_status.stdout.strip():
    subprocess.run(['git', 'commit', '-m', f'Sync from GitHub - ensure exact match [skip sync]'], ...)
```
Stages all changes. Checks if there are any changes, creates commit only if needed.

### Checking for more commits

```python
behind_check = subprocess.run(['git', 'rev-list', '--left-right', '--count', f'HEAD...gitlab/{branch}'], ...)
behind_ahead = behind_check.stdout.strip().split()
behind = int(behind_ahead[0])
ahead = int(behind_ahead[1])
```
Compares commits between HEAD and GitLab branch. `--left-right` shows commits on left (HEAD) and right (GitLab), `--count` gives numbers instead of commit hashes. Returns two numbers: commits behind, commits ahead.

```python
if behind > 0:
    merge_again = subprocess.run(['git', 'merge', f'gitlab/{branch}', '--no-edit', '--no-ff', '-X', 'ours'], ...)
```
If there are more commits on GitLab, merge again. This handles cases where GitLab had multiple commits.

If conflicts in second merge:

```python
if 'UU' in conflict_check.stdout or 'AA' in conflict_check.stdout:
    conflicted_files = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=U'], ...)
    for file in conflicted_files.stdout.strip().split('\n'):
        if file.strip():
            subprocess.run(['git', 'checkout', '--ours', file.strip()], ...)
            subprocess.run(['git', 'add', file.strip()], capture_output=True)
```
Checks git status for conflict indicators. `UU` = both modified (unmerged), `AA` = both added (unmerged). Resolves conflicts same way as before.

### Final push

```python
push_result = subprocess.run(['git', 'push', 'gitlab', branch], ...)
if push_result.returncode == 0:
    print(f"  Synced branch: {branch} (merged and pushed)")
else:
    push_error = push_result.stderr or push_result.stdout
    if 'protected branch' in push_error:
        print(f"     Branch is protected - unprotect it or give token permission")
```
Pushes merged result to GitLab. Provides helpful error messages based on error type.

### Main function

```python
def main():
    print("Starting sync...")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
```
Entry point when script is run directly. Prints timestamp.

```python
if not GITHUB_TOKEN or not GITLAB_TOKEN:
    print("Warning: Tokens not set. Some operations won't work.")
if not GITHUB_REPO or not GITLAB_REPO:
    print("Error: Need GITHUB_REPO and GITLAB_REPO env vars")
    sys.exit(1)
```
Warns if tokens missing (but continues). Exits if repo names not set (required).

```python
sync_type = sys.argv[1] if len(sys.argv) > 1 else 'code'
direction = sys.argv[2] if len(sys.argv) > 2 else 'both'
```
Gets command line arguments. `sys.argv[1]` is first argument (sync type: code, issues, or all). `sys.argv[2]` is second argument (direction: github-to-gitlab, gitlab-to-github, or both). Defaults are 'code' and 'both'.

```python
if sync_type == 'code':
    syncer.sync_code(direction)
elif sync_type == 'issues':
    syncer.sync_issues(direction)
elif sync_type == 'all':
    syncer.sync_code(direction)
    syncer.sync_issues(direction)
```
Calls appropriate sync function based on arguments.

```python
if __name__ == '__main__':
    main()
```
Only runs main() if script is executed directly (not imported). Standard Python pattern.

## Why it works this way

**Why all the file manipulation?**
Git tracks files in the "index" (staging area). To ensure exact match with GitHub, we need to remove all files from index, checkout files from GitHub, remove any extra files, stage everything, then commit.

**Why merge instead of force push?**
Preserves GitLab's commit history. Protected branches don't allow force push. Merge commits show the sync happened.

**Why `[skip sync]`?**
Prevents infinite loops. When script creates a commit and pushes, that push could trigger Jenkins again. `[skip sync]` tells the script to skip syncing that commit.

**Error handling:**
Most git commands use `check=False` so script continues on error. Errors are caught and printed, but script tries to continue. Final push errors are reported with helpful messages.
