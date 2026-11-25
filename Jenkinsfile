
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
    }

    environment {
        PYTHON = '/opt/anaconda3/bin/python3.13'
        STRIPE_SECRET_KEY = 'sk_test_ci_placeholder'
        STRIPE_WEBHOOK_SECRET = 'whsec_ci_placeholder'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Environment') {
            steps {
                sh '''
                    echo "Checking Python..."
                    "$PYTHON" --version

                    echo "Checking PostgreSQL..."
                    /opt/homebrew/bin/pg_isready \
                      -h 127.0.0.1 -p 5433 \
                      -U stripe_app -d stripe_billing
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    "$PYTHON" -m venv .jenkins-venv
                    .jenkins-venv/bin/python -m pip install --upgrade pip
                    .jenkins-venv/bin/pip install -r requirements.txt
                    .jenkins-venv/bin/pip install pytest-cov
                '''
            }
        }

        stage('Initialize Database') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'ci-database-password',
                        variable: 'DB_PASSWORD'
                    )
                ]) {
                    sh '''
                        set +x
                        export DATABASE_URL="postgresql+psycopg://stripe_app:${DB_PASSWORD}@127.0.0.1:5433/stripe_billing"

                        .jenkins-venv/bin/python \
                          -m app.src.database.init_db
                    '''
                }
            }
        }

        stage('Run Pytest') {
            steps {
                withCredentials([
                    string(
                        credentialsId: 'ci-database-password',
                        variable: 'DB_PASSWORD'
                    )
                ]) {
                    sh '''
                        set +x
                        export DATABASE_URL="postgresql+psycopg://stripe_app:${DB_PASSWORD}@127.0.0.1:5433/stripe_billing"

                        mkdir -p reports

                        .jenkins-venv/bin/python -m pytest -v \
                          --cov=app \
                          --cov-report=term-missing \
                          --cov-report=xml:reports/coverage.xml \
                          --junitxml=reports/pytest-results.xml \
                          --ignore=app/tests/stripe_integration_test.py
                    '''
                }
            }
        }
    }

    post {
        always {
            junit(
                allowEmptyResults: true,
                testResults: 'reports/pytest-results.xml'
            )

            archiveArtifacts(
                artifacts: 'reports/coverage.xml',
                allowEmptyArchive: true
            )
        }

        success {
            echo 'CI pipeline completed successfully!'
        }

        failure {
            echo 'CI pipeline failed. Check the stage logs.'
        }
    }
}

