from typing import Final

CONSOLE_INTERNAL_TOKEN: Final = "ConsoleInternalToken"
CORRELATION_ID: Final = "correlationId"


# class StepFunctionAtts:
#

# class HeadersNames:
#     CONTENT_TYPE: Final = "Content-Type"
#     ACCEPT: Final = "Accept"
#     X_CORRELATION_ID: Final = "X-Correlation-ID"
#     AUTHORIZATION: Final = "Authorization"
#     X_PCLOUD_SRC_SERVICE_NAME: Final = "X-PCLOUD-SRC-SERVICE-NAME"
#     X_PCLOUD_REQUEST_ID: Final = "X-PCLOUD-REQUEST-ID"


class EnvVarNames:

    STAGE: Final = "STAGE"
    # todo: not for now, but we need to start working with only 1 region env var.
    #AWS_REGION: Final = "AWS_REGION"
    AMAZON_REGION: Final = "AMAZON_REGION"
    AWS_ACCOUNT_ID: Final = "AWS_ACCOUNT_ID"

    DYNAMO_GSI_1: Final = "DYNAMO_GSI_1"
    TABLE_NAME: Final = "JOB_SEEKER_TABLE_NAME"


