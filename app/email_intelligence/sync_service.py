"""
Coordinates Gmail synchronization.

Workflow:

Gmail
    ↓
Download Attachment
    ↓
Detect Report Type
    ↓
Import into Database
"""

from app.email_intelligence.gmail_service import (
    get_recent_messages,
    download_attachment,
)

from datetime import datetime

from app import db
from app.models.email_account import EmailAccount
from app.services.agents_import_service import import_agents
from app.services.sim_import_service import import_sim


def sync_gmail_reports():
    """
    Synchronize Gmail reports.

    Phase 1
    --------
    • Find Gmail reports
    • Download attachments
    • Automatically import supported reports
    """

    messages = get_recent_messages(50)

    downloaded = 0
    imported = 0
    skipped = 0
    errors = 0

    for message in messages:

        # --------------------------------------------------
        # Skip emails without attachments
        # --------------------------------------------------

        if not message["has_attachment"]:
            skipped += 1
            continue

        try:

            download_result = download_attachment(
                message["id"],
                message["attachment_id"],
                message["attachment_name"],
            )

            if not download_result["success"]:
                errors += 1
                continue

            downloaded += 1

            # --------------------------------------------------
            # TUDOR AGENTS
            # --------------------------------------------------

            if message["type"] == "TUDOR AGENTS":

                import_result = import_agents(
                    download_result["file_path"]
                )

                imported += import_result["imported"]
                skipped += import_result["skipped"]

            # --------------------------------------------------
            # SIM ISSUANCE
            # --------------------------------------------------

            elif message["type"] == "SIM Issuance":

                import_result = import_sim(
                    download_result["file_path"]
                )

                imported += import_result["imported"]
                skipped += import_result["skipped"]

            # --------------------------------------------------
            # Partner Performance
            # (Coming next)
            # --------------------------------------------------

            # elif message["type"] == "Partner Performance":
            #
            #     import_result = import_performance(
            #         download_result["file_path"]
            #     )
            #
            #     imported += import_result["imported"]
            #     skipped += import_result["skipped"]

            else:
                skipped += 1

        except Exception as e:

            print(f"Sync Error: {e}")

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
