# GitHub and GitLab Sync

Simple Python script to keep repos in sync between GitHub and GitLab. I built this because I needed to keep code synced between both platforms and couldn't find a good existing solution.

Works with regular GitHub/GitLab, GitHub Enterprise, and self-hosted GitLab.

## How It Works

The script syncs code from one repo to another. It handles protected branches, merge conflicts, and keeps history intact. GitHub is treated as the source of truth when syncing GitHub → GitLab.

### Merge Conflict Resolution

When branches have diverged or there are merge conflicts, the script handles them automatically:

1. **Detection**: When a push fails due to diverged branches or protected branch rules, the script detects this and starts conflict resolution.

2. **Strategy**: Since GitHub is the source of truth, the script always keeps GitHub's version of files when conflicts occur.

3. **Process**:
   - Fetches the latest from both GitHub and GitLab
   - Resets to match GitHub exactly
   - Merges GitLab's branch using `-X ours` strategy (automatically keeps GitHub's version)
   - If conflicts still occur, explicitly resolves them by:
     - Detecting conflicted files using `git diff --diff-filter=U`
     - For each conflicted file, using `git checkout --ours` to keep GitHub's version
     - Staging and committing the resolved files
   - Ensures final state matches GitHub exactly
   - Pushes the merged result to GitLab

4. **Result**: GitLab gets updated with GitHub's code, but GitLab's commit history is preserved through merge commits. This way you don't lose any history from either side.

This approach ensures that even if someone makes changes directly on GitLab, those changes won't overwrite what's on GitHub - GitHub always wins in conflicts.

## Setup Options

You can run this a few different ways:

1. **Jenkins** - Set it up on a server, triggers automatically on git push (what I'm using)
2. **GitLab CI/CD** - If your main repo is on GitLab, syncs to GitHub automatically on push
3. **CircleCI** - Syncs GitHub → GitLab automatically on push
4. **Cron/Task Scheduler** - Run it on a schedule locally
5. **Manual** - Just run the Python script when you need it
6. **GitHub Actions** - Manual trigger only (GitHub security prevents auto-runs)

## Quick Test

Easiest way to test it locally:

```bash
pip install -r requirements.txt

export GITHUB_TOKEN="your_token"
export GITLAB_TOKEN="your_token"
export GITHUB_REPO="aminson49/git_gitlab_sync"
export GITLAB_REPO="poc-group1603702/gitlab_github_sync"

python sync_repos.py code github-to-gitlab
```

## Getting Tokens

**GitHub:**
- Settings → Developer settings → Personal access tokens → Tokens (classic)
- Need the `repo` scope

**GitLab:**
- Preferences → Access Tokens
- Need both `api` AND `write_repository` scopes (just `api` won't work - found that out the hard way)

## Common Problems

**403 Forbidden:**
- Make sure your GitLab token has both `api` AND `write_repository` scopes
- Check the token owner has access to the repo

**Protected branch errors:**
- Script tries to handle this by merging automatically
- If it still fails, you might need to temporarily unprotect the branch or give your token permission to push to protected branches

**Repository not found:**
- Use format `username/repo` (no .git, no full URL)
- Make sure tokens have access to both repos

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for more detailed setup instructions.

## CircleCI Setup

You can also use CircleCI to sync GitHub → GitLab automatically on push:

1. Copy `.circleci/config.yml` to your GitHub repo (in `.circleci/` directory)
2. Go to CircleCI → Your Project → Settings → Environment Variables
3. Add these environment variables:
   - `GITHUB_TOKEN` - Your GitHub personal access token
   - `GITLAB_TOKEN` - Your GitLab access token
   - `GITHUB_REPO` - Format: `username/repo`
   - `GITLAB_REPO` - Format: `username/repo`
   - `GITLAB_API_BASE` (optional) - Only if using self-hosted GitLab, default is `https://gitlab.com/api/v4`
4. Push to GitHub and CircleCI will automatically sync to GitLab

The CircleCI workflow triggers on pushes to the `main` branch. You can modify the branch filter in `.circleci/config.yml` if needed.
