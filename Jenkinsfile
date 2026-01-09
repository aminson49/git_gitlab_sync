pipeline {
    agent any
    
    // Webhook trigger (configure in Jenkins job) + polling as backup
    triggers {
        pollSCM('H/15 * * * *')  // Backup polling every 15 minutes if webhook fails
    }
    
    environment {
        GITHUB_TOKEN = credentials('github-token')
        GITLAB_TOKEN = credentials('gitlab-token')
        GITHUB_REPO = 'aminson49/git_gitlab_sync'
        GITLAB_REPO = 'username/repo'  // Update this with your GitLab repo
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt || pip3 install -r requirements.txt'
            }
        }
        
        stage('Sync GitHub to GitLab') {
            steps {
                sh 'python sync_repos.py code github-to-gitlab || python3 sync_repos.py code github-to-gitlab'
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}

