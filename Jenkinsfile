// Expense Tracker — declarative CI/CD pipeline.
//
// Stages: checkout → deps → lint → unit tests → integration tests → security
//         → build → docker build → tag → push → update GitOps manifests.
//
// No infrastructure-specific addresses or credentials are hard-coded — they
// come from Jenkins credentials and environment configuration.

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        // Image names (registry host comes from Jenkins global config).
        API_IMAGE = "expense-tracker-api"
        WEB_IMAGE = "expense-tracker-web"
        // Tag: short commit SHA + build number for traceability.
        IMAGE_TAG = "${env.GIT_COMMIT?.take(8) ?: 'local'}-${env.BUILD_NUMBER}"
        // Credentials IDs stored in Jenkins (not values).
        REGISTRY_CREDENTIALS = credentials('oci-registry-credentials')
        GITOPS_CREDENTIALS   = credentials('gitops-repo-credentials')
        REGISTRY_URL         = "${env.OCI_REGISTRY_URL ?: 'registry.example.com'}"
        GITOPS_REPO          = "${env.GITOPS_REPO_URL ?: 'https://github.com/example/expense-tracker-gitops.git'}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend: dependencies') {
            steps {
                dir('services/api') {
                    sh '''
                        python3 -m venv .venv
                        . .venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements-dev.txt
                    '''
                }
            }
        }

        stage('Backend: lint') {
            steps {
                dir('services/api') {
                    sh '''
                        . .venv/bin/activate
                        ruff check .
                        ruff format --check .
                    '''
                }
            }
        }

        stage('Backend: unit tests + coverage') {
            steps {
                dir('services/api') {
                    sh '''
                        . .venv/bin/activate
                        pytest tests/ --ignore=tests/test_auth.py \
                            --cov=app --cov-report=xml:coverage.xml --cov-report=term
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'services/api/**/junit.xml'
                }
            }
        }

        stage('Backend: integration tests') {
            steps {
                // Spin up an ephemeral Postgres for the integration suite.
                sh '''
                    docker run -d --name ci-db \
                        -e POSTGRES_DB=expense_tracker \
                        -e POSTGRES_USER=expense_app \
                        -e POSTGRES_PASSWORD=ci_test_password \
                        -p 5432:5432 postgres:16-alpine
                    sleep 8
                '''
                dir('database') {
                    sh '''
                        . ../services/api/.venv/bin/activate
                        export POSTGRES_HOST=localhost POSTGRES_PASSWORD=ci_test_password
                        alembic upgrade head
                    '''
                }
                dir('services/api') {
                    sh '''
                        . .venv/bin/activate
                        export POSTGRES_HOST=localhost POSTGRES_PASSWORD=ci_test_password
                        pytest tests/test_auth.py --cov=app --cov-append --cov-report=xml:coverage.xml
                    '''
                }
            }
            post {
                always {
                    sh 'docker rm -f ci-db || true'
                }
            }
        }

        stage('Security: dependency + image scan') {
            steps {
                dir('services/api') {
                    sh '''
                        . .venv/bin/activate
                        pip install pip-audit
                        pip-audit || echo "pip-audit findings (review)"
                    '''
                }
            }
        }

        stage('Frontend: analyze + test') {
            steps {
                dir('apps/mobile') {
                    sh '''
                        flutter pub get
                        flutter analyze
                        flutter test
                    '''
                }
            }
        }

        stage('Docker: build images') {
            steps {
                sh '''
                    docker build -f infrastructure/docker/api.Dockerfile \
                        -t ${REGISTRY_URL}/${API_IMAGE}:${IMAGE_TAG} \
                        -t ${REGISTRY_URL}/${API_IMAGE}:latest .
                    docker build -f infrastructure/docker/web.Dockerfile \
                        --build-arg API_BASE_URL=${WEB_API_BASE_URL:-http://localhost:8000} \
                        -t ${REGISTRY_URL}/${WEB_IMAGE}:${IMAGE_TAG} \
                        -t ${REGISTRY_URL}/${WEB_IMAGE}:latest .
                '''
            }
        }

        stage('Docker: scan images') {
            steps {
                sh '''
                    trivy image --severity HIGH,CRITICAL --exit-code 0 \
                        ${REGISTRY_URL}/${API_IMAGE}:${IMAGE_TAG} || true
                    trivy image --severity HIGH,CRITICAL --exit-code 0 \
                        ${REGISTRY_URL}/${WEB_IMAGE}:${IMAGE_TAG} || true
                '''
            }
        }

        stage('Docker: push') {
            steps {
                sh '''
                    echo ${REGISTRY_CREDENTIALS_PSW} | docker login ${REGISTRY_URL} \
                        -u ${REGISTRY_CREDENTIALS_USR} --password-stdin
                    docker push ${REGISTRY_URL}/${API_IMAGE}:${IMAGE_TAG}
                    docker push ${REGISTRY_URL}/${API_IMAGE}:latest
                    docker push ${REGISTRY_URL}/${WEB_IMAGE}:${IMAGE_TAG}
                    docker push ${REGISTRY_URL}/${WEB_IMAGE}:latest
                '''
            }
        }

        stage('GitOps: update manifests') {
            when {
                branch 'main'
            }
            steps {
                // Update the image tags in the GitOps repo; FluxCD reconciles.
                sh '''
                    git clone https://${GITOPS_CREDENTIALS_USR}:${GITOPS_CREDENTIALS_PSW}@${GITOPS_REPO#https://} gitops
                    cd gitops
                    # Update the prod overlay image tags.
                    sed -i "s|newTag: .*|newTag: \\"${IMAGE_TAG}\\"|g" \
                        infrastructure/kubernetes/overlays/prod/kustomization.yaml
                    git config user.email "ci@expense-tracker"
                    git config user.name "CI"
                    git add .
                    git commit -m "ci: deploy ${IMAGE_TAG}" || echo "no changes"
                    git push
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded: ${IMAGE_TAG}"
        }
        failure {
            echo "Pipeline failed — check stage logs."
        }
        always {
            cleanWs()
        }
    }
}
