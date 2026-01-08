# Setup Guide

## Get Your Tokens

### GitHub Token

1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Name it "gitlab-sync"
4. Check `repo` scope
5. Copy the token

### GitLab Token

1. Go to GitLab → Preferences → Access Tokens
2. Name it "github-sync"
3. Check `api` and `write_repository` scopes
4. Copy the token

## GitLab CI Setup

1. Copy `.gitlab-ci.yml` to your GitLab repo
2. Settings → CI/CD → Variables
3. Add `GITHUB_TOKEN` and `GITHUB_REPO_URL`
4. Push to GitLab and trigger the sync job

## GitHub Actions Setup

1. Copy `.github/workflows/sync-to-gitlab.yml` to your GitHub repo
2. Settings → Secrets and variables → Actions
3. Add secrets:
   - `GITLAB_TOKEN` - your GitLab token
   - `GITHUB_REPO` - format: `username/repo`
   - `GITLAB_REPO` - format: `username/repo`
4. Go to Actions tab → "Sync to GitLab" → "Run workflow"

Note: This workflow is manual only - it won't run automatically on push.

## Jenkins Setup

See [JENKINS_SETUP.md](JENKINS_SETUP.md) for detailed instructions on setting up Jenkins (hosted or self-hosted).

## Cron/Scheduled Tasks

**Windows:**
Create `sync.bat`:
```batch
cd /d F:\priyam\git_gitlab_sync
set GITHUB_TOKEN=your_token
set GITLAB_TOKEN=your_token
set GITHUB_REPO=username/repo
set GITLAB_REPO=username/repo
python sync_repos.py code github-to-gitlab
```
Add to Task Scheduler.

**Linux/Mac:**
```bash
crontab -e
# Add:
*/15 * * * * cd /path/to/git_gitlab_sync && GITHUB_TOKEN=token GITLAB_TOKEN=token GITHUB_REPO=user/repo GITLAB_REPO=user/repo python3 sync_repos.py code github-to-gitlab >> /var/log/gitlab-sync.log 2>&1
```

## Common Issues

**403 Forbidden:**
- GitLab token needs both `api` AND `write_repository` scopes
- Verify token owner has repository access

**Protected branch errors:**
- Script handles this automatically by merging
- If it fails, unprotect branch or give token permission

**Repository not found:**
- Use format `username/repo`, not full URL
- Check tokens have access
