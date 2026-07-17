from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = "ERROR"
    if hasattr(exc, "default_code"):
        code = str(exc.default_code).upper()
    if isinstance(exc, APIException) and exc.status_code == 400:
        code = "VALIDATION_ERROR"
    elif isinstance(exc, APIException) and exc.status_code == 403:
        code = "FORBIDDEN"
    elif isinstance(exc, APIException) and exc.status_code == 404:
        code = "NOT_FOUND"

    response.data = {
        "error": {
            "code": code,
            "message": _extract_message(response.data),
            "details": response.data if isinstance(response.data, dict) else {},
        }
    }
    return response


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        first_key = next(iter(data), None)
        if first_key and isinstance(data[first_key], list) and data[first_key]:
            return str(data[first_key][0])
    if isinstance(data, list) and data:
        return str(data[0])
    return "Request failed"
