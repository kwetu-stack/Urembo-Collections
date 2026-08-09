import os

from dotenv import load_dotenv

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    current_app,
    request,
)

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.models.email_account import EmailAccount
from app.email_intelligence.oauth_service import save_credentials
from app.email_intelligence.sync_service import sync_gmail_reports


load_dotenv()


if os.getenv("FLASK_DEBUG") == "1":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


email_bp = Blueprint(
    "email",
    __name__,
    url_prefix="/email",
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
        key
        for key in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET")
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
    account = EmailAccount.query.first()

    return render_template(
        "email/dashboard.html",
        account=account,
    )


@email_bp.route("/connect")
def connect_gmail():
    flow = create_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    from flask import session

    session["oauth_state"] = state
    session["code_verifier"] = flow.code_verifier

    return redirect(authorization_url)


@email_bp.route("/oauth2callback")
def oauth2callback():
    from flask import session

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
        credentials=credentials,
    )

    profile = (
        gmail.users()
        .getProfile(userId="me")
        .execute()
    )

    email_address = profile["emailAddress"]

    save_credentials(
        email_address,
        credentials,
    )

    return redirect(
        url_for("email.dashboard")
    )


@email_bp.route("/sync")
def sync():
    full_sync = request.args.get("full") == "1"

    summary = sync_gmail_reports(
        full_sync=full_sync
    )

    return render_template(
        "email/dashboard.html",
        account=EmailAccount.query.first(),
        summary=summary,
    )
