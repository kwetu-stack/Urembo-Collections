from app import create_app
from app.email_intelligence.gmail_service import get_gmail_service
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = create_app()
with app.app_context():
    service = get_gmail_service()
    print('--- raw list latest 20 ---')
    resp = service.users().messages().list(userId='me', maxResults=20).execute()
    for i, msgmeta in enumerate(resp.get('messages', []), start=1):
        msg = service.users().messages().get(userId='me', id=msgmeta['id'], format='metadata', metadataHeaders=['Subject']).execute()
        headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
        print(i, headers.get('Subject','<no subject>'))
    print('--- test query subject:(partner performance) ---')
    resp2 = service.users().messages().list(userId='me', q="subject:(partner performance)", maxResults=20).execute()
    print('count', resp2.get('resultSizeEstimate'), len(resp2.get('messages', [])))
    print('ids', [m['id'] for m in resp2.get('messages', [])])
    print('--- test query subject:commission ---')
    resp3 = service.users().messages().list(userId='me', q="subject:commission", maxResults=20).execute()
    print('count', resp3.get('resultSizeEstimate'), len(resp3.get('messages', [])))
    print('ids', [m['id'] for m in resp3.get('messages', [])])
