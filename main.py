"""
OpenHands Task Runner — FastHTML web application.

Slim entry point: app creation, route registration, and serve().
All business logic lives in db/, services/, routes/, and middleware/.
"""
from dotenv import load_dotenv
load_dotenv()

from fasthtml.common import fast_app, serve, Script, Link
from starlette.staticfiles import StaticFiles

from db.queries import init_db
from middleware.auth import auth_before
from services.execution import install_thread_safe_stdout

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
app, rt = fast_app(
    pico=True,
    before=auth_before,
    hdrs=(
        Link(rel="stylesheet", href="/static/style.css"),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script(src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"),
        Script(src="/static/app.js"),
    ),
)

# Serve static assets (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------
from routes import auth as _auth, web as _web, api as _api, stream as _stream

_auth.register(app)
_web.register(app, rt)
_api.register(app)
_stream.register(app)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
init_db()
install_thread_safe_stdout()

serve()
