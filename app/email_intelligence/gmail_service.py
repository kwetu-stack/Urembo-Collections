import os
import re
import base64
from html import unescape
from datetime import datetime

from flask import current_app

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.models.email_account import EmailAccount

# --------------------------------------------------
# Gmail Search Query
# --------------------------------------------------

GMAIL_REPORT_QUERY = (
    "subject:(partner performance) OR "
    "subject:(sim issuance) OR "
    "subject:(sim insuance) OR "
    "subject:(tudor agents) OR "
    "subject:commission"
)

FALLBACK_GMAIL_REPORT_QUERY = (
    "subject:(partner performance) OR "
    "subject:(sim issuance) OR "
    "subject:(sim insuance) OR "
    "subject:(tudor agents) OR "
    "subject:commission OR "
    "partner performance OR "
    "sim issuance OR "
    "sim insuance OR "
    "tudor agents OR "
    "commission"
)


# --------------------------------------------------
# Gmail Authentication
# --------------------------------------------------


def get_gmail_service():
    """
    Return an authenticated Gmail service.
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
        scopes=(account.scopes.split(",") if account.scopes else []),
    )

    return build(
        "gmail",
        "v1",
        credentials=credentials,
    )
    # --------------------------------------------------


# Read Recent Gmail Messages
# --------------------------------------------------


def get_recent_messages(limit=10, after=None):
    """
    Return Airtel-related Gmail messages together with
    report metadata, email body and attachment details.

    Parameters
    ----------
    limit : int
        Maximum number of messages to return.
    after : datetime.datetime | None
        Only return messages newer than this timestamp.
    """

    service = get_gmail_service()

    if service is None:
        return []

    query = GMAIL_REPORT_QUERY

    if after is not None:
        try:
            after_date = after.strftime("%Y/%m/%d")
            query = f"({query}) after:{after_date}"
        except Exception:
            pass

    current_app.logger.info(
        "Gmail fetch query=%s after=%s limit=%s",
        query,
        getattr(after, "isoformat", lambda: None)(),
        limit,
    )

    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            q=query,
            maxResults=limit,
        )
        .execute()
    )

    messages = response.get("messages", [])

    if not messages:
        fallback_query = FALLBACK_GMAIL_REPORT_QUERY

        if after is not None:
            try:
                fallback_query = f"({fallback_query}) after:{after_date}"
            except Exception:
                pass

        current_app.logger.info(
            "Gmail fetch fallback query=%s",
            fallback_query,
        )

        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=fallback_query,
                maxResults=limit,
            )
            .execute()
        )

        messages = response.get("messages", [])

    results = []

    REPORT_TYPES = {
        "Partner Performance": [
            r"\bpartner performance\b",
            r"\bperformance report\b",
            r"\bgross adds\b",
            r"\bback margin\b",
        ],
        "SIM Issuance": [
            r"\bsim[\s_-]*issuance\b",
            r"\bsim[\s_-]*insuance\b",
            r"\butilization\b",
            r"\bsim kits billing\b",
        ],
        "TUDOR AGENTS": [
            r"\btudor[\s_-]*agents?\b",
            r"\bagent\s+performance\b",
        ],
        "Commission": [
            r"\bcommission\b",
            r"\bcommissions\b",
        ],
    }

    def normalize_search_text(text):
        cleaned = re.sub(r"[^\w]+", " ", text or "").lower()
        return " ".join(cleaned.split())

    for message in messages:

        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=message["id"],
                format="full",
            )
            .execute()
        )

        headers = {}

        for header in msg["payload"].get("headers", []):

            headers[header["name"]] = header["value"]

        sender = headers.get("From", "")

        subject = headers.get("Subject", "")

        has_attachment = False

        attachment_name = ""

        attachment_id = ""
        # --------------------------------------------------
        # Find the Most Relevant Attachment
        # --------------------------------------------------

        def find_attachment(parts):
            """
            Recursively search Gmail MIME parts.

            Preference order:

            1. Excel files (.xlsx, .xls)
            2. CSV files
            3. PDF files
            4. Ignore embedded images such as
               image001.png and Outlook logos.
            """

            if not parts:
                return None

            for part in parts:

                filename = part.get("filename", "")

                body = part.get("body", {})

                if filename and body.get("attachmentId"):

                    lower = filename.lower()

                    if lower.endswith(
                        (
                            ".xlsx",
                            ".xls",
                            ".csv",
                            ".pdf",
                        )
                    ):

                        return (
                            filename,
                            body.get("attachmentId"),
                        )

                result = find_attachment(part.get("parts", []))

                if result:
                    return result

            return None

        # --------------------------------------------------
        # Extract Plain Text Email Body
        # --------------------------------------------------

        def strip_html(html):
            if not html:
                return ""

            cleaned = re.sub(
                r"<style.*?>.*?</style>",
                "",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
            cleaned = re.sub(
                r"<script.*?>.*?</script>",
                "",
                cleaned,
                flags=re.IGNORECASE | re.DOTALL,
            )
            cleaned = re.sub(r"<[^>]+>", "", cleaned)
            cleaned = unescape(cleaned)
            return " ".join(cleaned.split())

        def extract_text(parts):

            if not parts:
                return ""

            for part in parts:

                mime_type = part.get("mimeType", "")

                body = part.get("body", {})

                data = body.get("data")

                if mime_type == "text/plain" and data:

                    try:

                        text = base64.urlsafe_b64decode(data.encode("UTF-8")).decode(
                            "utf-8",
                            errors="ignore",
                        )
                        if text.strip():
                            return text

                    except Exception:
                        pass

                if mime_type == "text/html" and data:

                    try:
                        html_text = base64.urlsafe_b64decode(
                            data.encode("UTF-8")
                        ).decode(
                            "utf-8",
                            errors="ignore",
                        )
                        html_text = strip_html(html_text)
                        if html_text.strip():
                            return html_text

                    except Exception:
                        pass

                text = extract_text(part.get("parts", []))

                if text:
                    return text

            return ""
            # --------------------------------------------------

        # Read Message Contents
        # --------------------------------------------------

        parts = msg.get("payload", {}).get("parts", [])

        attachment = find_attachment(parts)

        email_body = extract_text(parts)

        # Some Gmail messages store the body
        # directly in the payload instead of parts.

        if not email_body:

            payload = msg.get("payload", {})

            data = payload.get("body", {}).get("data")

            if data:

                try:

                    raw_body = base64.urlsafe_b64decode(data.encode("UTF-8")).decode(
                        "utf-8",
                        errors="ignore",
                    )
                    email_body = strip_html(raw_body)

                except Exception:

                    email_body = ""

        # --------------------------------------------------
        # Attachment Information
        # --------------------------------------------------

        if attachment:

            has_attachment = True

            attachment_name = attachment[0]

            attachment_id = attachment[1]

        # --------------------------------------------------
        # Detect Report Type
        # --------------------------------------------------

        searchable_text = normalize_search_text(
            f"{sender} {subject} {attachment_name} {email_body}"
        )

        report_type = "Other"

        for report_name, keywords in REPORT_TYPES.items():

            if any(re.search(keyword, searchable_text) for keyword in keywords):

                report_type = report_name

                break

        if report_type == "Other" and attachment_name:
            attachment_name_lower = normalize_search_text(attachment_name)

            if re.search(r"\b(tudor|agent)\b", attachment_name_lower):
                report_type = "TUDOR AGENTS"

            elif re.search(r"\b(sim|utilization|issuance)\b", attachment_name_lower):
                report_type = "SIM Issuance"

            elif re.search(r"\bcommission\b", attachment_name_lower):
                report_type = "Commission"

        # --------------------------------------------------
        # Store Message
        # --------------------------------------------------

        results.append(
            {
                "id": message["id"],
                "date": headers.get(
                    "Date",
                    "",
                ),
                "from": sender,
                "subject": subject,
                "type": report_type,
                "has_attachment": has_attachment,
                "attachment_name": attachment_name,
                "attachment_id": attachment_id,
                "body": email_body,
                "debug": searchable_text,
            }
        )

    return results


# --------------------------------------------------
# Download Attachment
# --------------------------------------------------


def download_attachment(message_id, attachment_id, filename):
    """
    Download a Gmail attachment into

        data/uploads/email_reports/

    and return the saved file information.
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

    file_data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))

    upload_folder = os.path.join(
        current_app.root_path,
        "..",
        "data",
        "uploads",
        "email_reports",
    )

    os.makedirs(
        upload_folder,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_filename = os.path.basename(filename).replace(
        " ",
        "_",
    )

    saved_filename = f"{timestamp}_{safe_filename}"

    file_path = os.path.join(
        upload_folder,
        saved_filename,
    )

    with open(file_path, "wb") as file:

        file.write(file_data)

    return {
        "success": True,
        "file_path": os.path.abspath(file_path),
        "filename": saved_filename,
    }
