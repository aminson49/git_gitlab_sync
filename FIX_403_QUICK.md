# Quick Fix for 403 Error - Step by Step

If you're still getting 403 errors after checking token scopes, follow these steps **exactly**:

## Step 1: Delete Your Old Token

1. Go to GitLab → Your Profile → Preferences → Access Tokens
2. Find your current token (the one in CircleCI)
3. **Delete it** (or just create a new one - you can have multiple)

## Step 2: Create a NEW Token with EXACT Scopes

1. Still in GitLab → Preferences → Access Tokens
2. Click "Add new token"
3. **Token name:** `circleci-sync-v2` (or any name)
4. **Expiration date:** Leave blank (or set far in future)
5. **Select scopes:** Check **ONLY** these two:
   - ✅ **`api`** (Full API access)
   - ✅ **`write_repository`** (Write repository content)
6. **DO NOT check any other boxes!**
7. Click "Create personal access token"
8. **IMMEDIATELY copy the token** - you won't see it again!

## Step 3: Verify Token Owner Has Repository Access

1. Go to your GitLab repository
2. Settings → Members
3. Find the user who created the token
4. They must have at least **Developer** role (or Maintainer/Owner)
5. If they're not a member, add them with Developer+ role

## Step 4: Update CircleCI

1. Go to CircleCI → Your Project → Project Settings → Environment Variables
2. Find `GITLAB_TOKEN`
3. Click the edit/pencil icon
4. **Delete the old token value completely**
5. **Paste the new token** (from Step 2)
6. Click "Update" or "Save"

## Step 5: Verify Repository Path Format

1. Still in CircleCI Environment Variables
2. Check `GITLAB_REPO` value
3. It should be: `username/repo` or `group/repo`
4. **NOT:** `https://gitlab.com/username/repo.git`
5. **NOT:** `username/repo.git`
6. **NOT:** `gitlab.com/username/repo`

**Examples:**
- ✅ `priyam/myproject`
- ✅ `mygroup/myproject`
- ✅ `mygroup/subgroup/myproject`
- ❌ `https://gitlab.com/priyam/myproject.git`

## Step 6: Test the Fix

1. Push a new commit to your GitHub repo (or re-run the CircleCI job)
2. Watch the CircleCI logs
3. The new validation will show:
   - ✅ GitLab token is valid and can authenticate
   - ✅ Token has access to repository
   - ✅ Repository permissions check passed

If you still see 403 errors after this, the logs will now tell you exactly what's wrong.

## Common Mistakes

❌ **Only checking `write_repository`** - You MUST check BOTH `api` AND `write_repository`  
❌ **Token owner not a repository member** - They must be added as a member  
❌ **Wrong repository path** - Must be `username/repo`, not a URL  
❌ **Using expired token** - Check expiration date  
❌ **Token created for wrong user** - Make sure the right user creates it  

## Still Not Working?

If you've done all the above and still get 403:

1. **Check the CircleCI logs** - The new validation will show exactly what's wrong
2. **Try a different GitLab user** - Create token with a user who definitely has access
3. **Check if repository is archived** - Archived repos can't be pushed to
4. **Verify GitLab instance** - If self-hosted, you may need `GITLAB_API_BASE` variable

## Test Token Manually

You can test your token works before using it in CircleCI:

```bash
# Replace YOUR_TOKEN and username/repo with your values
curl --header "PRIVATE-TOKEN: YOUR_TOKEN" \
  "https://gitlab.com/api/v4/projects/username%2Frepo"

# Should return JSON with project info if token works
# If you get 403, token doesn't have access
# If you get 404, repository path is wrong
```

---

**The fix is almost always:** Create a fresh token with BOTH scopes, verify the user has repo access, and update CircleCI. That's it! 🎯

