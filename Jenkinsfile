pipeline {
    agent any
    
    triggers {
        pollSCM('H/5 * * * *')
    }
    
    environment {
        GITHUB_TOKEN = credentials('github-token')
        GITLAB_TOKEN = credentials('gitlab-token')
        GITHUB_REPO = 'username/repo'
        GITLAB_REPO = 'username/repo'
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

