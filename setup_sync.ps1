# Quick setup script for syncing GitHub and GitLab
# Just run this and it'll ask you for the stuff you need

Write-Host "Setting up GitHub/GitLab sync..." -ForegroundColor Cyan
Write-Host ""

# Check git
try {
    $gitVersion = git --version
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Need Git installed first!" -ForegroundColor Red
    exit 1
}

# Check python
try {
    $pythonVersion = python --version
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found - some features won't work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Let's configure things:" -ForegroundColor Cyan
Write-Host ""

# Get repos
$githubRepo = Read-Host "GitHub repo (username/repo)"
if ($githubRepo) {
    $env:GITHUB_REPO = $githubRepo
    [System.Environment]::SetEnvironmentVariable('GITHUB_REPO', $githubRepo, 'User')
    Write-Host "Set GitHub repo: $githubRepo" -ForegroundColor Green
}

$gitlabRepo = Read-Host "GitLab repo (username/repo)"
if ($gitlabRepo) {
    $env:GITLAB_REPO = $gitlabRepo
    [System.Environment]::SetEnvironmentVariable('GITLAB_REPO', $gitlabRepo, 'User')
    Write-Host "Set GitLab repo: $gitlabRepo" -ForegroundColor Green
}

# Get tokens
Write-Host ""
Write-Host "GitHub token (get it from https://github.com/settings/tokens)" -ForegroundColor Yellow
Write-Host "Need: repo, workflow scopes" -ForegroundColor Gray
$githubToken = Read-Host "GitHub token (or Enter to skip)"
if ($githubToken) {
    $env:GITHUB_TOKEN = $githubToken
    [System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', $githubToken, 'User')
    Write-Host "GitHub token saved" -ForegroundColor Green
}

Write-Host ""
Write-Host "GitLab token (get it from https://gitlab.com/-/user_settings/personal_access_tokens)" -ForegroundColor Yellow
Write-Host "Need: api, write_repository scopes" -ForegroundColor Gray
$gitlabToken = Read-Host "GitLab token (or Enter to skip)"
if ($gitlabToken) {
    $env:GITLAB_TOKEN = $gitlabToken
    [System.Environment]::SetEnvironmentVariable('GITLAB_TOKEN', $gitlabToken, 'User')
    Write-Host "GitLab token saved" -ForegroundColor Green
}

Write-Host ""
Write-Host "Installing python packages..." -ForegroundColor Cyan
try {
    pip install -r requirements.txt
    Write-Host "Done!" -ForegroundColor Green
} catch {
    Write-Host "Failed - try running: pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "All set!" -ForegroundColor Green
Write-Host ""
Write-Host "Next:" -ForegroundColor Cyan
Write-Host "  - Add the workflow files to your repos" -ForegroundColor White
Write-Host "  - Set up secrets in GitHub/GitLab" -ForegroundColor White
Write-Host "  - Run: python sync_repos.py" -ForegroundColor White
Write-Host ""

