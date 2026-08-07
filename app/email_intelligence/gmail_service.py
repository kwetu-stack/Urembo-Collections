import base64
import re
from html import unescape

from flask import current_app

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app import db
from app.models.email_account import EmailAccount
from app.email_intelligence.report_classifier import (
    classify_report,
    is_airtel_attachment,
    is_airtel_sender,
    is_supported_report,
)

GMAIL_REPORT_QUERY = (
    "from:airtel.com ("
    'subject:"partner performance" OR '
    'subject:"sim issuance" OR '
    'subject:"sim insuance" OR '
    'subject:"tudor agents" OR '
    'subject:"utilization"'
    ")"
)


def _persist_refreshed_credentials(account, credentials):
    if credentials.token and credentials.token != account.access_token:
        account.access_token = credentials.token

    if credentials.expiry:
        account.token_expiry = credentials.expiry

    db.session.commit()


def get_gmail_service():
    account = EmailAccount.query.first()

    if account is None:
        return None

    credentials = Credentials(
        token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri=account.token_uri or "https://oauth2.googleapis.com/token",
        client_id=current_app.config["GMAIL_CLIENT_ID"],
        client_secret=current_app.config["GMAIL_CLIENT_SECRET"],
        scopes=(account.scopes.split(",") if account.scopes else []),
    )

    if credentials.expired and credentials.refresh_token:
        from google.auth.transport.requests import Request

        credentials.refresh(Request())
        _persist_refreshed_credentials(account, credentials)

    return build("gmail", "v1", credentials=credentials)


def _list_messages(service, query, limit):
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=limit)
        .execute()
    )

    return response.get("messages", [])


def get_recent_messages(limit=10, after=None, airtel_only=True):
    service = get_gmail_service()

    if service is None:
        return []

    query = GMAIL_REPORT_QUERY

    if after is not None:
        try:
            after_date = after.strftime("%Y/%m/%d")
            query = f"{query} after:{after_date}"
        except Exception:
            pass

    current_app.logger.info(
        "Gmail fetch query=%s after=%s limit=%s",
        query,
        getattr(after, "isoformat", lambda: None)(),
        limit,
    )

    messages = _list_messages(service, query, limit)

    results = []

    for message in messages:
        parsed = _parse_message(service, message["id"])

        if parsed is None:
            continue

        if airtel_only and not is_supported_report(parsed["type"]):
            continue

        if airtel_only and not is_airtel_sender(parsed["from"]):
            continue

        results.append(parsed)

    return results


def _parse_message(service, message_id):
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    headers = {
        header["name"]: header["value"]
        for header in msg["payload"].get("headers", [])
    }

    sender = headers.get("From", "")
    subject = headers.get("Subject", "")
    parts = msg.get("payload", {}).get("parts", [])

    attachment = _find_attachment(parts)
    email_body = _extract_text(parts)

    if not email_body:
        payload = msg.get("payload", {})
        data = payload.get("body", {}).get("data")

        if data:
            try:
                raw_body = base64.urlsafe_b64decode(data.encode("UTF-8")).decode(
                    "utf-8",
                    errors="ignore",
                )
                email_body = _strip_html(raw_body)
            except Exception:
                email_body = ""

    has_attachment = attachment is not None
    attachment_name = attachment[0] if attachment else ""
    attachment_id = attachment[1] if attachment else ""

    report_type = classify_report(
        sender,
        subject,
        attachment_name,
        email_body,
    )

    return {
        "id": message_id,
        "date": headers.get("Date", ""),
        "from": sender,
        "subject": subject,
        "type": report_type,
        "has_attachment": has_attachment,
        "attachment_name": attachment_name,
        "attachment_id": attachment_id,
        "body": email_body,
    }


def _find_attachment(parts):
    if not parts:
        return None

    for part in parts:
        filename = part.get("filename", "")
        body = part.get("body", {})

        if filename and body.get("attachmentId"):
            lower = filename.lower()

            if lower.endswith((".xlsx", ".xls", ".csv")) and is_airtel_attachment(
                filename
            ):
                return (filename, body.get("attachmentId"))

        result = _find_attachment(part.get("parts", []))

        if result:
            return result

    return None


def _strip_html(html):
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
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    return " ".join(cleaned.split())


def _extract_text(parts):
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
                html_text = base64.urlsafe_b64decode(data.encode("UTF-8")).decode(
                    "utf-8",
                    errors="ignore",
                )
                html_text = _strip_html(html_text)
                if html_text.strip():
                    return html_text
            except Exception:
                pass

        text = _extract_text(part.get("parts", []))

        if text:
            return text

    return ""


def download_attachment(message_id, attachment_id, filename):
    service = get_gmail_service()

    if service is None:
        return None

    if not is_airtel_attachment(filename):
        return {
            "success": False,
            "error": "Attachment is not a supported Airtel report.",
        }

    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=message_id, id=attachment_id)
        .execute()
    )

    file_data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))

    return {
        "success": True,
        "file_data": file_data,
        "filename": filename,
        "content_type": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if filename.lower().endswith(".xlsx")
            else "application/vnd.ms-excel"
        ),
    }
