class CommonException(Exception):
    def __init__(self, message: str = None):
        self.description = str(message) if message else "Internal Server Error"
        self.status_code = 500

    def __str__(self):
        return str(self.description)


class InternalServerErrorError(CommonException):
    description = "Internal Server Error"
    status_code = 500


class FormattedCommonException(CommonException):
    def __str__(self):
        return self.description.format(*self.args)


class BadRequestError(CommonException):
    def __init__(self, message):
        self.description = message
        self.status_code = 400


class ConflictError(CommonException):
    def __init__(self, message):
        self.description = message
        self.status_code = 409


class NotFoundError(CommonException):
    def __init__(self, message):
        self.description = message
        self.status_code = 404


class CertificateValidationError(CommonException):
    def __init__(self, message):
        self.description = message
        self.status_code = 400


class RequestEntityTooLargeError(CommonException):
    def __init__(self, message):
        self.description = message
        self.status_code = 413


class MissingParameterError(CommonException):
    def __init__(self):
        self.description = "parameter {} not found in event.input"
        self.status_code = 500


class MissingContextCorrelationId(Exception):
    pass


class MissingEnvironmentVariableError(CommonException):
    status_code = 500
    description: str = "Environment variable '{}' is not defined"

    def __init__(self, env_var_name: str):
        super().__init__(f"Missing environment variable: '{env_var_name}'")


class ResourceNotFoundError(NotFoundError):

    def __init__(self, env_var_name: str):
        self.status_code = 404
        super().__init__(f"Resource not found: '{env_var_name}'")