# Syncing GitHub and GitLab repos

I got tired of manually keeping my repos in sync between GitHub and GitLab, so I threw together some scripts to automate it. Sharing in case anyone else needs this.

Works with regular GitHub/GitLab, GitHub Enterprise, self-hosted GitLab, whatever. Just need the right URLs and tokens.

## What's here

There's a few different ways to sync stuff:

1. **GitLab CI/CD** - pushes from GitLab to GitHub when you commit
2. **GitHub Actions** - pushes from GitHub to GitLab when you commit  
3. **Python script** - run it manually whenever you want
4. **GitLab mirroring** - built-in feature but it's one-way only

## Quick setup

**See [SETUP_GUIDE.md](SETUP_GUIDE.md) for the full walkthrough**

### GitLab CI (pushes to GitHub)

1. Copy `.gitlab-ci.yml` to your GitLab repo root
2. Settings → CI/CD → Variables
3. Add `GITHUB_TOKEN` (your GitHub token)
4. Add `GITHUB_REPO_URL` like `https://github.com/username/repo.git` (or your GitHub Enterprise URL)
5. Push to GitLab, then manually trigger the sync job (or change `when: manual` to `when: on_success`)

### GitHub Actions (pushes to GitLab)

1. Copy `.github/workflows/sync-to-gitlab.yml` to your GitHub repo (create `.github/workflows/` folder if needed)
2. Settings → Secrets → Actions
3. Add `GITLAB_TOKEN` (your GitLab token)
4. Add `GITLAB_REPO_URL` like `https://gitlab.com/username/repo.git` (or your GitLab instance URL)
5. Push to GitHub - it'll automatically sync to GitLab!

### Local Python script

Install deps:
```bash
pip install -r requirements.txt
```

Set env vars (PowerShell):
```powershell
$env:GITHUB_TOKEN="your_token"
$env:GITLAB_TOKEN="your_token"
$env:GITHUB_REPO="username/repo"
$env:GITLAB_REPO="username/repo"
```

Run it:
```bash
python sync_repos.py
```

You can also do `python sync_repos.py issues` to sync issues, or `python sync_repos.py all` for everything.

### GitLab mirroring (one-way)

If you just want GitHub → GitLab one-way, GitLab has a built-in mirror:
- Settings → Repository → Mirroring repositories
- Put in your GitHub URL and token
- Select "Pull" direction

## Getting tokens

**GitHub:**
- Settings → Developer settings → Personal access tokens → Tokens (classic)
- Need `repo` and `workflow` scopes
- Works with github.com or GitHub Enterprise

**GitLab:**
- Preferences → Access Tokens  
- Need `api` and `write_repository` scopes
- Works with gitlab.com or self-hosted instances

## Two-way sync

If you want both directions working, set up BOTH the GitLab CI and GitHub Actions workflows. 

⚠️ Watch out for loops though - if GitHub pushes to GitLab, which triggers GitLab to push back to GitHub, which triggers GitHub again... The workflows check for `[skip sync]` in commit messages to prevent this, but be careful.

## Syncing issues and stuff

The `sync_activities.py` script can sync issues, milestones, labels, etc. It's a bit rough but works for basic cases. You'll need the API tokens set up.

## Problems?

- **Auth errors**: Check your tokens have the right permissions
- **Loops**: Make sure workflows aren't triggering each other
- **Can't push**: Tokens need write access to the repos
- **Self-hosted**: Use your instance URLs instead of github.com/gitlab.com

Check the workflow logs in GitHub/GitLab - usually it's a token permission issue or wrong URL.

