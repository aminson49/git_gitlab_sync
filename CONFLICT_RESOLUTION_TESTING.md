# Testing Conflict Resolution

I've run into various conflict scenarios while syncing repos, so I wrote this guide to help test how the script handles different situations. The sync script (`sync_repos.py`) tries to handle these automatically, but it's good to test them to make sure everything works.

## What Conflicts Can Happen

The script handles a few different conflict types:

1. **Protected branches** - GitLab branch is protected, won't allow force push
2. **Diverged branches** - GitHub and GitLab have different commits
3. **File conflicts** - Same file changed differently in both places
4. **Combination** - Protected branch AND diverged history (the worst case)

The script's approach is to always keep GitHub as the source of truth. It merges GitLab's history in but makes sure the final files match GitHub exactly. It also adds `[skip sync]` to commit messages to avoid infinite sync loops.

---

## Test Scenarios

### Test 1: Protected Branch

This is probably the most common issue - your GitLab branch is protected.

**Setup:**
1. Make a change on GitHub:
   ```bash
   echo "Test protected branch" >> test-file.txt
   git add test-file.txt
   git commit -m "Test: Protected branch scenario"
   git push origin main
   ```

2. Push something different to GitLab (if you have direct access):
   ```bash
   git clone https://gitlab.com/your-username/your-repo.git
   cd your-repo
   echo "Different content" >> test-file.txt
   git add test-file.txt
   git commit -m "GitLab change"
   git push origin main
   ```

3. Protect the branch on GitLab:
   - Go to GitLab → Settings → Repository → Protected Branches
   - Protect the `main` branch
   - Set "Allowed to push" to maintainers only (or whatever your setup is)

**Run the sync:**
```bash
export GITHUB_TOKEN="your_github_token"
export GITLAB_TOKEN="your_gitlab_token"
export GITHUB_REPO="aminson49/git_gitlab_sync"
export GITLAB_REPO="your-username/your-repo"

python sync_repos.py code github-to-gitlab
```

**What should happen:**
- Script detects the protected branch error
- Fetches from GitLab
- Merges GitLab changes but keeps GitHub version of files
- Creates a merge commit with `[skip sync]` message
- Pushes successfully

**Check it worked:**
```bash
git clone https://gitlab.com/your-username/your-repo.git
cd your-repo
git log --oneline --graph
# Should see merge commit and both histories

git show HEAD
# Files should match GitHub version
```

---

### Test 2: Diverged Branches

When both repos have commits the other doesn't know about.

**Setup:**
1. Create commits on GitHub:
   ```bash
   echo "GitHub commit 1" >> diverged-test.txt
   git add diverged-test.txt
   git commit -m "GitHub: First commit"
   git push origin main
   ```

2. Create different commits on GitLab:
   ```bash
   git clone https://gitlab.com/your-username/your-repo.git
   cd your-repo
   echo "GitLab commit 1" >> diverged-test.txt
   git add diverged-test.txt
   git commit -m "GitLab: First commit"
   git push origin main
   ```

3. Create another commit on GitHub (makes it diverge more):
   ```bash
   # Back on GitHub repo
   echo "GitHub commit 2" >> diverged-test.txt
   git add diverged-test.txt
   git commit -m "GitHub: Second commit"
   git push origin main
   ```

**Run the sync:**
```bash
python sync_repos.py code github-to-gitlab
```

**What should happen:**
- Script detects non-fast-forward error
- Fetches latest from GitLab
- Resets to GitHub version
- Merges GitLab history but keeps GitHub files
- Makes sure files match GitHub exactly
- Pushes successfully

**Check it:**
```bash
cd your-repo
git log --oneline --graph --all
# Should show merge commit with both histories

cat diverged-test.txt
# Should have GitHub content (both commits)
```

---

### Test 3: Protected Branch + Diverged History

The worst case scenario - both problems at once.

Just combine the setups from Test 1 and Test 2. Protect the branch AND create diverged commits.

