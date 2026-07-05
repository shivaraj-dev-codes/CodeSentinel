"""Custom exception handler — wraps all errors in the standard envelope."""
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Wrap DRF exceptions in:
    { "success": false, "error": { "code": "...", "message": "...", "details": {} } }
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Map HTTP status to a readable code
        code = getattr(exc, "default_code", "ERROR").upper()
        message = str(exc.detail) if hasattr(exc, "detail") else str(exc)

        # Flatten single-key detail dicts into a friendlier message
        if isinstance(getattr(exc, "detail", None), dict):
            details = exc.detail
            # Pick the first field's first message as the primary message
            for field, msgs in details.items():
                if isinstance(msgs, list) and msgs:
                    message = str(msgs[0])
                    break
        else:
            details = {}

        response.data = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details if isinstance(details, dict) else {},
            },
        }

    return response
