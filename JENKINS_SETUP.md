# Jenkins Setup Guide

I've been using Jenkins to auto-sync my repos and it works pretty well. Here's how I set it up. There are two main approaches - using a publicly hosted Jenkins (easier for webhooks) or running it yourself.

## Publicly Hosted Jenkins

Using a hosted Jenkins is way easier because you don't have to mess with exposing your local server to the internet for webhooks. I set mine up on AWS EC2 but there are other options too.

### Why Hosted is Better

- No need to set up your own server
- Always accessible from internet (webhooks just work)
- Someone else handles the infrastructure
- Webhooks are dead simple to configure

### Hosting Options

I went with AWS EC2 because it's cheap and I'm familiar with AWS, but you could also use:
- CloudBees (if you're okay paying for it)
- Azure VMs
- Google Cloud
- Or any VPS provider really

### My Setup: AWS EC2

Here's what I did step by step:

#### Launch an EC2 Instance

1. AWS Console → EC2 → Launch Instance
2. Pick Ubuntu or Amazon Linux (Ubuntu is easier in my experience)
3. Configure security group - this is important:
   - Port 8080 from `0.0.0.0/0` for HTTP (or 443 if you set up HTTPS)
   - Port 22 for SSH
4. Launch it and SSH in

#### Install Java 17 (Required)

Newer Jenkins versions (2.400+) require Java 17 or 21, not Java 11:

```bash
# Install Java 17
sudo apt update
sudo apt install openjdk-17-jdk -y

# Verify installation
java -version
# Should show "openjdk version 17..."
```

#### Install Jenkins

```bash
# Add Jenkins repository
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo apt-key add -
sudo sh -c 'echo deb https://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt update
sudo apt install jenkins -y

# Make sure Jenkins uses Java 17
sudo update-alternatives --config java
# Select Java 17 if prompted

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Wait a few seconds for Jenkins to initialize
sleep 15

# Get the initial password (you'll need this)
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**Note:** If you already installed Java 11, you can install Java 17 alongside it and Jenkins will use 17 automatically.

#### Initial Jenkins Setup

1. Open `http://your-ec2-public-ip:8080` in your browser
2. Paste that initial password
3. Install suggested plugins (this takes a few minutes)
4. Create an admin user

#### Install Required Plugins

Go to Manage Jenkins → Manage Plugins → Available tab

You'll need these plugins:
- GitHub plugin
- GitHub Branch Source plugin (for webhooks)
- Git plugin
- Pipeline plugin
- Credentials Binding plugin

Just search for them and install. You might need to restart Jenkins after.

#### Create the Pipeline Job

1. Click "New Item"
2. Name it `git-gitlab-sync-pipeline` (or whatever you want)
3. Select "Pipeline" type
4. Click OK

In the configuration:
- **Build Triggers:** Check "GitHub hook trigger for GITScm polling" - this is what makes it auto-trigger
- **Pipeline section:** Select "Pipeline script from SCM"
- **SCM:** Choose Git
- **Repository URL:** `https://github.com/aminson49/git_gitlab_sync.git` (or your repo)
- **Credentials:** 
  - If repo is **public**: Leave as "- none -"
  - If repo is **private**: Select the "Username with password" credential you created (e.g., `github-repo-access`)
- **Branch:** `*/main` (or `*/master` if that's your default branch)
- **Script Path:** `Jenkinsfile`
- Save it

#### Add Your Credentials

You need to create credentials in two places:

**1. For Git SCM (Repository Access):**

Go to Manage Jenkins → Credentials → System → Global credentials

Click "+ Add Credentials" and create:
- **Kind:** Username with password
- **Username:** Your GitHub username (or `git` for token-based auth)
- **Password:** Your GitHub personal access token
- **ID:** `github-repo-access` (or any name you want)
- **Description:** GitHub Repo Access

**Note:** If your GitHub repo is public, you can skip this and leave credentials as "- none -" in the pipeline config.

**2. For Jenkinsfile Environment Variables:**

Add two "Secret text" credentials:
1. ID: `github-token` (this exact name - the Jenkinsfile looks for this)
   - Secret: Your GitHub personal access token
2. ID: `gitlab-token` (also exact)
   - Secret: Your GitLab access token

These are used by the sync script inside the pipeline, not for Git access.

#### Set Up GitHub Webhook

1. Go to your GitHub repo → Settings → Webhooks
2. Click "Add webhook"
3. **Payload URL:** `http://your-ec2-public-ip:8080/github-webhook/` (the trailing slash matters!)
4. **Content type:** `application/json`
5. **Events:** Just select "Just the push event" - no need for all events
6. Click "Add webhook"

Now whenever you push to GitHub, it should trigger a Jenkins build automatically.

#### Test It

Make a test commit:
```bash
git add .
git commit -m "Test Jenkins trigger"
git push origin main
```

Check your Jenkins: `http://your-ec2-public-ip:8080/job/git-gitlab-sync-pipeline/`

You should see a new build start within a few seconds!

---

## Running Jenkins Locally (Docker)

If you want to run Jenkins on your own machine for testing:

Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  jenkins:
    image: jenkins/jenkins:lts
    ports:
      - "8080:8080"
    volumes:
      - jenkins_home:/var/jenkins_home

volumes:
  jenkins_home:
```

Run it:
```bash
docker-compose up -d
```

Access it at `http://localhost:8080`

Get the password: `docker exec <container-name> cat /var/jenkins_home/secrets/initialAdminPassword`

Then follow the same setup steps as above. Only catch is webhooks won't work unless you expose it to the internet somehow.

---

## Using ngrok for Local Testing

If you want to test webhooks with a local Jenkins, ngrok works but it's annoying because the URL changes every time:

1. Install ngrok from their website
2. Run: `ngrok http 8080`
3. Copy the HTTPS URL it gives you
4. Use that in your GitHub webhook

It works but the URL changes when you restart ngrok, so you have to update the webhook every time. For anything real, just use a hosted Jenkins.

---

## Jenkinsfile Setup

Make sure your `Jenkinsfile` has the right repo names:

```groovy
environment {
    GITHUB_TOKEN = credentials('github-token')
    GITLAB_TOKEN = credentials('gitlab-token')
    GITHUB_REPO = 'aminson49/git_gitlab_sync'  // change this
    GITLAB_REPO = 'username/repo'  // change this too
}
```

The credential IDs need to match exactly what you created in Jenkins.

---

## Security Stuff

If you're exposing Jenkins to the internet (which you need to for webhooks), here's what I do:

- Use HTTPS if possible (Let's Encrypt is free)
- Restrict the security group to only allow necessary ports
- Use strong passwords
- Keep Jenkins updated (it has security issues sometimes)
- Store tokens in Jenkins credentials, never hardcode them

For AWS specifically:
- Security groups should only allow 8080 (or 443), 22 for SSH
- Use SSH keys, don't allow password auth
- Consider using a VPC if you're serious about it
- Set up SSL if you can (free with Let's Encrypt)

---

## Troubleshooting

### Webhook not working?

1. Check if Jenkins is actually accessible:
   ```bash
   curl http://your-jenkins-url:8080/github-webhook/
   ```
   Should return 403, not 404. If 404, the webhook endpoint isn't working.

2. Check GitHub's webhook delivery logs:
   - Go to your repo → Settings → Webhooks → Click on your webhook
   - Check "Recent Deliveries" - you'll see if GitHub is even trying to send requests
   - Look for error codes

3. Check Jenkins logs:
   ```bash
   # On EC2
   sudo tail -f /var/log/jenkins/jenkins.log
   
   # Docker
   docker logs jenkins
   ```

### Builds failing?

1. Credentials not set up right:
   - Make sure the credential IDs are exactly `github-token` and `gitlab-token`
   - Check they're actually set (sometimes they look set but aren't)

2. Jenkinsfile issues:
   - Verify the repo names are correct
   - Make sure Python is installed on Jenkins (the pipeline needs it)

3. Check the build console output - that usually tells you exactly what's wrong

---

## What's Next?

Once it's working:
- Test it with a small change first
- Watch the build logs to make sure it's syncing right
- Maybe set up email notifications if builds fail (optional)
- Check out the conflict resolution testing guide to make sure edge cases work

See [CONFLICT_RESOLUTION_TESTING.md](CONFLICT_RESOLUTION_TESTING.md) for how to test various conflict scenarios.
