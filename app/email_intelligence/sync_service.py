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
    Synchronize all Airtel reports from Gmail.
    """

    messages = get_recent_messages(50)

    downloaded = 0
    imported = 0
    skipped = 0
    errors = 0

    for message in messages:

        try:

            # ------------------------------------------
            # PARTNER PERFORMANCE
            # (No attachment)
            # ------------------------------------------

            if message["type"] == "Partner Performance":

                result = import_performance(
                    message["body"]
                )

                imported += result["imported"]
                skipped += result["skipped"]
                errors += result["errors"]

                continue

            # ------------------------------------------
            # Everything below requires attachments
            # ------------------------------------------

            if not message["has_attachment"]:
                skipped += 1
                continue

            download = download_attachment(
                message["id"],
                message["attachment_id"],
                message["attachment_name"],
            )

            if not download["success"]:
                errors += 1
                continue

            downloaded += 1

            # ------------------------------------------
            # TUDOR AGENTS
            # ------------------------------------------

            if message["type"] == "TUDOR AGENTS":

                result = import_agents(
                    download["file_path"]
                )

                imported += result["imported"]
                skipped += result["skipped"]

            # ------------------------------------------
            # SIM ISSUANCE
            # ------------------------------------------

            elif message["type"] == "SIM Issuance":

                result = import_sim(
                    download["file_path"]
                )

                imported += result["imported"]
                skipped += result["skipped"]

            else:

                skipped += 1

        except Exception as e:

            print(f"SYNC ERROR: {e}")

            errors += 1

    account = EmailAccount.query.first()

    if account:

        account.last_sync = datetime.utcnow()

        db.session.commit()

    return {
        "success": True,
        "messages_found": len(messages),
        "downloaded": downloaded,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
