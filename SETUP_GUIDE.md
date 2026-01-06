# How to set this up

I'll walk you through getting the auto-sync working. It's not too bad once you get the tokens set up.

## First: Get your tokens

You'll need tokens from both GitHub and GitLab. These let the scripts push code for you.

### GitHub token

1. Go to https://github.com/settings/tokens (or your GitHub instance if self-hosted)
2. Click "Generate new token (classic)" 
3. Give it a name like "gitlab-sync" or whatever
4. Check these boxes: `repo` (all of it) and `workflow`
5. Click generate and **copy that token right away** - GitHub won't show it again

### GitLab token

1. Go to your GitLab instance (gitlab.com or your self-hosted one)
2. Click your profile → Preferences → Access Tokens
3. Name it something like "github-sync"
4. Check: `api` and `write_repository`
5. Expiration is optional - I usually leave it blank
6. Create it and **copy the token**

Note: If you're using a self-hosted GitLab, the URL will be different. Just make sure you're logged in and can create tokens.

## Jenkins Pipeline (recommended for GitHub → GitLab)

Jenkins is a great option for automating the sync from GitHub to GitLab, especially in enterprise environments.

> **💡 Don't have a machine?** Skip to [Cloud Jenkins Setup](#cloud-jenkins-setup-no-machine-needed) below for options that don't require your own server. Or consider using [CircleCI](#circleci-easier-alternative) or [Azure DevOps](#azure-devops-easier-alternative) instead - they're much easier to set up.

### Prerequisites

- Jenkins server with Python and Git installed
- Access to create credentials and pipelines in Jenkins

### Setup Jenkins Pipeline

1. **Add the Jenkinsfile to your GitHub repo:**
   - Copy the `Jenkinsfile` from this repo to the root of your GitHub repository
   - Update the `GITHUB_REPO` and `GITLAB_REPO` values in the Jenkinsfile
   - Commit and push it

2. **Create credentials in Jenkins:**
   - Go to Jenkins → Manage Jenkins → Credentials
   - Click "Add Credentials"
   - Create two "Secret text" credentials:
     - ID: `github-token` - paste your GitHub token
     - ID: `gitlab-token` - paste your GitLab token

3. **Create a new Pipeline job:**
   - New Item → Pipeline
   - Name it something like "GitHub to GitLab Sync"
   - Under "Pipeline Definition", select "Pipeline script from SCM"
   - SCM: Git
   - Repository URL: your GitHub repo URL
   - Script Path: `Jenkinsfile` (or leave default)
   - Save

4. **Configure triggers (choose one):**
   
   **Option A: Webhook (recommended)**
   - In GitHub: Settings → Webhooks → Add webhook
   - Payload URL: `http://your-jenkins-url/github-webhook/`
   - Content type: `application/json`
   - Events: Just the push event
   - In Jenkinsfile, remove the `pollSCM` trigger
   
   **Option B: Polling**
   - Keep the `pollSCM('H/5 * * * *')` in Jenkinsfile
   - This checks for changes every 5 minutes

5. **Test it:**
   - Make a change to your GitHub repo
   - Push it
   - Check Jenkins - the pipeline should trigger automatically
   - Check your GitLab repo - changes should appear

### Alternative: Freestyle Job

If you prefer a simpler setup without a Jenkinsfile:

1. Create a "Freestyle project" in Jenkins
2. **Source Code Management:**
   - Git
   - Repository URL: your GitHub repo URL
   - Credentials: your GitHub credentials (if private repo)
3. **Build Triggers:**
   - Check "Poll SCM"
   - Schedule: `H/5 * * * *` (every 5 minutes)
   - Or set up webhook instead
4. **Build:**
   - Add "Execute shell" step:
   ```bash
   pip install -r requirements.txt || pip3 install -r requirements.txt
   export GITHUB_TOKEN="your_github_token"
   export GITLAB_TOKEN="your_gitlab_token"
   export GITHUB_REPO="username/repo"
   export GITLAB_REPO="username/repo"
   python sync_repos.py code github-to-gitlab || python3 sync_repos.py code github-to-gitlab
   ```
5. Save and test

## Cloud Jenkins Setup (No Machine Needed)

If you don't have your own server/machine, here are cloud-based Jenkins options:

### Option 1: CloudBees Jenkins (Easiest Cloud Jenkins)

1. **Sign up:** Go to [cloudbees.com](https://www.cloudbees.com/products/cloudbees-ci)
   - Free tier available for open source projects
   - Paid plans for private repos

2. **Create organization:**
   - After signup, create a new organization
   - This gives you a Jenkins instance in the cloud

3. **Add Jenkinsfile to your repo:**
   - Copy the `Jenkinsfile` from this repo to your GitHub repo root
   - Update `GITHUB_REPO` and `GITLAB_REPO` values

4. **Create Pipeline:**
   - In CloudBees, create a new Pipeline job
   - Point it to your GitHub repo
   - It will automatically detect the Jenkinsfile

5. **Add credentials:**
   - Go to Credentials in CloudBees
   - Add `github-token` and `gitlab-token` as Secret text
   - Paste your tokens

6. **Configure webhook:**
   - In GitHub: Settings → Webhooks
   - Add webhook pointing to your CloudBees Jenkins URL
   - Or use polling (already configured in Jenkinsfile)

### Option 2: AWS EC2 (Free Tier for 12 Months)

1. **Launch EC2 instance:**
   - Go to AWS Console → EC2
   - Launch Instance → Choose Amazon Linux 2 (free tier eligible)
   - Instance type: t2.micro (free tier)
   - Configure security group: Allow port 8080 (HTTP) and 22 (SSH)

2. **Install Jenkins:**
   ```bash
   # SSH into your EC2 instance
   sudo yum update -y
   sudo yum install java-11-amazon-corretto -y
   sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
   sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key
   sudo yum install jenkins -y
   sudo systemctl start jenkins
   sudo systemctl enable jenkins
   ```

3. **Access Jenkins:**
   - Get your EC2 public IP
   - Visit `http://your-ec2-ip:8080`
   - Get initial password: `sudo cat /var/lib/jenkins/secrets/initialAdminPassword`

4. **Install Python:**
   ```bash
   sudo yum install python3 git -y
   ```

5. **Follow regular Jenkins setup** (steps 2-5 from above)

### Option 3: Docker on Cloud Platforms

Run Jenkins in Docker on platforms like Railway, Render, or Fly.io:

**Railway.app (Free Tier):**
1. Sign up at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Select "Dockerfile" option
4. Create `Dockerfile`:
   ```dockerfile
   FROM jenkins/jenkins:lts
   USER root
   RUN apt-get update && apt-get install -y python3 python3-pip git
   USER jenkins
   ```
5. Deploy and access Jenkins at the provided URL

**Render.com (Free Tier):**
1. Sign up at [render.com](https://render.com)
2. New → Web Service
3. Connect your GitHub repo with a Dockerfile (same as above)
4. Deploy

### Option 4: Use Easier Alternatives Instead

If setting up Jenkins seems complicated, consider these easier cloud CI/CD options:

#### CircleCI (Recommended - Free for Open Source)

1. Sign up at [circleci.com](https://circleci.com) (free for open source)
2. Add your GitHub repo
3. Create `.circleci/config.yml` in your repo (see README.md for example)
4. Add environment variables in CircleCI project settings
5. Push to GitHub - it runs automatically!

#### Azure DevOps (Free for Open Source)

1. Sign up at [dev.azure.com](https://dev.azure.com) (free)
2. Create new project
3. Pipelines → New Pipeline → Connect GitHub
4. Create `azure-pipelines.yml` (see README.md for example)
5. Add variables in Pipeline Library
6. Done!

**💡 My Recommendation:** If you don't have infrastructure and want something quick, use **CircleCI** or **Azure DevOps** instead of Jenkins. They're much easier to set up and don't require managing servers.

## Cron/Scheduled Tasks (GitHub → GitLab)

For simple automation without a CI/CD server, use cron (Linux/Mac) or Task Scheduler (Windows).

### Windows Task Scheduler

1. **Create a batch file** `sync.bat`:
   ```batch
   @echo off
   cd /d F:\priyam\git_gitlab_sync
   set GITHUB_TOKEN=your_github_token
   set GITLAB_TOKEN=your_gitlab_token
   set GITHUB_REPO=username/repo
   set GITLAB_REPO=username/repo
   python sync_repos.py code github-to-gitlab
   ```

2. **Open Task Scheduler:**
   - Search for "Task Scheduler" in Windows
   - Click "Create Basic Task"

3. **Configure the task:**
   - Name: "GitHub to GitLab Sync"
   - Trigger: "Daily" or "When the computer starts" (you can change frequency later)
   - Action: "Start a program"
   - Program: path to your `sync.bat` file
   - Start in: directory containing `sync.bat`

4. **Set frequency:**
   - Right-click the task → Properties
   - Triggers tab → Edit
   - Repeat task every: 15 minutes (or your preferred interval)
   - Duration: Indefinitely

### Linux/Mac Cron

1. **Edit crontab:**
   ```bash
   crontab -e
   ```

2. **Add this line** (runs every 15 minutes):
   ```bash
   */15 * * * * cd /path/to/git_gitlab_sync && GITHUB_TOKEN=your_token GITLAB_TOKEN=your_token GITHUB_REPO=username/repo GITLAB_REPO=username/repo python3 sync_repos.py code github-to-gitlab >> /var/log/gitlab-sync.log 2>&1
   ```

3. **For better security**, store tokens in a file:
   ```bash
   # Create .env file (chmod 600 .env)
   GITHUB_TOKEN=your_token
   GITLAB_TOKEN=your_token
   GITHUB_REPO=username/repo
   GITLAB_REPO=username/repo
   
   # Update crontab to source it
   */15 * * * * cd /path/to/git_gitlab_sync && source .env && python3 sync_repos.py code github-to-gitlab >> /var/log/gitlab-sync.log 2>&1
   ```

4. **Test it:**
   ```bash
   # Run manually first
   cd /path/to/git_gitlab_sync
   source .env
   python3 sync_repos.py code github-to-gitlab
   ```

## GitLab CI/CD (pushes GitLab → GitHub)

This one syncs from GitLab to GitHub. By default it's set to manual trigger to avoid loops, but you can make it automatic if you want.

### Add the CI file

1. In your GitLab repo root, create a file called `.gitlab-ci.yml`
2. Copy the contents from `.gitlab-ci.yml` in this repo
3. Commit it

### Set up variables

1. In your GitLab repo: Settings → CI/CD
2. Scroll down to Variables and expand it
3. Click "Add variable"
4. Add `GITHUB_TOKEN` - paste your GitHub token
   - Check "Mask variable" so it doesn't show in logs
   - Check "Protect variable" if you want (I usually do)
5. Add another variable `GITHUB_REPO_URL` - your GitHub repo URL like `https://github.com/username/repo.git`

### Test it

Push a change to GitLab, then go to CI/CD → Pipelines. You'll see a pipeline. Click on it, then click the `sync-to-github` job. Hit the play button to run it (it's manual by default). If it worked, check your GitHub repo.

## Important stuff

### Avoiding loops

Both workflows look for `[skip sync]` in your commit message. If you don't want something to sync, just add that:

```bash
git commit -m "testing something [skip sync]"
```

### Making GitLab sync automatic

Right now the GitLab → GitHub sync is manual (you have to click play). To make it automatic:

1. Open `.gitlab-ci.yml`
2. Find `when: manual` 
3. Change it to `when: on_success`

**But be careful** - if both are automatic and you push to either one, you could get a loop. I'd only make it automatic if:
- You're syncing different branches, OR
- You're okay with potential loops and will use `[skip sync]` when needed

### If something breaks

**Jenkins not working:**
- Check that Python and Git are installed on the Jenkins agent
- Verify credentials are set correctly (github-token and gitlab-token)
- Check the Jenkins build logs for specific errors
- Make sure the repo paths in Jenkinsfile match your actual repos
- Verify webhook is configured correctly if using webhook triggers

**Cron/Task Scheduler not working:**
- Test the script manually first: `python sync_repos.py code github-to-gitlab`
- Check that environment variables are set correctly
- For Windows: Check Task Scheduler history for errors
- For Linux: Check cron logs: `grep CRON /var/log/syslog` or check your log file
- Make sure Python is in the PATH for scheduled tasks

**GitLab CI not working:**
- Check the variables are set (GITHUB_TOKEN and GITHUB_REPO_URL)
- Make sure your GitHub token has repo scope
- Remember it's manual by default - you need to click the play button!
- Check the pipeline logs for what went wrong

**Getting loops:**
- Don't make both automatic unless you know what you're doing
- Use `[skip sync]` when you need to push without syncing
- You could sync different branches (like GitHub main → GitLab main, but GitLab dev → GitHub dev)

### What actually syncs

- Code and commits (all branches)
- Full git history

Issues, PRs, comments, etc. don't sync automatically - you'd need to use the Python scripts for that (`sync_repos.py` and `sync_activities.py`).

### Self-hosted instances

If you're using GitHub Enterprise or self-hosted GitLab, just use your instance URLs instead of github.com/gitlab.com. Everything else should work the same.

## GitHub Actions (last resort option)

⚠️ **Note:** Only use GitHub Actions if you don't have access to Jenkins, cron, or other CI/CD systems. It requires storing secrets in GitHub.

### Add the workflow file

1. In your GitHub repo, go to the root
2. Create a folder called `.github` if it doesn't exist
3. Inside that, create `workflows` folder
4. Create a file called `sync-to-gitlab.yml` in `.github/workflows/`
5. Copy the contents from the `.github/workflows/sync-to-gitlab.yml` file in this repo (if it exists)
6. Commit and push it

### Set up secrets

1. In your GitHub repo, go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `GITLAB_TOKEN` - paste your GitLab token here
4. Add another secret called `GITLAB_REPO_URL` - this should be your full GitLab repo URL like `https://gitlab.com/yourusername/yourrepo.git` or `https://gitlab.yourcompany.com/group/repo.git` if self-hosted

### Test it

Make a small change, commit, push. Then check the Actions tab - you should see it running. If it worked, your GitLab repo should have the same changes.

**GitHub Actions troubleshooting:**
- Double-check the secrets are set (GITLAB_TOKEN and GITLAB_REPO_URL)
- Make sure your GitLab token has write_repository permission
- Check the Actions tab - the error messages are usually pretty clear

---

Once you've got both set up, you're good to go. Push to GitHub and it goes to GitLab automatically (via Jenkins/cron/etc). Push to GitLab and trigger the sync job to send it to GitHub.

