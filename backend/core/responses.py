from rest_framework import status
from rest_framework.response import Response


def success_response(data, status_code=status.HTTP_200_OK) -> Response:
    return Response({"data": data}, status=status_code)


def error_response(
    code: str,
    message: str,
    *,
    details: dict | None = None,
    status_code=status.HTTP_400_BAD_REQUEST,
) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
        status=status_code,
    )
