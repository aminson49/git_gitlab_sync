# Quick checklist

Just checking things off as you go.

## Get tokens first

- [ ] Got GitHub token (repo + workflow scopes)
- [ ] Got GitLab token (api + write_repository scopes)
- [ ] Both repos exist and I can push to them

## GitHub Actions setup (GitHub → GitLab)

- [ ] Added `.github/workflows/sync-to-gitlab.yml` to GitHub repo
- [ ] Set `GITLAB_TOKEN` secret in GitHub
- [ ] Set `GITLAB_REPO_URL` secret in GitHub  
- [ ] Pushed a test commit to GitHub
- [ ] Checked Actions tab - workflow ran
- [ ] Verified the change showed up in GitLab

## GitLab CI setup (GitLab → GitHub)

- [ ] Added `.gitlab-ci.yml` to GitLab repo
- [ ] Set `GITHUB_TOKEN` variable in GitLab CI/CD
- [ ] Set `GITHUB_REPO_URL` variable in GitLab CI/CD
- [ ] Pushed a test commit to GitLab
- [ ] Ran the sync job manually (clicked play button)
- [ ] Verified the change showed up in GitHub

## Make sure it works both ways

- [ ] Pushed to GitHub, checked GitLab (worked)
- [ ] Pushed to GitLab, triggered sync, checked GitHub (worked)
- [ ] Tested `[skip sync]` in a commit message (didn't sync)
- [ ] No weird loops happening

All done! Both repos should be syncing now.

