from datetime import datetime

from app import db


class EmailAccount(db.Model):
    __tablename__ = "email_accounts"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    access_token = db.Column(
        db.Text,
        nullable=False
    )

    refresh_token = db.Column(
        db.Text,
        nullable=True
    )

    token_uri = db.Column(
        db.String(255),
        nullable=True
    )

    scopes = db.Column(
        db.Text,
        nullable=True
    )

    token_expiry = db.Column(
        db.DateTime,
        nullable=True
    )

    connected = db.Column(
        db.Boolean,
        default=True
    )

    last_sync = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )