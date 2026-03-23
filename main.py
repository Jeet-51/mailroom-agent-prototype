# main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from orchestrator import run_pipeline, clear_cache

load_dotenv()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # dev only — remove in production HTTPS

app = FastAPI(title="Legal Mailroom Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─── OAuth state ─────────────────────────────────────────────────────────────
# In production: use a proper session store (Redis, DB)
_oauth_state: dict = {}

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth/callback")


def gmail_connected() -> bool:
    return os.path.exists("token.json")


# ─── Pages ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"gmail_connected": gmail_connected()}
    )


# ─── Gmail OAuth ─────────────────────────────────────────────────────────────

@app.get("/auth/login")
async def auth_login():
    """Step 1: redirect user to Google consent screen."""
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")
    # Store the ENTIRE flow object so the code verifier (PKCE) is preserved
    _oauth_state["flow"]  = flow
    _oauth_state["state"] = state
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Step 2: Google redirects here — reuse the same flow object to preserve PKCE."""
    flow = _oauth_state.get("flow")
    if not flow:
        return RedirectResponse("/")   # session expired, try again
    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials
    with open("token.json", "w") as f:
        f.write(creds.to_json())
    _oauth_state.clear()
    return RedirectResponse("/?gmail=connected")


@app.get("/auth/status")
async def auth_status():
    return {"connected": gmail_connected()}


@app.post("/auth/disconnect")
async def auth_disconnect():
    if os.path.exists("token.json"):
        os.remove("token.json")
    return {"disconnected": True}


# ─── Pipeline ────────────────────────────────────────────────────────────────

@app.post("/run")
async def run_agent(request: Request):
    body = await request.json()
    use_gmail = body.get("use_gmail", False)
    hours = body.get("hours", 4)
    todos = await run_pipeline(use_gmail=use_gmail, hours=hours)
    return {"todos": todos}


@app.post("/cache/clear")
async def cache_clear():
    """Force reprocess all emails on next run."""
    clear_cache()
    return {"cleared": True}
