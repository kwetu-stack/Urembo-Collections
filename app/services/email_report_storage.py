from app import db
from app.models.email_report import EmailReport


def save_email_report(
    gmail_message_id,
    subject,
    report_type,
    filename,
    file_data,
    content_type=None,
    rows_imported=0,
    rows_updated=0,
    import_status="Downloaded",
):
    report = EmailReport(
        gmail_message_id=gmail_message_id,
        subject=subject,
        report_type=report_type,
        filename=filename,
        content_type=content_type,
        file_data=file_data,
        file_size=len(file_data),
        rows_imported=rows_imported,
        rows_updated=rows_updated,
        import_status=import_status,
    )

    db.session.add(report)
    db.session.flush()

    return report


def get_latest_reports(limit=10):
    return (
        EmailReport.query.order_by(EmailReport.downloaded_at.desc())
        .limit(limit)
        .all()
    )


def get_report_by_id(report_id):
    return EmailReport.query.get(report_id)
