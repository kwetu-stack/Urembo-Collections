"""
Coordinates Gmail synchronization.

Gmail -> detect Airtel report -> download -> store in PostgreSQL -> import
"""

from datetime import datetime

from flask import current_app

from app import db
from app.models.email_account import EmailAccount
from app.models.email_report import ProcessedEmailMessage
from app.email_intelligence.gmail_service import (
    get_recent_messages,
    download_attachment,
)
from app.email_intelligence.report_classifier import is_supported_report
from app.services.agents_import_service import import_agents
from app.services.sim_import_service import import_sim
from app.services.performance_import_service import import_performance
from app.services.email_report_storage import save_email_report


def _already_processed(message_id):
    return (
        ProcessedEmailMessage.query.filter_by(gmail_message_id=message_id).first()
        is not None
    )


def _mark_processed(message, imported=0, updated=0, skipped=0, status="Success"):
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
            "downloaded": 0,
            "imported": 0,
            "updated": 0,
            "skipped_messages": 0,
            "skipped_rows": 0,
            "errors": 0,
        }

    has_processed = ProcessedEmailMessage.query.count() > 0
    limit = 100 if full_sync or not has_processed else 50

    if account.last_sync and has_processed and not full_sync:
        messages = get_recent_messages(limit, after=account.last_sync)
    else:
        messages = get_recent_messages(limit)

    downloaded = 0
    imported = 0
    updated = 0
    skipped_messages = 0
    skipped_rows = 0
    errors = 0

    for message in messages:
        if not full_sync and _already_processed(message["id"]):
            skipped_messages += 1
            continue

        if not is_supported_report(message["type"]):
            skipped_messages += 1
            continue

        try:
            current_app.logger.info(
                "Sync message id=%s subject=%s type=%s has_attachment=%s",
                message["id"],
                message["subject"],
                message["type"],
                message["has_attachment"],
            )

            if message["type"] == "Partner Performance":
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
                )
                continue

            if not message["has_attachment"]:
                skipped_messages += 1
                _mark_processed(message, status="No attachment")
                continue

            download = download_attachment(
                message["id"],
                message["attachment_id"],
                message["attachment_name"],
            )

            if not download or not download.get("success"):
                errors += 1
                _mark_processed(message, status="Download failed")
                continue

            downloaded += 1

            file_data = download["file_data"]
            filename = download["filename"]

            if message["type"] == "TUDOR AGENTS":
                result = import_agents(file_data=file_data, filename=filename)
            elif message["type"] == "SIM Issuance":
                result = import_sim(file_data=file_data, filename=filename)
            else:
                skipped_messages += 1
                _mark_processed(message, status="Unsupported attachment")
                continue

            imported += result["imported"]
            updated += result.get("updated", 0)
            skipped_rows += result["skipped"]

            save_email_report(
                gmail_message_id=message["id"],
                subject=message["subject"],
                report_type=message["type"],
                filename=filename,
                file_data=file_data,
                content_type=download.get("content_type"),
                rows_imported=result["imported"],
                rows_updated=result.get("updated", 0),
                import_status="Imported",
            )

            _mark_processed(
                message,
                imported=result["imported"],
                updated=result.get("updated", 0),
                skipped=result["skipped"],
            )

            db.session.commit()

        except Exception as exc:
            current_app.logger.exception("Sync error for message %s", message["id"])
            print(f"SYNC ERROR: {exc}")
            errors += 1
            db.session.rollback()

            try:
                _mark_processed(message, status=f"Failed: {exc}")
            except Exception:
                db.session.rollback()

    if account:
        account.last_sync = datetime.utcnow()
        db.session.commit()

    return {
        "success": True,
        "messages_found": len(messages),
        "downloaded": downloaded,
        "imported": imported,
        "updated": updated,
        "skipped_messages": skipped_messages,
        "skipped_rows": skipped_rows,
        "skipped": skipped_messages + skipped_rows,
        "errors": errors,
    }

