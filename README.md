# GitHub and GitLab Sync

Simple scripts to keep repos in sync between GitHub and GitLab. Works with regular GitHub/GitLab, GitHub Enterprise, and self-hosted GitLab instances.

## Options

There are a few ways to set this up depending on your needs:

1. **GitLab CI/CD** - Syncs GitLab → GitHub (if your main repo is on GitLab)
2. **Jenkins** - Syncs GitHub → GitLab (works great, I use this one)
3. **Cron/Task Scheduler** - Run the script on a schedule locally
4. **Python script** - Just run it manually when needed
5. **GitHub Actions** - Manual trigger only (GitHub doesn't let it auto-run for some reason)

## Quick Start

### GitLab CI/CD

If you're syncing from GitLab to GitHub:

1. Copy `.gitlab-ci.yml` to your GitLab repo
2. Go to Settings → CI/CD → Variables
3. Add `GITHUB_TOKEN` and `GITHUB_REPO_URL`
4. Push to GitLab and it should trigger the sync

### Local Python Script

The easiest way to test it:

```bash
pip install -r requirements.txt

export GITHUB_TOKEN="your_token"
export GITLAB_TOKEN="your_token"
export GITHUB_REPO="username/repo"
export GITLAB_REPO="username/repo"

python sync_repos.py code github-to-gitlab
```

## Getting Tokens

**GitHub:**
- Go to Settings → Developer settings → Personal access tokens → Tokens (classic)
- Make sure to check the `repo` scope, that's important

**GitLab:**
- Preferences → Access Tokens
- You need both `api` AND `write_repository` scopes (I learned this the hard way - just `api` isn't enough)

## Troubleshooting

**403 Forbidden:**
- GitLab token needs BOTH `api` AND `write_repository` scopes, not just one
- Double check the token owner actually has access to the repo

**Protected branch errors:**
- The script tries to handle this automatically by merging
- If it still fails, you might need to unprotect the branch temporarily or give your token permission to push to protected branches

**Repository not found:**
- Use the format `username/repo` (without .git or the full URL)
- Make sure your tokens actually have access to both repos

### GitHub Actions (Manual Only)

GitHub Actions won't auto-run for security reasons, so you have to trigger it manually:

1. Copy `.github/workflows/sync-to-gitlab.yml` to your GitHub repo
2. Settings → Secrets and variables → Actions
3. Add your secrets:
   - `GITLAB_TOKEN`
   - `GITHUB_REPO` (format: `username/repo`)
   - `GITLAB_REPO` (format: `username/repo`)
4. Go to Actions tab and manually run "Sync to GitLab"

For more detailed setup, check out [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Additional Guides

- **[JENKINS_SETUP.md](JENKINS_SETUP.md)** - How I set up Jenkins (works great for auto-syncing)
- **[CONFLICT_RESOLUTION_TESTING.md](CONFLICT_RESOLUTION_TESTING.md)** - Testing different conflict scenarios I've run into
