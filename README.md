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

### NOTES
 - In handler.py file there is a constant of USER_ID = "11111" until Authorization token will be supported on the client
side. This is the only user that is used hard coded until it will be taken from the auth token.
   When authorization token will be available, please search for all "user_id = USER_ID" and remove the remark as below:

 # TODO user_id = event.request_context.authorizer.claims["sub"]
 user_id = USER_ID
 
remove the user_id = USER_ID line and use user_id = event.request_context.authorizer.claims["sub"] 

 - Enable the authorizer in jobli_construct.py by replacing this code at the end of the file
   ```shell script
   @staticmethod
    def __add_resource_method(resource: apigw.Resource, http_method: str, integration: apigw.LambdaIntegration,
                              authorizer: apigw.CfnAuthorizer) -> None:
        method = resource.add_method(
            http_method=http_method,
            integration=integration
        )
   ```
   
   with this
   ```shell script
     @staticmethod
     def __add_resource_method(resource: apigw.Resource, http_method: str, integration: apigw.LambdaIntegration,
                               authorizer: apigw.CfnAuthorizer) -> None:
         method = resource.add_method(
             http_method=http_method,
             integration=integration,
             authorization_type=apigw.AuthorizationType.COGNITO,
         )
         method_resource: apigw.Resource = method.node.find_child("Resource")
         method_resource.add_property_override("AuthorizerId", {"Ref": authorizer.logical_id})
   ```
   After you run deploy.py it will set the authorizer for all APIs in the API GW.