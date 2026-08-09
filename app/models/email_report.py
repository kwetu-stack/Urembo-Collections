from datetime import datetime

from app import db


class EmailReport(db.Model):
    __tablename__ = "email_reports"

    id = db.Column(db.Integer, primary_key=True)

    gmail_message_id = db.Column(
        db.String(255),
        nullable=False,
        index=True
    )

    subject = db.Column(
        db.String(500),
        nullable=True
    )

    report_type = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    filename = db.Column(
        db.String(500),
        nullable=False
    )

    content_type = db.Column(
        db.String(255),
        nullable=True
    )

    file_data = db.Column(
        db.LargeBinary,
        nullable=True
    )

    file_size = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    rows_imported = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    rows_updated = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    import_status = db.Column(
        db.String(50),
        default="Imported",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<EmailReport {self.filename}>"


class ProcessedEmailMessage(db.Model):
    __tablename__ = "processed_email_messages"

    id = db.Column(db.Integer, primary_key=True)

    gmail_message_id = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    subject = db.Column(
        db.String(500),
        nullable=True
    )

    processed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<ProcessedEmailMessage {self.gmail_message_id}>"