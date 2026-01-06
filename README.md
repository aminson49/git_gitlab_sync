# Syncing GitHub and GitLab repos

I got tired of manually keeping my repos in sync between GitHub and GitLab, so I threw together some scripts to automate it. Sharing in case anyone else needs this.

Works with regular GitHub/GitLab, GitHub Enterprise, self-hosted GitLab, whatever. Just need the right URLs and tokens.

> **💡 Don't have a server/machine?** Check out **[CLOUD_SETUP_GUIDE.md](CLOUD_SETUP_GUIDE.md)** for easy cloud-based automation options (CircleCI, Azure DevOps, CloudBees) that don't require your own infrastructure.

## What's here

There's a few different ways to sync stuff:

1. **GitLab CI/CD** - pushes from GitLab to GitHub when you commit
2. **Jenkins Pipeline** - automated sync with Jenkins CI/CD
3. **Cron/Scheduled Tasks** - run the Python script on a schedule
4. **Python script** - run it manually whenever you want
5. **GitLab mirroring** - built-in feature but it's one-way only
6. **GitHub Actions** - pushes from GitHub to GitLab when you commit (last resort option)

## Quick setup

**See [SETUP_GUIDE.md](SETUP_GUIDE.md) for the full walkthrough**

### GitLab CI/CD (pushes GitLab → GitHub)

1. Copy `.gitlab-ci.yml` to your GitLab repo root
2. Settings → CI/CD → Variables
3. Add `GITHUB_TOKEN` (your GitHub token)
4. Add `GITHUB_REPO_URL` like `https://github.com/username/repo.git` (or your GitHub Enterprise URL)
5. Push to GitLab, then manually trigger the sync job (or change `when: manual` to `when: on_success`)

### Jenkins Pipeline (automated sync)

> **Don't have a machine?** See [Cloud Jenkins Setup](#cloud-jenkins-setup-no-machine-needed) below or check out **[CLOUD_SETUP_GUIDE.md](CLOUD_SETUP_GUIDE.md)** for easy cloud-based options (CircleCI, Azure DevOps, etc.) that don't require your own server.

Create a `Jenkinsfile` in your GitHub repo root:

```groovy
pipeline {
    agent any
    
    triggers {
        // Poll GitHub every 5 minutes for changes
        pollSCM('H/5 * * * *')
        // Or use webhook triggers instead
    }
    
    environment {
        GITHUB_TOKEN = credentials('github-token')
        GITLAB_TOKEN = credentials('gitlab-token')
        GITHUB_REPO = 'username/repo'
        GITLAB_REPO = 'username/repo'
    }
    
    stages {
        stage('Sync GitHub to GitLab') {
            steps {
                script {
                    sh '''
                        pip install -r requirements.txt || pip3 install -r requirements.txt
                        python sync_repos.py code github-to-gitlab
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs() // Clean workspace after build
        }
    }
}
```

**Setup (if you have a machine):**
1. Install Python and Git on your Jenkins agent
2. Create credentials in Jenkins:
   - `github-token` (Secret text) - your GitHub personal access token
   - `gitlab-token` (Secret text) - your GitLab access token
3. Create a new Pipeline job in Jenkins
4. Point it to your GitHub repo
5. Configure webhook in GitHub (Settings → Webhooks) to trigger on push, or use polling

**Alternative: Freestyle Job**
- Create a "Freestyle project" in Jenkins
- Source Code Management: Git (point to GitHub repo)
- Build Triggers: "Poll SCM" (e.g., `H/5 * * * *` for every 5 minutes)
- Build: Add "Execute shell" step:
  ```bash
  pip install -r requirements.txt
  export GITHUB_TOKEN="your_token"
  export GITLAB_TOKEN="your_token"
  export GITHUB_REPO="username/repo"
  export GITLAB_REPO="username/repo"
  python sync_repos.py code github-to-gitlab
  ```

### Cloud Jenkins Setup (No Machine Needed)

If you don't have your own machine/server, here are cloud-based options:

