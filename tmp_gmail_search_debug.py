from app import create_app
from app.email_intelligence.gmail_service import get_gmail_service
app = create_app()
with app.app_context():
    service = get_gmail_service()
    for q in [
        'commission',
        'performance',
        'sim issuance',
        'sim insuance',
        'tudor agents',
        'partner performance',
        'subject:commission',
        'subject:performance',
        'subject:sim',
        'subject:tudor',
        'subject:partner'
    ]:
        try:
            resp = service.users().messages().list(userId='me', q=q, maxResults=5).execute()
            print('Q=', q, 'count=', resp.get('resultSizeEstimate'), 'msgs=', len(resp.get('messages', [])))
            if resp.get('messages'):
                for m in resp['messages']:
                    msg = service.users().messages().get(userId='me', id=m['id'], format='metadata', metadataHeaders=['Subject','From']).execute()
                    headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                    print('  ', headers.get('Subject','<no subject>'), 'FROM', headers.get('From',''))
        except Exception as e:
            print('Q error', q, e)
