from app import create_app
from app.email_intelligence.gmail_service import get_gmail_service
app = create_app()
with app.app_context():
    service = get_gmail_service()
    queries = [
        'airtel',
        'Airtel',
        'AIRTEL',
        'report',
        'performance report',
        'invoice',
        'subject:report',
        'subject:"performance report"',
        'subject:"Partner Performance"',
        'subject:Partner',
        'subject:Performance',
        'from:airtel.com',
        'from:(airtel.com)',
        'has:attachment',
        'newer_than:30d',
        'has:attachment newer_than:30d',
    ]
    for q in queries:
        try:
            resp = service.users().messages().list(userId='me', q=q, maxResults=10).execute()
            print('Q=', q, 'count=', resp.get('resultSizeEstimate'), 'msgs=', len(resp.get('messages', [])))
            if resp.get('messages'):
                for m in resp['messages']:
                    msg = service.users().messages().get(userId='me', id=m['id'], format='metadata', metadataHeaders=['Subject','From']).execute()
                    headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                    print('   ', headers.get('Subject','<no subject>'), 'FROM', headers.get('From',''))
        except Exception as e:
            print('Q error', q, e)
