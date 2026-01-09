# GitHub and GitLab Sync.

Scripts to keep repos in sync between GitHub and GitLab. Works with regular GitHub/GitLab, GitHub Enterprise, and self-hosted GitLab.

## Options

1. **GitLab CI/CD** - Syncs GitLab → GitHub
2. **CircleCI** - Syncs GitHub → GitLab (recommended, no server needed)
3. **Jenkins** - Syncs GitHub → GitLab
4. **Cron/Task Scheduler** - Run script on schedule
5. **Python script** - Run manually
6. **GitHub Actions** - Manual trigger only (no auto-run)

## Quick Start

### CircleCI (Easiest - No Server Needed)

1. Sign up at [circleci.com](https://circleci.com) and add your GitHub repo
2. Add environment variables in Project Settings:
   - `GITHUB_TOKEN` - GitHub personal access token (repo scope)
   - `GITLAB_TOKEN` - GitLab access token (api + write_repository scopes)
   - `GITHUB_REPO` - Format: `username/repo` (no .git)
   - `GITLAB_REPO` - Format: `username/repo` (no .git)
3. Copy `.circleci/config.yml` to your repo
4. Push to GitHub - it will sync automatically

### GitLab CI/CD

1. Copy `.gitlab-ci.yml` to your GitLab repo
2. Settings → CI/CD → Variables
3. Add `GITHUB_TOKEN` and `GITHUB_REPO_URL`
4. Push to GitLab and trigger the sync job

### Local Python Script

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
- Settings → Developer settings → Personal access tokens → Tokens (classic)
- Need `repo` scope

**GitLab:**
- Preferences → Access Tokens
- Need `api` and `write_repository` scopes

## Troubleshooting

**403 Forbidden:**
- Make sure GitLab token has both `api` AND `write_repository` scopes
- Verify token owner has access to the repository

**Protected branch errors:**
- Script automatically merges for protected branches
- If it still fails, unprotect the branch or give token permission

**Repository not found:**
- Check repo format: `username/repo` (not `https://github.com/username/repo.git`)
- Verify tokens have access to the repositories

### GitHub Actions (Manual Only)

1. Copy `.github/workflows/sync-to-gitlab.yml` to your GitHub repo
2. Settings → Secrets and variables → Actions
3. Add secrets:
   - `GITLAB_TOKEN` - your GitLab token
   - `GITHUB_REPO` - format: `username/repo`
   - `GITLAB_REPO` - format: `username/repo`
4. Go to Actions tab and click "Sync to GitLab" → "Run workflow"

Note: This workflow is manual only - it won't run automatically on push.

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.
