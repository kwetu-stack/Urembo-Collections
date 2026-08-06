"""
Coordinates Gmail synchronization.

Workflow

Gmail
    ↓
Read Messages
    ↓
Detect Report Type
    ↓
Download Attachment (if required)
    ↓
Import Into Database
"""

from datetime import datetime

from flask import current_app

from app import db

from app.models.email_account import EmailAccount

from app.email_intelligence.gmail_service import (
    get_recent_messages,
    download_attachment,
)

from app.services.agents_import_service import (
    import_agents,
)

from app.services.sim_import_service import (
    import_sim,
)

from app.services.performance_import_service import (
    import_performance,
)


def sync_gmail_reports():
    """
    Synchronize all supported Airtel reports.
    """

    account = EmailAccount.query.first()

    if account and account.last_sync:
        messages = get_recent_messages(50, after=account.last_sync)
    else:
        messages = get_recent_messages(50)

    downloaded = 0
    imported = 0
    skipped = 0
    errors = 0

    for message in messages:

        try:
            current_app.logger.info(
                "Sync message id=%s subject=%s type=%s has_attachment=%s",
                message["id"],
                message["subject"],
                message["type"],
                message["has_attachment"],
            )

            # --------------------------------------------------
            # Partner Performance
            # (Imported directly from the email body)
            # --------------------------------------------------

            if message["type"] == "Partner Performance":

                result = import_performance(message["body"])

                imported += result["imported"]
                skipped += result["skipped"]
                errors += result["errors"]

                continue

            # --------------------------------------------------
            # Remaining reports require attachments
            # --------------------------------------------------

            if not message["has_attachment"]:

                skipped += 1

                continue

            download = download_attachment(
                message["id"],
                message["attachment_id"],
                message["attachment_name"],
            )

            if not download:

                errors += 1

                continue

            if not download["success"]:

                errors += 1

                continue

            downloaded += 1

            # --------------------------------------------------
            # TUDOR AGENTS
            # --------------------------------------------------

            if message["type"] == "TUDOR AGENTS":

                result = import_agents(download["file_path"])

                imported += result["imported"]
                skipped += result["skipped"]
                errors += result["errors"]

            # --------------------------------------------------
            # SIM ISSUANCE
            # --------------------------------------------------

            elif message["type"] == "SIM Issuance":

                result = import_sim(download["file_path"])

                imported += result["imported"]
                skipped += result["skipped"]
                errors += result["errors"]

            # --------------------------------------------------
            # Unsupported Report
            # --------------------------------------------------

            else:

                skipped += 1
        except Exception as e:

            print(f"SYNC ERROR: {e}")

            errors += 1

    # --------------------------------------------------
    # Update Last Synchronization Time
    # --------------------------------------------------

    account = EmailAccount.query.first()

    if account:

        account.last_sync = datetime.utcnow()

        db.session.commit()

    # --------------------------------------------------
    # Synchronization Summary
    # --------------------------------------------------

    return {
        "success": True,
        "messages_found": len(messages),
        "downloaded": downloaded,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
