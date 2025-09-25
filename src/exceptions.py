import jwt

InvalidTokenError = jwt.InvalidTokenError


class EpicEventsError(Exception):
    alert: str = __name__

    def __init__(self, message: str | None = None):
        msg = message or self.alert
        super().__init__(msg)
        self.message = msg

    def __str__(self) -> str:
        return f"{self.alert}: {self.message}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(alert={self.alert!r}, message={self.message!r})"


class OperationDeniedError(EpicEventsError):
    alert = "OPERATION DENIED"

class InvalidUsernameError(EpicEventsError):
    alert = "INVALID USERNAME"

class InvalidIdError(EpicEventsError):
    alert = "INVALID ID"

class InvalidUserIDError(EpicEventsError):
    alert = "INVALID USER ID"

class InvalidPasswordError(EpicEventsError):
    alert = "INVALID PASSWORD"

class ExpiredTokenError(EpicEventsError):
    alert = "EXPIRED TOKEN"
