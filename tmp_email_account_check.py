from app import create_app
from app.models.email_account import EmailAccount
app = create_app()
with app.app_context():
    print('SQLALCHEMY_DATABASE_URI=', app.config['SQLALCHEMY_DATABASE_URI'])
    acc = EmailAccount.query.first()
    print('account_exists', acc is not None)
    if acc:
        print('id=', acc.id)
        print('email=', acc.email)
        print('connected=', acc.connected)
        print('last_sync=', acc.last_sync)
        print('token_uri=', acc.token_uri)
        print('scopes=', acc.scopes)
        print('access_token_present=', bool(acc.access_token))
        print('refresh_token_present=', bool(acc.refresh_token))