The script should handle both issues, but this is a good stress test. It might do multiple merge operations.

---

### Test 4: File Conflicts

Same file changed differently in both repos.

**Setup:**
1. On GitHub:
   ```bash
   echo "GitHub version" > conflict-file.txt
   git add conflict-file.txt
   git commit -m "GitHub: Update conflict file"
   git push origin main
   ```

2. On GitLab:
   ```bash
   echo "GitLab version" > conflict-file.txt
   git add conflict-file.txt
   git commit -m "GitLab: Update conflict file"
   git push origin main
   ```

**Run sync:**
```bash
python sync_repos.py code github-to-gitlab
```

**What should happen:**
- Script merges the histories
- Uses `-X ours` strategy to keep GitHub version
- Final file should match GitHub exactly

**Check:**
```bash
cat conflict-file.txt
# Should say "GitHub version"
```

---

### Test 5: Multiple Branches

Make sure it syncs all branches, not just main.

**Setup:**
1. Create feature branch on GitHub:
   ```bash
   git checkout -b feature-branch
   echo "Feature content" >> feature.txt
   git add feature.txt
   git commit -m "Add feature"
   git push origin feature-branch
   ```

2. Create different branch on GitLab (optional, just to test):
   ```bash
   # On GitLab clone
   git checkout -b different-branch
   echo "Different content" >> different.txt
   git add different.txt
   git commit -m "Different branch"
   git push origin different-branch
   ```

**Run sync:**
```bash
python sync_repos.py code github-to-gitlab
```

**What should happen:**
- All branches from GitHub get synced
- Each branch handled separately
- All branches pushed to GitLab

**Check:**
```bash
git fetch origin
git branch -r
# Should see all GitHub branches

git checkout feature-branch
cat feature.txt
# Should have GitHub content
```

---

## Testing with Jenkins

You can test conflicts through Jenkins too. Just trigger a build manually and watch the logs. The script outputs messages when it detects conflicts and tries to resolve them.

---

## What to Verify

After running sync, make sure:

- All GitHub branches exist on GitLab
- File contents match GitHub exactly (this is the important part)
- Git history is preserved (merge commits are created)
- No force push errors
- Protected branches work
- Merge commits have `[skip sync]` message
- No infinite loops happening

---

## Issues I've Run Into

**"unrelated histories" error:**
The script uses `--allow-unrelated-histories` so this should be handled. If you still get this, might be a Git version issue.

**Files don't match GitHub:**
The script does multiple passes to ensure files match. If they don't, check the logs - something might have gone wrong with the merge strategy.

**Infinite sync loops:**
The `[skip sync]` tag should prevent this. Make sure your GitLab CI/CD (if you have it) is configured to skip commits with that tag.

**Protected branch still fails:**
Make sure your GitLab token has `write_repository` scope AND permission to push to protected branches. Some GitLab setups need you to explicitly allow API tokens to push to protected branches.

---

## Expected Output

When everything works, you should see output like:

```
Syncing aminson49/git_gitlab_sync -> your-username/your-repo
Found 3 branch(es) to sync: main, feature, develop
  Branch main needs merge (protected or diverged)
     Fetching from GitLab...
     Resetting to GitHub version...
     Creating sync commit matching GitHub exactly...
     Merging GitLab history (keeping GitHub files)...
     Ensuring files match GitHub exactly...
     Pushing to GitLab...
  Synced branch: main (merged and pushed)
  Synced branch: feature
  Synced branch: develop
Done syncing to GitLab
```

If you see errors or warnings, check the output - it usually tells you what went wrong.

---

## Quick Test Checklist

1. Set up test repos (or use real ones if you're brave)
2. Create conflict scenarios
3. Run sync script
4. Check GitLab repo matches GitHub
5. Verify merge commits look right
6. Clean up test repos

The script tries to handle most edge cases, but if you find something it doesn't handle, let me know or fix it and send a PR!
