import os
from fasthtml.common import (
    Titled, Main, Card, Form, Label, Input, Button, Header, H2, P,
    RedirectResponse,
)
from middleware.rate_limit import login_limiter
from middleware.auth import get_client_ip

LOGIN_USER = os.getenv("LOGIN_USER")
LOGIN_PASS = os.getenv("LOGIN_PASS")

if not LOGIN_USER or not LOGIN_PASS:
    raise ValueError(
        "LOGIN_USER and LOGIN_PASS environment variables are required. "
        "Please set them in your .env file."
    )


def _login_form(error_msg=None):
    children = []
    if error_msg:
        children.append(P(error_msg, style="color: red"))
    children.append(
        Form(
            Label("Username", fr="username"),
            Input(type="text", name="username", id="username", required=True),
            Label("Password", fr="password"),
            Input(type="password", name="password", id="password", required=True),
            Button("Login", type="submit"),
            action="/login", method="post",
        )
    )
    return Titled(
        "Task runner",
        Main(
            Card(*children, header=Header(H2("Authentication Required"))),
            cls="container", style="max-width: 400px; margin-top: 100px;",
        ),
    )


def register(app):
    @app.get("/login")
    def get_login():
        return _login_form()

    @app.post("/login")
    def post_login(username: str, password: str, session, request):
        client_ip = get_client_ip(request)
        if login_limiter.is_rate_limited(client_ip):
            return _login_form("Too many login attempts. Please try again later.")

        if username == LOGIN_USER and password == LOGIN_PASS:
            session["auth"] = username
            return RedirectResponse("/", status_code=303)
        return _login_form("Invalid username or password")

    @app.get("/logout")
    def get_logout(session):
        session.pop("auth", None)
        return RedirectResponse("/login", status_code=303)
