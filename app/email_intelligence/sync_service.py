"""
Coordinates Gmail synchronization for Partner Performance reports.

Gmail -> detect Partner Performance report -> parse -> store -> dashboard
"""

from datetime import datetime

from flask import current_app

from app import db
from app.models.email_account import EmailAccount
from app.models.email_report import ProcessedEmailMessage
from app.email_intelligence.gmail_service import get_recent_messages
from app.email_intelligence.performance_reader import import_performance


def _already_processed(message_id):
    return (
        ProcessedEmailMessage.query.filter_by(
            gmail_message_id=message_id
        ).first()
        is not None
    )


def _mark_processed(
    message,
    imported=0,
    updated=0,
    skipped=0,
    status="Success",
):
    record = ProcessedEmailMessage.query.filter_by(
        gmail_message_id=message["id"]
    ).first()

    if record is None:
        record = ProcessedEmailMessage(
            gmail_message_id=message["id"],
            report_type=message["type"],
            subject=message.get("subject"),
        )
        db.session.add(record)

    record.imported = imported
    record.updated = updated
    record.skipped = skipped
    record.status = status
    record.processed_at = datetime.utcnow()

    db.session.commit()

    return record


def sync_gmail_reports(full_sync=False):
    account = EmailAccount.query.first()

    if account is None:
        return {
            "success": False,
            "error": "No Gmail account connected.",
            "messages_found": 0,
            "imported": 0,
            "updated": 0,
            "skipped_messages": 0,
            "skipped_rows": 0,
            "errors": 0,
        }

    messages = get_recent_messages(limit=500)

    imported = 0
    updated = 0
    skipped_messages = 0
    skipped_rows = 0
    errors = 0
    performance_messages = 0

    for message in messages:

        # Phase 1 only handles Partner Performance reports.
        if message["type"] != "Partner Performance":
            continue

        performance_messages += 1

        if _already_processed(message["id"]):
            skipped_messages += 1
            continue

        try:
            current_app.logger.info(
                "Processing performance message id=%s subject=%s",
                message["id"],
                message["subject"],
            )

            result = import_performance(
                message["body"],
                subject=message["subject"],
            )

            imported += result["imported"]
            updated += result.get("updated", 0)
            skipped_rows += result["skipped"]

            _mark_processed(
                message,
                imported=result["imported"],
                updated=result.get("updated", 0),
                skipped=result["skipped"],
                status="Success",
            )

        except Exception as exc:
            current_app.logger.exception(
                "Performance sync error for message %s",
                message["id"],
            )

            errors += 1
            db.session.rollback()

            try:
                _mark_processed(
                    message,
                    status=f"Failed: {exc}",
                )
            except Exception:
                db.session.rollback()

    account.last_sync = datetime.utcnow()
    db.session.commit()

    return {
        "success": True,
        "messages_found": len(messages),
        "performance_messages": performance_messages,
        "imported": imported,
        "updated": updated,
        "skipped_messages": skipped_messages,
        "skipped_rows": skipped_rows,
        "skipped": skipped_messages + skipped_rows,
        "errors": errors,
    }