#!/usr/bin/env python
import argparse
import getpass
import os
from jobli_service_cdk.service_stack import constants
from boto3 import session
from pathlib import Path
from infra_automation_utils.random_utils import random_password
from stack_utils.stack_name import get_stack_name
from stack_utils import environment
from build import do_build
from deploy import users
from everest_env_utils.env_mapping import DEPLOY_ENV


def init_local_dotenv():
    region = session.Session().region_name
    project_path = os.path.abspath(os.path.dirname(__file__))
    vars = {
        'DEFAULT_USER_PASSWORD': random_password(16),
        'USER_NAME': getpass.getuser(),
        'PYLINTRC': '.venv/src/tools-configuration/pylint_linter/configuration/.pylintrc',
        'COGNITO_URL': f'https://cognito-idp.{region}.amazonaws.com/',
        'USE_REMOTE_API': 'true'
    }
    environment.init_local_dotenv(project_path, vars)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--deploy-env', default='dev')
    parser.add_argument("--region", default="eu-west-1")
    parser.add_argument('--stack-name')
    parser.add_argument('--require-approval', default='broadening')
    parser.add_argument('--clean', nargs='?', const=True, help="Remove existing environment before deploying")
    parser.add_argument('--synth', nargs='?', const=True, help="Synthesize cloudformation.yml before deploying")
    parser.add_argument('--no-build', nargs='?', const=True, default=False, help="Skip lambda build")
    parser.add_argument('--skip-deps', nargs="?", const=True, default=False, help="Skip lambda dependencies")
    args = parser.parse_args()

    os.environ[DEPLOY_ENV] = args.deploy_env
    # environment update with the .env file
    init_local_dotenv()

    if not args.no_build:
        print("Building the lambda package...")
        do_build(consume_dependencies=not args.skip_deps)

    if args.clean:
        print("cdk destroy...")
        rc = os.system(f"cdk destroy")
        if rc != 0:
            print(f"cdk destroy failed with return code: {rc}")
            exit(1)

    if args.synth:
        print("cdk synth...")
        Path("cdk.out").mkdir(parents=True, exist_ok=True)
        rc = os.system(f"cdk synth --no-staging > .build{os.path.sep}template.yml")
        if rc:
            print(f"cdk synth failed with return code: {rc}")
            exit(1)

    print("cdk deploy...")
    rc = os.system(f"cdk deploy --require-approval {args.require_approval}")
    if rc:
        print(f"cdk deploy failed with return code: {rc}")
        exit(1)

    user_pool_id = users.get_user_pool_id(get_stack_name(constants.BASE_NAME))

    if args.deploy_env != 'prod':
        password = os.environ.get('DEFAULT_USER_PASSWORD', default='Password123')
        email = os.environ.get('USER_EMAIL')
        users.create_user(getpass.getuser(), password, user_pool_id, email=email)
        # additional user to simulate the JIT process
        jit_user_name: str = getpass.getuser() + '.jitUser'
        users.create_user(name=jit_user_name, password=password, user_pool_id=user_pool_id, email=f"{jit_user_name}@cyberark.com")


if __name__ == '__main__':
    main()
