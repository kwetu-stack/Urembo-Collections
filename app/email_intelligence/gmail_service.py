from flask import current_app
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.models.email_account import EmailAccount


def get_gmail_service():
    """
    Returns an authenticated Gmail service
    using the saved credentials.
    """

    account = EmailAccount.query.first()

    if account is None:
        return None

    credentials = Credentials(
        token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri=account.token_uri,
        client_id=current_app.config["GMAIL_CLIENT_ID"],
        client_secret=current_app.config["GMAIL_CLIENT_SECRET"],
        scopes=account.scopes.split(",")
        if account.scopes else [],
    )

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return service


def get_recent_messages(limit=10):
    """
    Returns the latest Gmail messages with
    sender, subject, date, report type
    and attachment information.
    """

    service = get_gmail_service()

    if service is None:
        return []

    response = service.users().messages().list(
        userId="me",
        maxResults=limit
    ).execute()

    messages = response.get("messages", [])

    results = []

    REPORT_TYPES = {
        "Partner Performance": [
            "partner performance",
            "gross adds",
            "back margin",
        ],

        "SIM Issuance": [
            "sim issuance",
            "utilization",
            "sim kits billing",
        ],

        "TUDOR AGENTS": [
            "tudor agents",
        ],

        "Commission": [
            "commission",
        ],
    }

    for message in messages:

        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="full",
        ).execute()

        headers = {}

        for header in msg["payload"].get("headers", []):
            headers[header["name"]] = header["value"]

        sender = headers.get("From", "")
        subject = headers.get("Subject", "")

        text = f"{sender} {subject}".lower()

        report_type = "Other"

        for report_name, keywords in REPORT_TYPES.items():

            if any(keyword in text for keyword in keywords):
                report_type = report_name
                break

        has_attachment = False
        attachment_name = ""
        attachment_id = ""

        parts = msg.get("payload", {}).get("parts", [])

        for part in parts:

            filename = part.get("filename", "")
            body = part.get("body", {})

            if filename:

                has_attachment = True
                attachment_name = filename
                attachment_id = body.get("attachmentId", "")

                break

        results.append(
            {
                "id": message["id"],
                "date": headers.get("Date", ""),
                "from": sender,
                "subject": subject,
                "type": report_type,
                "has_attachment": has_attachment,
                "attachment_name": attachment_name,
                "attachment_id": attachment_id,
            }
        )

    return results