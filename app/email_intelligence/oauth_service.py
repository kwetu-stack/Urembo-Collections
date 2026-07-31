from datetime import datetime

from app import db
from app.models.email_account import EmailAccount


def save_credentials(email_address, credentials):
    """
    Creates or updates a Gmail account record.
    """

    account = EmailAccount.query.filter_by(
        email=email_address
    ).first()

    if account is None:
        account = EmailAccount(
            email=email_address
        )
        db.session.add(account)

    account.access_token = credentials.token

    account.refresh_token = credentials.refresh_token

    account.token_uri = credentials.token_uri

    if credentials.scopes:
        account.scopes = ",".join(
            credentials.scopes
        )

    account.token_expiry = credentials.expiry

    account.connected = True

    account.last_sync = datetime.utcnow()

    db.session.commit()

    return account