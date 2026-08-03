from datetime import datetime

from app import db
from app.models.email_account import EmailAccount


def save_credentials(email_address, credentials):
    """
    Save the Gmail credentials.

    UREMBO COLLECTIONS supports a single connected
    Gmail account. Reconnecting Gmail updates the
    existing account instead of creating a new row.
    """

    account = EmailAccount.query.first()

    if account is None:
        account = EmailAccount()
        db.session.add(account)

    account.email = email_address
    account.access_token = credentials.token
    account.refresh_token = credentials.refresh_token
    account.token_uri = credentials.token_uri

    if credentials.scopes:
        account.scopes = ",".join(credentials.scopes)

    account.token_expiry = credentials.expiry
    account.connected = True
    account.last_sync = datetime.utcnow()

    db.session.commit()

    return account