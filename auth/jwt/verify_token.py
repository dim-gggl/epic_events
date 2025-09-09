import jwt
from auth.utils import get_secret_key
from crm.views.views import MainView
from exceptions import InvalidTokenError, ExpiredTokenError
from sentry.observability import log_authentication_event, log_error, log_operation

view = MainView()

SECRET_KEY = get_secret_key()


def verify_access_token(token: str) -> dict | str:
    """
    Verify JWT access token and return payload.
    
    Args:
        token: JWT access token string
        
    Returns:
        dict: Token payload containing user information
        str: If the payload cannot be extracted from the JWT,
        returns an error message containing the necessary
        information to understand what failed.
        
    """
    if not token:
        log_authentication_event(
            "token_verification_failed",
            success=False,
            context={"reason": "no_token_provided"}
        )
        view.wrong_message("You must authenticate first.")
        return "No token provided"
        
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=["HS256"])
        # Validate that required fields are present
        if 'sub' not in payload or 'role_id' not in payload:
            log_authentication_event(
                "token_verification_failed",
                success=False,
                context={"reason": "missing_required_fields", "user_id": payload.get('sub')}
            )
            raise InvalidTokenError("Token missing required fields")
        
        # Log successful token verification
        log_authentication_event(
            "token_verification_success",
            success=True,
            context={"user_id": payload.get('sub'), "role_id": payload.get('role_id')}
        )
        
        return payload

    except jwt.ExpiredSignatureError as e:
        log_authentication_event(
            "token_verification_failed",
            success=False,
            context={"reason": "expired_signature", "error": str(e)}
        )
        reason = f"EXPIRED SIGNATURE IN YOUR TOKEN\n{e}"
        view.wrong_message(reason)
        return reason

    except jwt.InvalidTokenError as e:
        log_authentication_event(
            "token_verification_failed",
            success=False,
            context={"reason": "invalid_token", "error": str(e)}
        )
        reason = f"INVALID TOKEN\n{str(e)}"
        view.wrong_message(reason)
        return reason

    except Exception as e:
        log_error(
            e,
            context={
                "operation": "token_verification",
                "error_type": "verification_error"
            }
        )
        reason = f"TOKEN VERIFICATION FAILED \n{str(e)}"
        view.wrong_message(reason)
        return reason

