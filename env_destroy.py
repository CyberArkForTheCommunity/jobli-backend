#!/usr/bin/env python
# pylint: disable = print-used
import os
from dotenv import load_dotenv

# pylint: disable=invalid-name
load_dotenv()
rc = os.system(f"cdk destroy")
if rc != 0:
    print(f"cdk destroy failed with return code: {rc}")
    exit(1)
