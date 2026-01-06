# How the Git Sync Works

Quick rundown of how the GitHub ↔ GitLab sync is set up. There are two config files that work together to keep things in sync without creating infinite loops.

## The Two Config Files

- `.github/workflows/sync-to-gitlab.yml` - Pushes GitHub → GitLab automatically
- `.gitlab-ci.yml` - Pushes GitLab → GitHub (manual by default, but you can make it automatic)

---

## GitHub Actions (sync-to-gitlab.yml)

This one runs automatically whenever you push to `main`, `master`, or `develop`. You can also trigger it manually from the Actions tab if needed.

### What it does

When you push to GitHub, it:
1. Checks if the commit has `[skip sync]` in the message (to avoid loops)
2. Sets up GitLab as a remote using the token from secrets
3. Figures out if the branch exists on GitLab and what state it's in
4. Pushes the changes, handling conflicts and protected branches along the way

### The tricky part: handling different branch states

The push logic (around lines 48-82) deals with three scenarios:

**Branch doesn't exist on GitLab yet**
- Just push it. Simple.

**Branch exists and we can fast-forward**
- GitLab's branch is an ancestor of GitHub's branch, so a regular push works fine. No force needed, which is good for protected branches.

**Branches have diverged**
- This is where it gets interesting. The script merges GitLab's changes into GitHub's branch first, then pushes the result.
- Uses `--allow-unrelated-histories` because sometimes repos are initialized separately
- Uses `-X ours` to prefer GitHub's version when there are conflicts (since GitHub is the source of truth in this direction)
- The merge commit gets `[skip sync]` in the message so GitLab doesn't try to sync it back

### Why no force push?

Protected branches on GitLab don't allow force pushes. So instead of forcing, we merge first. It's a bit more work but it works with protected branches and keeps the history clean.

### What you need

Set these secrets in GitHub (Settings → Secrets and variables → Actions):
- `GITLAB_TOKEN` - GitLab access token with `write_repository` permission
- `GITLAB_REPO_URL` - Full GitLab repo URL like `https://gitlab.com/user/repo.git`

---

## GitLab CI (.gitlab-ci.yml)

This file has two jobs. The main one is `sync-to-github` which pushes GitLab → GitHub. There's also `sync-from-github` but that's more for pulling changes in, and it's always manual.

### sync-to-github job

Runs on Alpine Linux (lightweight, fast). By default it's manual - you have to click the "Play" button in GitLab's pipeline UI. Change `when: manual` to `when: on_success` on line 74 if you want it automatic.

**The script does:**
1. Checks for `[skip sync]` (same loop prevention)
2. Sets up GitHub as a remote
3. Figures out what branch we're on (tries `CI_COMMIT_REF_NAME` first, falls back to `CI_COMMIT_BRANCH`)
4. Checks out the branch explicitly (sometimes needed)
5. Embeds the GitHub token in the remote URL for auth
6. Pushes to GitHub

**Important:** If the push fails, the job actually fails (exits with code 1). The old version just printed an error but still passed, which was confusing.

### sync-from-github job

This one pulls from GitHub and merges into GitLab. It's always manual and only runs on scheduled pipelines or web triggers. Honestly, I don't use this one much - the GitHub Actions workflow handles GitHub → GitLab automatically.

### What you need

Set these variables in GitLab (Settings → CI/CD → Variables):
- `GITHUB_TOKEN` - GitHub personal access token with `repo` scope
- `GITHUB_REPO_URL` - Full GitHub repo URL like `https://github.com/user/repo.git`

---

## How they work together

Here's the typical flow:

1. You push to GitHub → GitHub Actions runs automatically → syncs to GitLab
2. You push to GitLab → GitLab CI runs (if automatic) → syncs to GitHub

The `[skip sync]` check prevents loops. When GitHub syncs to GitLab and creates a merge commit, that commit has `[skip sync]` in the message. So when GitLab tries to sync back, it sees that message and skips it. Same thing happens the other way.

### Conflict handling

- **GitHub → GitLab**: Uses `-X ours`, so GitHub wins. Makes sense since GitHub is the source.
- **GitLab → GitHub**: Standard merge, no preference. Might need manual resolution if conflicts are bad.

### Protected branches

Both configs avoid force pushes. They merge first, then push. This works with protected branches and keeps history intact.

---

## Common issues

**GitHub Actions not running?**
- Check the secrets are actually set
- Make sure the GitLab token has write permissions
- Check the Actions tab - the error messages are usually pretty clear
- Is your branch in the list? (main, master, or develop)

**GitLab CI not syncing?**
- Is it set to manual? You have to click the play button
- Check the CI/CD variables are set
- Make sure the GitHub token has `repo` scope
- Look at the pipeline logs

**Protected branch errors?**
- Both configs should avoid force pushes now
- If you're still seeing errors, check that tokens have permission to push to protected branches
- The workflows merge first, then push, so it should work

**Merge conflicts?**
- GitHub → GitLab: Auto-resolved (GitHub version wins)
- GitLab → GitHub: Might need manual fix
- Use `[skip sync]` in your commit message if you need to skip a sync

---

## Tips

- Add `[skip sync]` to commit messages when you don't want to trigger sync
- Don't commit tokens. Use secrets/variables.
- Watch both GitHub Actions and GitLab pipelines - if something breaks, you'll see it there
- Test with manual triggers first before making things automatic
- Fix conflicts early before they cause bigger problems

---

## Quick reference

- **GitHub → GitLab**: Automatic, runs on push to main/master/develop
- **GitLab → GitHub**: Manual by default (change line 74 to make it automatic)
- **Loop prevention**: `[skip sync]` in commit messages
- **Protected branches**: Both handle them by merging first, no force push
- **Unrelated histories**: Both support repos that were created separately

That's pretty much it. The configs are set up to handle most edge cases, but if something breaks, check the logs - they usually tell you what's wrong.
