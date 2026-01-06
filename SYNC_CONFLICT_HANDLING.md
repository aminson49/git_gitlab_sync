# Handling Sync Conflicts (Rejected Push Errors)

## The Problem

When you see this error:
```
! [rejected] main -> main (fetch first)
error: failed to push some refs
```

This means **GitLab has commits that GitHub doesn't have**. Git is preventing the push to avoid overwriting history.

## Why This Happens

This typically occurs when:
- Someone pushed directly to GitLab (not through sync)
- GitLab CI/CD created commits
- You manually edited files in GitLab
- There was a previous sync that added commits to GitLab

## How the Script Handles It

The updated script now automatically handles this:

1. **Fetches from GitLab first** - Checks what commits exist there
2. **Tries normal push** - Attempts a regular push
3. **If rejected, tries safe force push** - Uses `--force-with-lease` which is safer than `--force`
   - `--force-with-lease` only force pushes if no one else has pushed since you last fetched
   - This prevents accidentally overwriting someone else's work

## What You'll See

### Successful Sync (No Conflicts)
```
✅ Synced branch: main
```

### Conflict Detected and Resolved
```
⚠️  Branch main rejected (GitLab has different commits)
   Attempting safe force push (--force-with-lease)...
✅ Synced branch: main (force pushed)
```

### Conflict That Couldn't Be Auto-Resolved
```
⚠️  Branch main rejected (GitLab has different commits)
   Attempting safe force push (--force-with-lease)...
⚠️  Could not sync branch main - GitLab has commits that conflict
   You may need to manually merge or resolve conflicts in GitLab
```

## Manual Resolution (If Auto-Resolution Fails)

If the script can't automatically resolve the conflict, you have a few options:

### Option 1: Accept GitLab's Version (Overwrite with GitHub)
1. Go to your GitLab repository
2. Settings → Repository → Protected Branches
3. Temporarily unprotect `main` (if protected)
4. The next sync will force push GitHub's version

### Option 2: Keep GitLab's Changes
1. Manually merge GitLab's commits into GitHub
2. Then sync will work normally

### Option 3: Reset GitLab to Match GitHub
1. In GitLab, go to Repository → Branches
2. Delete the conflicting branch
3. Re-run the sync - it will create a fresh branch from GitHub

## Best Practices

1. **Don't push directly to GitLab** - Always push to GitHub and let sync handle it
2. **Use `[skip sync]` when needed** - If you must push to GitLab directly, add `[skip sync]` to commit message
3. **Regular syncs** - More frequent syncs = fewer conflicts
4. **One-way sync** - Consider syncing only GitHub → GitLab (not both ways) to avoid conflicts

## Understanding Force Push

The script uses `--force-with-lease` which is **safer** than `--force`:

- **`--force`** - Overwrites everything, can lose commits
- **`--force-with-lease`** - Only overwrites if no one else pushed (safer)

This means:
- ✅ Safe if you're the only one syncing
- ✅ Safe if GitLab commits are from previous syncs
- ⚠️ Will fail if someone else pushed to GitLab (protects their work)

## If You Want Different Behavior

You can modify the script behavior:

### Always Force Push (Not Recommended)
Change line 125 in `sync_repos.py`:
```python
['git', 'push', '--force', 'gitlab', branch],  # Dangerous!
```

### Never Force Push (Safer, but may fail more)
Remove the force-with-lease section - sync will fail if there are conflicts, requiring manual resolution.

### Merge Instead of Force
The script already tries to merge first. If you want to always merge (never force), remove the force-with-lease fallback.

---

**TL;DR:** The script now automatically handles conflicts by using safe force push. If it still fails, you'll need to manually resolve the conflict in GitLab.

