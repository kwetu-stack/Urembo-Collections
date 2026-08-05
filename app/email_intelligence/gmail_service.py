import os
import base64
from flask import current_app
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime

from app.models.email_account import EmailAccount


# Search only for Airtel business reports
GMAIL_REPORT_QUERY = (
    '"partner performance" '
    'OR "sim issuance" '
    'OR "tudor agents" '
    'OR commission'
)


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
    Returns Airtel-related Gmail messages with
    sender, subject, date, report type and
    attachment information.
    """

    service = get_gmail_service()

    if service is None:
        return []

    response = service.users().messages().list(
        userId="me",
        q=GMAIL_REPORT_QUERY,
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

        has_attachment = False
        attachment_name = ""
        attachment_id = ""

        def find_attachment(parts):
            """
            Recursively search Gmail MIME parts
            for the first attachment.
            """

            if not parts:
                return None

            for part in parts:

                filename = part.get("filename", "")

                body = part.get("body", {})

                if filename and body.get("attachmentId"):
                    return (
                        filename,
                        body.get("attachmentId"),
                    )

                result = find_attachment(
                    part.get("parts", [])
                )

                if result:
                    return result

            return None


        parts = msg.get("payload", {}).get("parts", [])

        attachment = find_attachment(parts)

        if attachment:

            has_attachment = True

            attachment_name = attachment[0]

            attachment_id = attachment[1]

        # Build searchable text after attachment detection.
        text = (
            f"{sender} "
            f"{subject} "
            f"{attachment_name}"
        ).lower()

        report_type = "Other"

        for report_name, keywords in REPORT_TYPES.items():

            if any(keyword in text for keyword in keywords):
                report_type = report_name
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
                
                "debug": text,
            }
        )

    return results


def download_attachment(message_id, attachment_id, filename):
    """
    Downloads a Gmail attachment and saves it to:

        data/uploads/email_reports/

    Returns the full path of the saved file.
    """

    service = get_gmail_service()

    if service is None:
        return None

    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(
            userId="me",
            messageId=message_id,
            id=attachment_id,
        )
        .execute()
    )

    file_data = base64.urlsafe_b64decode(
        attachment["data"].encode("UTF-8")
    )

    upload_folder = os.path.join(
        current_app.root_path,
        "..",
        "data",
        "uploads",
        "email_reports",
    )

    os.makedirs(upload_folder, exist_ok=True)

    # Create a unique filename for each downloaded attachment.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = os.path.basename(filename).replace(" ", "_")
    saved_filename = f"{timestamp}_{safe_filename}"

    file_path = os.path.join(
        upload_folder,
        saved_filename,
    )

    with open(file_path, "wb") as f:
        f.write(file_data)

    return {
        "success": True,
        "file_path": os.path.abspath(file_path),
        "filename": saved_filename,
    }
