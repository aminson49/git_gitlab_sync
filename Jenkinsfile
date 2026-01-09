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
        GITLAB_REPO = 'poc-group1603702/gitlab_github_sync'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . ./venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Sync GitHub to GitLab') {
            steps {
                sh '''
                    . ./venv/bin/activate
                    python sync_repos.py code github-to-gitlab
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}

