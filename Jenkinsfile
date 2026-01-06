// Jenkins Pipeline for syncing GitHub to GitLab
// Place this file in the root of your GitHub repository
//
// Setup:
// 1. Install Python and Git on your Jenkins agent
// 2. Create credentials in Jenkins:
//    - github-token (Secret text) - your GitHub personal access token
//    - gitlab-token (Secret text) - your GitLab access token
// 3. Create a new Pipeline job in Jenkins
// 4. Point it to your GitHub repo
// 5. Configure webhook in GitHub (Settings → Webhooks) to trigger on push

pipeline {
    agent any
    
    triggers {
        // Option 1: Poll GitHub every 5 minutes for changes
        pollSCM('H/5 * * * *')
        
        // Option 2: Use webhook triggers (recommended)
        // Remove pollSCM and configure webhook in GitHub instead
        // Settings → Webhooks → Add webhook → Payload URL: http://your-jenkins-url/github-webhook/
    }
    
    environment {
        // These credentials should be created in Jenkins
        // Manage Jenkins → Credentials → Add Secret text
        GITHUB_TOKEN = credentials('github-token')
        GITLAB_TOKEN = credentials('gitlab-token')
        
        // Update these with your actual repo names
        GITHUB_REPO = 'username/repo'
        GITLAB_REPO = 'username/repo'
        
        // Optional: For self-hosted GitLab
        // GITLAB_API_BASE = 'https://gitlab.yourcompany.com/api/v4'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script {
                    // Try pip first, fallback to pip3
                    sh '''
                        python --version || python3 --version
                        pip install -r requirements.txt || pip3 install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Sync GitHub to GitLab') {
            steps {
                script {
                    sh '''
                        echo "🔄 Syncing from GitHub to GitLab..."
                        python sync_repos.py code github-to-gitlab || python3 sync_repos.py code github-to-gitlab
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Sync completed successfully!'
        }
        failure {
            echo '❌ Sync failed. Check the logs above for details.'
        }
        always {
            cleanWs() // Clean workspace after build
        }
    }
}

