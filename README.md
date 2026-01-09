# GitHub and GitLab Sync

Simple Python script to keep repos in sync between GitHub and GitLab. I built this because I needed to keep code synced between both platforms and couldn't find a good existing solution.

Works with regular GitHub/GitLab, GitHub Enterprise, and self-hosted GitLab.

## How It Works

The script syncs code from one repo to another. It handles protected branches, merge conflicts, and keeps history intact. GitHub is treated as the source of truth when syncing GitHub → GitLab.

## Setup Options

You can run this a few different ways:

1. **Jenkins** - Set it up on a server, triggers automatically on git push (what I'm using)
2. **GitLab CI/CD** - If your main repo is on GitLab, syncs to GitHub
3. **Cron/Task Scheduler** - Run it on a schedule locally
4. **Manual** - Just run the Python script when you need it
5. **GitHub Actions** - Manual trigger only (GitHub security prevents auto-runs)

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
