import os

from dotenv import load_dotenv

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    current_app,
    request,
)

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.models.email_account import EmailAccount

from app.email_intelligence.oauth_service import save_credentials
from app.email_intelligence.gmail_service import get_recent_messages
from app.email_intelligence.sync_service import sync_gmail_reports

load_dotenv()

if os.getenv("FLASK_DEBUG") == "1":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

email_bp = Blueprint(
    "email",
    __name__,
    url_prefix="/email"
)


def get_gmail_redirect_uri():
    configured_uri = current_app.config.get("GMAIL_REDIRECT_URI")

    if configured_uri:
        return configured_uri

    return url_for(
        "email.oauth2callback",
        _external=True,
    )


def require_gmail_oauth_config():
    missing = [
        key for key in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET")
        if not current_app.config.get(key)
    ]

    if missing:
        raise RuntimeError(
            "Missing Gmail OAuth environment variable(s): "
            + ", ".join(missing)
        )


def create_flow(state=None):

    require_gmail_oauth_config()

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": current_app.config["GMAIL_CLIENT_ID"],
                "client_secret": current_app.config["GMAIL_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=current_app.config["GMAIL_SCOPES"],
        state=state,
        autogenerate_code_verifier=True,
    )

    flow.redirect_uri = get_gmail_redirect_uri()

    return flow


@email_bp.route("/")
def dashboard():

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )

    account = EmailAccount.query.first()

    return render_template(
        "email/dashboard.html",
        account=account,
    )


@email_bp.route("/connect")
def connect_gmail():

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )

    flow = create_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    session["oauth_state"] = state
    session["code_verifier"] = flow.code_verifier

    return redirect(
        authorization_url
    )


@email_bp.route("/oauth2callback")
def oauth2callback():

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )

    flow = create_flow(
        state=session.get("oauth_state")
    )

    flow.code_verifier = session.get(
        "code_verifier"
    )

    flow.fetch_token(
        authorization_response=request.url
    )

    credentials = flow.credentials

    gmail = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    profile = gmail.users().getProfile(
        userId="me"
    ).execute()

    email_address = profile["emailAddress"]

    save_credentials(
        email_address,
        credentials
    )

    return (
        f"<h2>✅ Gmail Connected Successfully</h2>"
        f"<p><strong>Email:</strong> {email_address}</p>"
        f"<p>Credentials saved successfully.</p>"
        f'<p><a href="/email/messages">View Latest Emails</a></p>'
    )


@email_bp.route("/messages")
def messages():

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )

    messages = get_recent_messages(10)

    return render_template(
        "email/messages.html",
        messages=messages,
    )
@email_bp.route("/sync")
def sync():

    if not session.get("logged_in"):
        return redirect(
            url_for("auth.login")
        )

    summary = sync_gmail_reports()

    return render_template(
        "email/sync_results.html",
        summary=summary,
    )   
