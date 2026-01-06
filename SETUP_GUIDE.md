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

## GitHub Actions (pushes GitHub → GitLab)

This one's pretty straightforward. When you push to GitHub, it automatically pushes the same stuff to GitLab.

### Add the workflow file

1. In your GitHub repo, go to the root
2. Create a folder called `.github` if it doesn't exist
3. Inside that, create `workflows` folder
4. Create a file called `sync-to-gitlab.yml` in `.github/workflows/`
5. Copy the contents from the `.github/workflows/sync-to-gitlab.yml` file in this repo
6. Commit and push it

### Set up secrets

1. In your GitHub repo, go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `GITLAB_TOKEN` - paste your GitLab token here
4. Add another secret called `GITLAB_REPO_URL` - this should be your full GitLab repo URL like `https://gitlab.com/yourusername/yourrepo.git` or `https://gitlab.yourcompany.com/group/repo.git` if self-hosted

That's it for the GitHub side.

### Test it

Make a small change, commit, push. Then check the Actions tab - you should see it running. If it worked, your GitLab repo should have the same changes.

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

**GitHub Actions not working:**
- Double-check the secrets are set (GITLAB_TOKEN and GITLAB_REPO_URL)
- Make sure your GitLab token has write_repository permission
- Check the Actions tab - the error messages are usually pretty clear

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

Once you've got both set up, you're good to go. Push to GitHub and it goes to GitLab automatically. Push to GitLab and trigger the sync job to send it to GitHub.

