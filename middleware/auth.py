import os
from starlette.responses import JSONResponse, RedirectResponse
from middleware.rate_limit import login_limiter, api_limiter

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    import warnings
    warnings.warn(
        "API_KEY environment variable is not set. All /api/* endpoints will be disabled.",
        stacklevel=2
    )


def get_client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.scope.get("client")
    return client[0] if client else "unknown"


def auth_before(request, session):
    """Authentication middleware for all routes."""
    path = request.scope["path"]

    # Public paths
    if path in ("/login", "/favicon.ico") or path.startswith("/static"):
        return

    # API authentication via API key
    if path.startswith("/api/"):
        client_ip = get_client_ip(request)
        if api_limiter.is_rate_limited(client_ip):
            return JSONResponse({"error": "Rate limit exceeded. Try again later."}, status_code=429)

        api_key = (
            request.headers.get("X-API-Key")
            or request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        )
        if not API_KEY or api_key != API_KEY:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return

    # Web session authentication
    if "auth" not in session:
        return RedirectResponse("/login", status_code=303)
