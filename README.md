# jobli-service


## Prerequisite installation
You should install the following tools before starting to work
1. Install Python 3.8.+
1. Install pipenv for python dependency management 
- zsh shell (MacOS):
   ```shell script
   pip install pipenv==2018.11.26
   echo export PIPENV_VENV_IN_PROJECT=true >> ~/.zshrc
    ```
 - bash shell (Linux):
   ```shell script
   pip install pipenv==2018.11.26
   echo export PIPENV_VENV_IN_PROJECT=true >> ~/.bashrc
    ```
1. Node.js download and install from: [https://nodejs.org/en/download](https://nodejs.org/en/download/)
   Then configure [npm proxy](https://ca-il-confluence.il.cyber-ark.com/display/GRnD/Proxy+Configuration+for+Dev+Tools#ProxyConfigurationforDevTools-npm)
1. Install [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
    ```shell script
    npm install -g aws-cdk
    ```

## Getting started
1. Load your github.com ssh key in order to resolve dependencies next step
    ```shell script
    ssh-add ~/.ssh/id_rsa
    ```

1. Install dependencies
    ```shell script
    pipenv install --dev 
    ```

1. Enter virtual env by:
    ```shell script
    pipenv shell 
    ```

1. Retrieve AWS token for one day, execute the following:
   ```shell script
   saml2aws login
   ```   
   For more info go to https://github.com/Versent/saml2aws


### Deploy
In order to deploy infra-library CloudFormation stack resources for example: KMS, S3
```shell script
python deploy.py
```

### Run tests
In order to run unit tests
```shell script
pytest -v tests/unit
```
In order to run integration tests you should deploy first and then you can run 
```shell script
pytest -v tests/integration
```
In order to run all tests 
```shell script
pytest -v tests
```

### Destroy
In order to delete the CloudFormation stack deployed in the last step:
```shell script
python env_destroy.py
```