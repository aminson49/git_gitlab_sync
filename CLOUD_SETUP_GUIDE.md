# Cloud Setup Guide - No Machine Needed

If you don't have your own server/machine, here are the easiest ways to automate GitHub → GitLab sync:

## 🏆 Recommended: CircleCI (Easiest)

**Why:** Free for open source, very easy setup, no server management.

### Quick Setup (5 minutes):

1. **Sign up:** [circleci.com](https://circleci.com) (free for public repos)
2. **Add your GitHub repo:**
   - Click "Add Projects"
   - Select your GitHub repo
   - Click "Set Up Project"
3. **Create `.circleci/config.yml` in your repo:**
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
4. **Add environment variables:**
   - In CircleCI: Project Settings → Environment Variables
   - Add: `GITHUB_TOKEN`, `GITLAB_TOKEN`, `GITHUB_REPO`, `GITLAB_REPO`
5. **Push to GitHub** - CircleCI will automatically run!

**Cost:** Free for open source, $15/month for private repos (includes 6,000 build minutes)

---

## 🥈 Alternative: Azure DevOps (Also Easy)

**Why:** Free for open source, Microsoft-backed, good free tier.

### Quick Setup:

1. **Sign up:** [dev.azure.com](https://dev.azure.com) (free)
2. **Create project:**
   - Click "New Project"
   - Give it a name
3. **Create pipeline:**
   - Pipelines → New Pipeline
   - Connect to GitHub
   - Select your repo
   - Choose "Starter pipeline"
4. **Replace pipeline content with:**
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
5. **Add variables:**
   - Pipelines → Library → Variable groups
   - Create new group, add your variables
6. **Save and run!**

**Cost:** Free for open source, 1,800 minutes/month free for private repos

---

## 🥉 Cloud Jenkins Options

If you specifically need Jenkins, here are cloud options:

### CloudBees Jenkins (Easiest Cloud Jenkins)

1. Sign up: [cloudbees.com](https://www.cloudbees.com/products/cloudbees-ci)
2. Create organization (free tier available)
3. Add `Jenkinsfile` to your repo (see main README)
4. Create Pipeline job pointing to your GitHub repo
5. Add credentials (github-token, gitlab-token)
6. Configure webhook

**Cost:** Free tier for open source, paid plans available

### AWS EC2 (Free for 12 Months)

1. Launch t2.micro EC2 instance (free tier)
2. Install Jenkins (see SETUP_GUIDE.md)
3. Configure security group (port 8080)
4. Follow regular Jenkins setup

**Cost:** Free for 12 months (t2.micro), then ~$10/month

### Docker on Railway/Render (Free Tier)

1. Sign up at [railway.app](https://railway.app) or [render.com](https://render.com)
2. Deploy Jenkins Docker container
3. Access Jenkins via provided URL
4. Follow regular setup

**Cost:** Free tier available, paid plans for more resources

---

## 🎯 Quick Comparison

| Option | Setup Time | Cost | Difficulty | Best For |
|--------|-----------|------|------------|----------|
| **CircleCI** | 5 min | Free (OSS) | ⭐ Easy | Most users |
| **Azure DevOps** | 10 min | Free (OSS) | ⭐ Easy | Microsoft ecosystem |
| **CloudBees** | 15 min | Free tier | ⭐⭐ Medium | Jenkins-specific needs |
| **AWS EC2** | 30 min | Free 12mo | ⭐⭐⭐ Hard | AWS users |
| **Docker Cloud** | 20 min | Free tier | ⭐⭐ Medium | Docker users |

---

## 💡 My Recommendation

**For most users:** Use **CircleCI** - it's the fastest to set up and works great.

**If you need Jenkins specifically:** Use **CloudBees** - it's Jenkins in the cloud without server management.

**If you're already on Azure:** Use **Azure DevOps** - integrates well with Microsoft tools.

---

## Need Help?

- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- See [README.md](README.md) for all automation options
- Check the main repo for example config files

