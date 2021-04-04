@Library("shared-library") _

def SHOULD_CLEAN_ENV = false

def awsRoles = getAwsRoles()
def awsAccount = getAwsAccount()
def isProd = isProd()

pipeline {

    agent { label 'jenkins-slave-serverless' }

    parameters {
        choice(name: 'AWS_DEFAULT_OUTPUT', choices: ['json','text', 'table'], description: 'Aws cli default output')
        string(name: 'AWS_DEFAULT_REGION', defaultValue: "us-east-1", description: "Aws region to use")
        choice(name: 'CLEAN_ENV', choices: ['Yes', 'No'],
                description: 'Should clean the CloudFomation stack at the end of build')
        string(name: "PROD_TAG", defaultValue: "none", description: "Used to automatically trigger production builds from master build. Do not edit!!!")
    }

    environment {
        //Values: never/broadening/any-change
        CDK_REQUIRE_APPROVAL = "never"
        VIRTUAL_ENV = "/home/jenkins/.virtualenvs"
        PATH = "/home/jenkins/.virtualenvs/bin:${env.PATH}"
        AWS_DEFAULT_REGION = "${params.AWS_DEFAULT_REGION}"
        AWS_DEFAULT_OUTPUT = "${params.AWS_DEFAULT_OUTPUT}"
        CLEAN_ENV = "${params.CLEAN_ENV}"
        JENKINS_ROLE_ARN = "${awsRoles[awsAccount]}"
        USE_REMOTE_API = true
    }

    stages {

        stage("Init Prod Build") {
            steps {
                initProdBuild()
            }
        }

        stage("Activate Python Virtual Environment") {
           steps {
                echo "VIRTUAL_ENV = ${VIRTUAL_ENV}"
                echo "PATH = ${PATH}"
                echo "AWS_DEFAULT_REGION = ${AWS_DEFAULT_REGION}"
                echo "AWS_DEFAULT_OUTPUT = ${AWS_DEFAULT_OUTPUT}"
                echo "JENKINS_ROLE_ARN = ${env.JENKINS_ROLE_ARN}"
                echo "CLEAN_ENV = ${CLEAN_ENV}"
                sh "python3.8 -m venv ${VIRTUAL_ENV}"
           }
        }

        stage("Initialize Environment") {
            steps {
                sh "pip install --upgrade pip"
                sh "python --version"
                sh "pip --version"
                sh "aws --version"
                sh "pipenv --version"
                sh "cdk --version"
            }
        }

        stage("Consuming dependencies") {
            steps {
                withCredentials([usernamePassword(credentialsId: 'jenkins-artifactory-user', usernameVariable: 'ARTIFACTORY_USERNAME', passwordVariable: 'ARTIFACTORY_PASSWORD')]) {
                    sh "set +x && echo \"machine everest.jfrog.io\" > $HOME/.netrc && echo \"login ${ARTIFACTORY_USERNAME}\" >> $HOME/.netrc && echo \"password ${ARTIFACTORY_PASSWORD}\" >> $HOME/.netrc"

                    sh "pipenv sync --dev"
                }
            }
        }

        stage("Snyk - dependencies scan") {
            when{ expression { !isProd } }
            steps {
                withCredentials([usernamePassword(credentialsId: "jenkins-everest-github-token", usernameVariable: 'user', passwordVariable: 'gitToken')]) {
                    script {
                        env.SNYK_PROJECT_NAME = env.GIT_URL.replaceAll('https://github.com/cyberark-everest/', '').replaceAll('.git', '')
                        env.SNYK_UI = (env.BRANCH_NAME == 'master')
                    }
                    addSnykScan(gitToken, SNYK_PROJECT_NAME, SNYK_UI)
                }
            }
        }


        stage("linters - code analysis") {
            when{ expression { !isProd } }
            parallel {
                stage("static code analysis - pylint") {
                    steps {
                        sh """
                            pylint `find ${WORKSPACE} -iname "*.py" -not -path "./.venv/*"` --rcfile=${VIRTUAL_ENV}/lib/python3.8/site-packages/pylint_linter/configuration/.pylintrc -E
                        """
                    }
                }
                stage("in code security check - bandit") {
                    steps {
                        sh """
                            bandit -r ${WORKSPACE} -x ${WORKSPACE}/.venv,${WORKSPACE}/deploy.py,${WORKSPACE}/env_destroy.py -lll
                        """
                    }
                }
                stage("Code complexity scan") {
                    steps {
                        sh "radon cc -e 'tests/*' ."
                        sh "xenon --max-absolute B --max-modules A --max-average A -e 'tests/*,.venv/*' ."
                    }
                }
            }
        }


        stage("Unit tests") {
            when{ expression { !isProd } }
            steps {
                sh "pytest tests/unit -v --junitxml unit-test-results.xml --html=unit-tests-report.html --self-contained-html --cov=. --cov-report html"
            }
        }

        stage("Build lambda") {
            steps {
                sh "./build.py"
            }
        }
       
        stage("Current env: Deploy") {
            when{ expression { awsAccount != 'stage'}  }
            steps {
                script { SHOULD_CLEAN_ENV = true }
                deploy_cdk(awsAccount, awsRoles)
            }
        }

        stage("Current env: Integration tests") {
            when{ expression { awsAccount != 'stage' && !isDeployOnly() }  }
            steps {
                run_integration_tests(awsAccount, awsRoles)
           }
        }
        
        // *********  Deploy Master  *********
        stage("Master: Deploy to test environment") {
            when{ expression { awsAccount == 'stage'}  }
            steps {
                deploy_cdk('test', awsRoles)
            }
        }

        stage("Master: Integration tests on test environment") {
            when{ expression { awsAccount == 'stage'}  }
            steps {
                run_integration_tests('test', awsRoles)
           }
        }

        stage("Master: Deploy to dev environment") {
            when{ expression { awsAccount == 'stage'}  }
            steps {
                deploy_cdk('dev', awsRoles)
            }
        }

        stage("Master: Deploy to stage environment") {
            when{ expression { awsAccount == 'stage'}  }
            steps {
                deploy_cdk('stage', awsRoles)
            }
        }

        stage("Master: Integration tests on stage environment") {
            when{ expression { awsAccount == 'stage'}  }
            steps {
                run_integration_tests('stage', awsRoles)
            }
        }

        stage("cfn_nag scan") {
            when{ expression { !isProd } }
            steps {
                runCfnNag()
            }
        }

    }

    post {
        always {
           archiveArtifacts artifacts: 'cdk.out/*.*', fingerprint: true
           archiveArtifacts artifacts: '*test*.html', fingerprint: true, allowEmptyArchive: true
           archiveArtifacts artifacts: 'htmlcov/*.*', fingerprint: true, allowEmptyArchive: true
           junit allowEmptyResults: true, testResults: '*test-results.xml'
           script{
            if (!isProd && "${CLEAN_ENV}"=="Yes" && SHOULD_CLEAN_ENV == true)
                destroy_env(awsAccount, awsRoles)
           }
        }
        success {
            triggerProdBuild()
        }
    }
}

def deploy_cdk(account, awsRoles, region = env.AWS_DEFAULT_REGION) {
    withSecuredAWS(awsRoles[account], region) {
        sh "./deploy.py --no-build --deploy-env ${account} --region ${region} --require-approval ${env.CDK_REQUIRE_APPROVAL}"
    }
}

def run_integration_tests(account, awsRoles) {
    withSecuredAWS(awsRoles[account], env.AWS_DEFAULT_REGION) {
        sh "pytest tests/integration -v --junitxml integration-test-results.xml --html=integration-tests-report.html --self-contained-html --cov=.  --cov-report html"
    }
}

def destroy_env(account, awsRoles) {
    withSecuredAWS(awsRoles[account], env.AWS_DEFAULT_REGION) {
        sshagent(credentials: ['jenkins-everest-github-ssh-key']) {
            sh "./env_destroy.py"
        }
    }
}
