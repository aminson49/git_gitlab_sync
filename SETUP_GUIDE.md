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

### Setting up HTTPS for Jenkins on EC2

If you want to use HTTPS (recommended for production), here's how to set it up with nginx and Let's Encrypt on EC2:

**Prerequisites:**
- EC2 instance with public IP or Elastic IP
- Domain name pointing to your EC2 instance (or you can use the public IP, but domain is better)
- Security group allowing inbound traffic on ports 80 and 443

**EC2 Security Group Setup:**

1. Go to EC2 → Security Groups → Select your instance's security group
2. Add inbound rules:
   - Type: HTTP, Port: 80, Source: 0.0.0.0/0
   - Type: HTTPS, Port: 443, Source: 0.0.0.0/0
3. Save rules

**On Your EC2 Instance:**

1. Install nginx:
   ```bash
   sudo apt update
   sudo apt install nginx -y
   ```

2. Install certbot for Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

3. Create nginx config for Jenkins:
   ```bash
   sudo nano /etc/nginx/sites-available/jenkins
   ```
   
   Add this (replace `your-domain.com` with your domain or use your EC2 public IP):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # or your EC2 public IP
       
       location / {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 90s;
       }
   }
   ```

4. Enable the site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/jenkins /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default  # Remove default site if it exists
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. Get SSL certificate:
   
   **If you have a domain:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```
   
   **If you only have EC2 public IP (no domain):**
   - You'll need to use a self-signed certificate, but GitHub webhooks won't work with it
   - Better option: Get a free domain from services like Freenom, or use AWS Route 53
   - Or use ngrok for testing (it provides HTTPS automatically)
   
   Certbot will automatically:
   - Get the SSL certificate from Let's Encrypt
   - Configure nginx for HTTPS
   - Set up automatic HTTP to HTTPS redirect
   - Configure auto-renewal

6. Configure Jenkins to work behind proxy:
   ```bash
   sudo nano /etc/default/jenkins
   ```
   
   Add or update this line:
   ```
   JENKINS_ARGS="--httpPort=8080 --httpListenAddress=127.0.0.1"
   ```
   
   This makes Jenkins only listen on localhost (nginx handles external traffic).

7. Configure Jenkins URL in Jenkins UI:
   - Go to Manage Jenkins → Configure System
   - Find "Jenkins URL" field
   - Set it to: `https://your-domain.com` (or your HTTPS URL)
   - Save

8. Restart Jenkins:
   ```bash
   sudo systemctl restart jenkins
   ```

9. Test HTTPS:
   - Open browser and go to `https://your-domain.com`
   - You should see Jenkins login page over HTTPS

10. Update GitHub webhook URL:
    - Go to your GitHub repo → Settings → Webhooks
    - Edit the webhook
    - Change URL to: `https://your-domain.com/github-webhook/`
    - Save

**Auto-renewal:**
Let's Encrypt certificates expire every 90 days. Certbot sets up auto-renewal automatically, but you can test it:
```bash
sudo certbot renew --dry-run
```

**If you don't have a domain:**
- Option 1: Get a free domain (Freenom, etc.) and point it to your EC2 IP
- Option 2: Use AWS Route 53 to register a domain
- Option 3: Use ngrok for testing (provides HTTPS tunnel)
- Option 4: Stick with HTTP (not recommended for production, and GitHub webhooks may have issues)

**Troubleshooting:**
- If certbot fails, make sure port 80 is open in security group
- If nginx won't start, check config: `sudo nginx -t`
- If Jenkins isn't accessible, check it's running: `sudo systemctl status jenkins`
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`

## GitLab CI Setup

If your main repo is on GitLab:

1. Copy `.gitlab-ci.yml` to your GitLab repo
2. Settings → CI/CD → Variables
3. Add these variables:
   - `GITHUB_TOKEN` - Your GitHub personal access token
   - `GITHUB_REPO_URL` (optional) - GitHub repo URL, defaults to `https://github.com/$CI_PROJECT_PATH.git`
4. Push to GitLab and it'll automatically sync to GitHub

The pipeline runs automatically on every push to any branch. It syncs GitLab → GitHub and handles conflicts by keeping GitLab's version (since GitLab is the source in this case).

**Important:** If you're also using Jenkins or CircleCI to sync GitHub → GitLab, make sure only one direction is automated to avoid infinite loops. For example:
- Use GitLab CI to sync GitLab → GitHub (automated)
- Use Jenkins/CircleCI to sync GitHub → GitLab (automated)
- But don't automate both directions at the same time, or you'll create a loop

The `[skip sync]` check helps prevent loops, but it's safer to only automate one direction.

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
