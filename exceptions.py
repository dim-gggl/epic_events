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
    alert = "❌ Invalid username"

class InvalidUserIDError(EpicEventsError):
    alert = "❌ Invalid user id"

class InvalidPasswordError(EpicEventsError):
    alert = "❌ Invalid password"

class InvalidTokenError(EpicEventsError):
    alert = "❌ Invalid token"

class ExpiredTokenError(EpicEventsError):
    alert = "❌ Expired token"

class NoRefreshTokenSavedError(EpicEventsError):
    alert = "❌ No refresh token saved"