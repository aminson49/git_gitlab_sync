# Fixing 403 Forbidden Error (GitLab Push)

If you're getting a **403 Forbidden** error when CircleCI tries to push to GitLab, this guide will help you fix it.

## The Error

```
fatal: unable to access 'https://gitlab.com/...': The requested URL returned error: 403
Failed to sync branch main: Command '['git', 'push', 'gitlab', 'main']' returned non-zero exit status 128
```

## Root Cause

A 403 error means "Forbidden" - your GitLab token doesn't have the right permissions or access.

## Solution (Step by Step)

### Step 1: Check Your GitLab Token Scopes

Your GitLab token **MUST** have these two scopes:

1. ✅ **`api`** - Full API access
2. ✅ **`write_repository`** - Write repository content

**How to check:**
1. Go to GitLab → Your Profile → Preferences → Access Tokens
2. Find your token (or create a new one)
3. Make sure BOTH `api` AND `write_repository` are checked

### Step 2: Create a New Token (Recommended)

If your token doesn't have both scopes, create a new one:

1. Go to GitLab → Preferences → Access Tokens
2. Name it: `circleci-sync` (or whatever you want)
3. **Check these scopes:**
   - ✅ `api`
   - ✅ `write_repository`
4. Set expiration (optional - leave blank for no expiration)
5. Click "Create personal access token"
6. **Copy the token immediately** (you won't see it again!)

### Step 3: Update CircleCI

1. Go to CircleCI → Your Project → Project Settings → Environment Variables
2. Find `GITLAB_TOKEN`
3. Click the edit/pencil icon
4. Paste your new token
5. Save

### Step 4: Verify Repository Access

Make sure the token owner has access to the GitLab repository:

1. Go to your GitLab repository
2. Settings → Members
3. Verify the user who created the token is listed
4. They need at least **Developer** role (or higher) to push

### Step 5: Check Repository Path

Verify your `GITLAB_REPO` environment variable is correct:

- ✅ Correct: `username/repo` or `group/repo`
- ❌ Wrong: `https://gitlab.com/username/repo.git`
- ❌ Wrong: `username/repo.git`

**For nested groups:** `group/subgroup/repo`

### Step 6: Test Again

1. Push a new commit to trigger CircleCI
2. Check the build logs
3. The 403 error should be gone!

## Still Not Working?

### For Self-Hosted GitLab

If you're using self-hosted GitLab (not gitlab.com), you may need to set an additional environment variable:

1. In CircleCI, add: `GITLAB_API_BASE`
2. Value: `https://your-gitlab-instance.com/api/v4`
3. Example: `https://gitlab.mycompany.com/api/v4`

### Token Still Not Working?

1. **Double-check token scopes** - Both `api` and `write_repository` must be checked
2. **Verify token hasn't expired** - Check expiration date
3. **Check repository is not archived** - Archived repos can't be pushed to
4. **Verify user permissions** - Token owner must have Developer+ role
5. **Try regenerating token** - Sometimes tokens get corrupted

### Quick Test

You can test your token manually:

```bash
# Test if token works
curl --header "PRIVATE-TOKEN: YOUR_TOKEN" "https://gitlab.com/api/v4/user"

# Should return your user info if token is valid
```

## Common Mistakes

❌ **Only checking `write_repository`** - You need BOTH `api` AND `write_repository`  
❌ **Using project token instead of personal token** - Use personal access token  
❌ **Token created by user without repo access** - Token owner must be a member  
❌ **Wrong repository path format** - Must be `username/repo`, not URL  
❌ **Token expired** - Check expiration date  

## Summary

The fix is almost always: **Create a new GitLab token with BOTH `api` AND `write_repository` scopes, then update it in CircleCI.**

That's it! 🎉

