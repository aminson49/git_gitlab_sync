# Setup Guide

Quick guide to get this working. I've used Jenkins mostly, but there are other options too.

## Get Your Tokens First

### GitHub Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it something like "gitlab-sync"
4. Check the `repo` scope
5. Copy the token (you won't see it again)

**Note:** This token is used by the sync script for API access. For cloning the repo in Jenkins, we use username and password instead (see Jenkins setup below).

### GitLab Token

1. GitLab → Preferences → Access Tokens
2. Name it "github-sync" or whatever
3. Check `api` and `write_repository` scopes (both are needed)
4. Copy the token

## Jenkins Setup

I'm running Jenkins on AWS EC2. Here's the quick version:

### On Your Server

1. Install Java 17 (newer Jenkins needs it):
   ```bash
   sudo apt update
   sudo apt install openjdk-17-jdk python3 python3-pip python3-venv -y
   ```

2. Install Jenkins:
   ```bash
   wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo apt-key add -
   sudo sh -c 'echo deb https://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
   sudo apt update
   sudo apt install jenkins -y
   sudo systemctl start jenkins
   sudo systemctl enable jenkins
   ```

3. Get initial password:
   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```

4. Open Jenkins in browser (http://your-server-ip:8080), paste password, complete setup

### Configure Jenkins

1. Install plugins: GitHub plugin, GitHub Branch Source plugin, Git plugin, Pipeline plugin

2. Create credentials:
   - Go to Manage Jenkins → Credentials → Global
   - Add "Secret text" with ID `github-token` (your GitHub token - used by the sync script)
   - Add "Secret text" with ID `gitlab-token` (your GitLab token)
   - Add "Username with password" credential for GitHub Git access:
     - Username: your GitHub username
     - Password: your GitHub personal access token (or password if you don't use 2FA)
     - ID: something like `github-git-credentials` (you'll select this in the pipeline config)

3. Create pipeline job:
   - New Item → Pipeline
   - Name it `git-gitlab-sync-pipeline`
   - Build Triggers: Check "GitHub hook trigger for GITScm polling"
   - Pipeline: "Pipeline script from SCM"
   - SCM: Git
   - Repository URL: `https://github.com/aminson49/git_gitlab_sync.git`
   - Credentials: Select the "Username with password" credential you created above
   - Branch: `*/main` (or whatever your branch is)
   - Script Path: `Jenkinsfile`
   - Save

4. Set up webhook in GitHub:
   - Repo → Settings → Webhooks → Add webhook
   - URL: `http://your-jenkins-ip:8080/github-webhook/`
   - Events: Just push events
   - Add webhook

Now when you push to GitHub, Jenkins will automatically sync to GitLab.

**Note:** If Jenkins is local, you'll need ngrok or similar to expose it for webhooks. Or just use polling instead.

## GitLab CI Setup

If your main repo is on GitLab:

1. Copy `.gitlab-ci.yml` to your GitLab repo
2. Settings → CI/CD → Variables
3. Add `GITHUB_TOKEN` and `GITHUB_REPO_URL`
4. Push to GitLab and it'll trigger

## GitHub Actions

GitHub won't let Actions auto-run for security, so it's manual only:

1. Copy `.github/workflows/sync-to-gitlab.yml` to your repo
2. Settings → Secrets and variables → Actions
3. Add secrets: `GITLAB_TOKEN`, `GITHUB_REPO`, `GITLAB_REPO`
4. Go to Actions tab and manually run it

## Scheduled Tasks

**Windows:**
Create a batch file and add to Task Scheduler:
```batch
cd /d F:\priyam\git_gitlab_sync
set GITHUB_TOKEN=your_token
set GITLAB_TOKEN=your_token
set GITHUB_REPO=aminson49/git_gitlab_sync
set GITLAB_REPO=poc-group1603702/gitlab_github_sync
python sync_repos.py code github-to-gitlab
```

**Linux/Mac:**
Add to crontab:
```bash
*/15 * * * * cd /path/to/repo && GITHUB_TOKEN=token GITLAB_TOKEN=token GITHUB_REPO=user/repo GITLAB_REPO=user/repo python3 sync_repos.py code github-to-gitlab >> /var/log/gitlab-sync.log 2>&1
```

## Troubleshooting

**403 Forbidden:**
- GitLab token needs both `api` AND `write_repository` scopes
- Make sure token owner has repo access

**Protected branch:**
- Script tries to merge automatically
- If it fails, unprotect branch temporarily or give token permission

**Repo not found:**
- Use `username/repo` format, not full URL
- Check tokens have access

**Jenkins build fails:**
- Make sure Python 3 and python3-venv are installed
- Check credentials IDs match exactly: `github-token` and `gitlab-token`
- Verify repo names in Jenkinsfile are correct
- If checkout fails, make sure you selected the "Username with password" credential in the pipeline job's Git SCM configuration

**Merge conflicts:**
- The script automatically handles merge conflicts by keeping GitHub's version
- If you see conflict messages in the logs, that's normal - the script resolves them automatically
- GitHub is always treated as the source of truth, so GitLab will be updated to match GitHub
