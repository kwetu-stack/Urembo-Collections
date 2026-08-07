from datetime import datetime

from app import db


class EmailReport(db.Model):
    """Airtel report file stored in PostgreSQL."""

    __tablename__ = "email_reports"

    id = db.Column(db.Integer, primary_key=True)

    gmail_message_id = db.Column(db.String(255), nullable=False, index=True)

    subject = db.Column(db.String(500), nullable=True)

    report_type = db.Column(db.String(100), nullable=False)

    filename = db.Column(db.String(255), nullable=False)

    content_type = db.Column(db.String(100), nullable=True)

    file_data = db.Column(db.LargeBinary, nullable=False)

    file_size = db.Column(db.Integer, nullable=False, default=0)

    rows_imported = db.Column(db.Integer, default=0)

    rows_updated = db.Column(db.Integer, default=0)

    import_status = db.Column(db.String(50), default="Downloaded")

    downloaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<EmailReport {self.report_type} {self.filename}>"


class ProcessedEmailMessage(db.Model):
    """Tracks Gmail messages that have already been synchronized."""

    __tablename__ = "processed_email_messages"

    id = db.Column(db.Integer, primary_key=True)

    gmail_message_id = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    report_type = db.Column(db.String(100), nullable=False)

    subject = db.Column(db.String(500), nullable=True)

    imported = db.Column(db.Integer, default=0)

    updated = db.Column(db.Integer, default=0)

    skipped = db.Column(db.Integer, default=0)

    status = db.Column(db.String(50), default="Success")

    processed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<ProcessedEmailMessage {self.gmail_message_id}>"
