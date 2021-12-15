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
You can also deploy faster if dependencies were not changed by running the following:
```shell script
python deploy.py --skip-deps
```

### Configure Google App credentials
Running python deploy.py will fail on missing environment variables. Do the following steps to fix this
1. Go to: https://console.cloud.google.com/apis/credentials/oauthclient/909417432201-gkh6vpm1vdel1kq95j2pd3chtu3o8vua.apps.googleusercontent.com?authuser=1&project=jobliapp1&supportedpurview=project
2. Sign in Jobli google account with jobli.akim@gmail.com user & password (you can also extract it from git secrets if you have permission)
3. Go to created .env file under the project home directory and add (replace XXXX with actual Client ID & Secret shown in link above):
GOOGLE_CLIENT_ID=XXXX
GOOGLE_CLIENT_SECRET=XXXX
4. run again: python deploy.py

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

### One time Google app configuration
Steps in creating a google application for authentication in jobli after login with google account credentials: https://console.cloud.google.com/apis
1. Create a project with Google Account ("Jobli")
2. Configure Oauth consent page: https://console.cloud.google.com/apis/credentials/consent?authuser=2&project=jobli-328707:
   * Configure application as "External" and add support email to be presented in Consent Page
   * As long "Publishing status" is in Testing status, in order to to authenticate with app using google account, you must add your email to the Test Users
3. Create an API application by going to "Credentials" section: https://console.cloud.google.com/apis/credentials?authuser=2&project=jobli-328707:
   * Give Name for for API Client (for internal use, not displayed to users).
   * Add under "Authorized JavaScript origins our cognito custom domain: https://<joblimain>.auth.<eu-west-1>.amazoncognito.com
   * Add under "Authorized JavaScript redirect URIs the cognito redirect URI: https://<joblimain>.auth.<eu-west-1>.amazoncognito.com/oauth2/idpresponse

### Deleting a seeker user data
For debug purpose, you will be able to delete yours seeker user data by creating a DELETE request via postman
You shall login to the system via the client application, get the jwt authorization token, pass it as an 'Authorization' header of a 
DELETE /api/seeker
without body. After you get successful result, reload the client application and start over as a new seeker.

### Development Notes:
Project additional dependencies can be added in Pipfile
- Runtime dependencies under [packages] section
- Development only dependencies under [dev-packages] section

Deployment of this project is done via AWS CDK tools. If you want to add/remove AWS resources, please update the following file:
- /cdk/jobli_service_cdk/service_stack/jobli_construct.py