#### Option 1: CloudBees Jenkins (Free Tier Available)
1. Sign up at [cloudbees.com](https://www.cloudbees.com/products/cloudbees-ci) (free tier available)
2. Create a new organization
3. Add the `Jenkinsfile` to your GitHub repo
4. Create a Pipeline job pointing to your GitHub repo
5. Add credentials (github-token, gitlab-token) in CloudBees
6. Configure webhook or polling

#### Option 2: AWS EC2 (Free Tier for 12 Months)
1. Launch an EC2 instance (t2.micro is free tier eligible)
2. Install Jenkins: `sudo yum install jenkins` or use Docker
3. Follow the regular Jenkins setup steps above
4. Configure security group to allow web access (port 8080)

#### Option 3: Google Cloud Run (Pay per use)
1. Use Jenkins in Docker on Cloud Run
2. Or use Cloud Build (Google's CI/CD) - see [Other CI/CD Options](#other-cicd-options) below

#### Option 4: Azure DevOps Pipelines (Free for Open Source)
- See [Other CI/CD Options](#other-cicd-options) below - Azure DevOps is easier than setting up Jenkins

#### Option 5: Docker on Cloud Platforms
Run Jenkins in Docker on:
- **Railway.app** (free tier): Deploy Jenkins Docker image
- **Render.com** (free tier): Deploy Jenkins as a web service
- **Fly.io** (free tier): Run Jenkins container

**Quick Docker Setup:**
```bash
# On any cloud platform that supports Docker
docker run -d -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts
```

Then access Jenkins at `http://your-cloud-url:8080` and follow setup wizard.

**💡 Recommendation:** If you don't have infrastructure, consider using **CircleCI**, **Azure DevOps**, or **GitLab CI** (if syncing to GitLab) instead - they're easier to set up than Jenkins.

### Cron/Scheduled Tasks (Windows Task Scheduler or Linux cron)

**Windows (Task Scheduler):**
1. Create a batch file `sync.bat`:
   ```batch
   @echo off
   cd /d F:\priyam\git_gitlab_sync
   set GITHUB_TOKEN=your_token
   set GITLAB_TOKEN=your_token
   set GITHUB_REPO=username/repo
   set GITLAB_REPO=username/repo
   python sync_repos.py code github-to-gitlab
   ```
2. Open Task Scheduler
3. Create Basic Task → Set trigger (e.g., every 15 minutes)
4. Action: Start a program → Point to `sync.bat`

**Linux/Mac (cron):**
```bash
# Edit crontab
crontab -e

# Add this line to run every 15 minutes
*/15 * * * * cd /path/to/git_gitlab_sync && GITHUB_TOKEN=your_token GITLAB_TOKEN=your_token GITHUB_REPO=username/repo GITLAB_REPO=username/repo python3 sync_repos.py code github-to-gitlab >> /var/log/gitlab-sync.log 2>&1
```

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

### Other CI/CD Options (Easier than Jenkins - No Machine Needed)

These cloud CI/CD services are easier to set up than Jenkins and don't require your own machine:

**CircleCI (Recommended - Free for Open Source):**

1. Sign up at [circleci.com](https://circleci.com) and add your GitHub repo
2. **Add environment variables** (IMPORTANT):
   - Project Settings → Environment Variables
   - Add: `GITHUB_TOKEN`, `GITLAB_TOKEN`, `GITHUB_REPO`, `GITLAB_REPO`
   - **Format for repos:** `username/repo` (e.g., `octocat/Hello-World`) - **NO .git extension!**
3. Create `.circleci/config.yml`:
```yaml
version: 2.1
jobs:
  sync:
    docker:
      - image: python:3.9
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -r requirements.txt
      - run:
          name: Sync to GitLab
          command: |
            export GITHUB_TOKEN=$GITHUB_TOKEN
            export GITLAB_TOKEN=$GITLAB_TOKEN
            export GITHUB_REPO=$GITHUB_REPO
            export GITLAB_REPO=$GITLAB_REPO
            python sync_repos.py code github-to-gitlab
workflows:
  version: 2
  sync-on-push:
    jobs:
      - sync:
          filters:
            branches:
              only: main
```

**Azure DevOps Pipelines (Free for Open Source):**
1. Sign up at [dev.azure.com](https://dev.azure.com) (free)
2. Create a new project
3. Pipelines → New Pipeline → Connect to GitHub
4. Select your repo
5. Create `azure-pipelines.yml` in your repo root:
```yaml
trigger:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.9'
- script: |
    pip install -r requirements.txt
    export GITHUB_TOKEN=$(GITHUB_TOKEN)
    export GITLAB_TOKEN=$(GITLAB_TOKEN)
    export GITHUB_REPO=$(GITHUB_REPO)
    export GITLAB_REPO=$(GITLAB_REPO)
    python sync_repos.py code github-to-gitlab
  env:
    GITHUB_TOKEN: $(GITHUB_TOKEN)
    GITLAB_TOKEN: $(GITLAB_TOKEN)
    GITHUB_REPO: $(GITHUB_REPO)
    GITLAB_REPO: $(GITLAB_REPO)
```
6. Add variables in Pipeline → Library → Variable groups (GITHUB_TOKEN, GITLAB_TOKEN, etc.)

**GitLab CI (If syncing TO GitLab):**
- Already configured! Just use the `.gitlab-ci.yml` file
- GitLab provides free CI/CD minutes
- No setup needed - it's built-in

**Travis CI:**
Create `.travis.yml`:
```yaml
language: python
python:
  - "3.9"
install:
  - pip install -r requirements.txt
script:
  - export GITHUB_TOKEN=$GITHUB_TOKEN
  - export GITLAB_TOKEN=$GITLAB_TOKEN
  - export GITHUB_REPO=$GITHUB_REPO
  - export GITLAB_REPO=$GITLAB_REPO
  - python sync_repos.py code github-to-gitlab
```
Add environment variables in Travis CI settings.

**GitHub Actions (last resort option)**

If you don't have access to Jenkins, cron, or other CI/CD systems, GitHub Actions can work as a fallback:

1. Copy `.github/workflows/sync-to-gitlab.yml` to your GitHub repo (create `.github/workflows/` folder if needed)
2. Settings → Secrets → Actions
3. Add `GITLAB_TOKEN` (your GitLab token)
4. Add `GITLAB_REPO_URL` like `https://gitlab.com/username/repo.git` (or your GitLab instance URL)
5. Push to GitHub - it'll automatically sync to GitLab!

⚠️ **Note:** GitHub Actions is listed last because it requires storing secrets in GitHub and may not be suitable for all organizations. Prefer Jenkins, cron, or GitLab CI/CD when possible.

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

If you want both directions working, you can combine different methods:
- **GitLab → GitHub**: Use GitLab CI/CD (already configured in `.gitlab-ci.yml`)
- **GitHub → GitLab**: Use Jenkins, cron, or the Python script (preferred) instead of GitHub Actions

⚠️ Watch out for loops though - if GitHub pushes to GitLab, which triggers GitLab to push back to GitHub, which triggers GitHub again... The workflows check for `[skip sync]` in commit messages to prevent this, but be careful.

## Syncing issues and stuff

The `sync_activities.py` script can sync issues, milestones, labels, etc. It's a bit rough but works for basic cases. You'll need the API tokens set up.

## Problems?

### CircleCI Issues

**"repository not found" or "remote: Not Found":**
- ✅ Check `GITHUB_REPO` format: Should be `username/repo` (NOT `https://github.com/username/repo.git`)
- ✅ Verify `GITHUB_TOKEN` has `repo` scope and access to the repository
- ✅ Make sure all 4 environment variables are set in CircleCI project settings

**"GITHUB_REPO is not set":**
- ✅ Go to CircleCI → Project Settings → Environment Variables
- ✅ Verify all variables are set: `GITHUB_TOKEN`, `GITLAB_TOKEN`, `GITHUB_REPO`, `GITLAB_REPO`
- ✅ Check for typos (variable names are case-sensitive)

**"403 Forbidden" when pushing to GitLab:**
- ✅ **Most common issue!** Your GitLab token needs BOTH scopes:
  - `api` (full API access)
  - `write_repository` (write repository content)
- ✅ Go to GitLab → Preferences → Access Tokens
- ✅ Create a NEW token with both `api` AND `write_repository` scopes checked
- ✅ Update `GITLAB_TOKEN` in CircleCI with the new token
- ✅ Verify the token owner has access to the repository (at least Developer role)
- ✅ For self-hosted GitLab, you may need to set `GITLAB_API_BASE` environment variable

### General Issues

- **Auth errors**: Check your tokens have the right permissions (`repo` for GitHub, `write_repository` for GitLab)
- **Loops**: Make sure workflows aren't triggering each other
- **Can't push**: Tokens need write access to the repos
- **Self-hosted**: Use your instance URLs instead of github.com/gitlab.com

Check the workflow logs - usually it's a token permission issue or wrong URL format.

