from app import create_app
from app.email_intelligence.gmail_service import get_gmail_service
from base64 import urlsafe_b64decode
import re

app = create_app()
with app.app_context():
    service = get_gmail_service()
    # Using results from previous debug: first id under subject=airtel likely one message
    q = 'airtel'
    resp = service.users().messages().list(userId='me', q=q, maxResults=5).execute()
    print('messages', resp.get('resultSizeEstimate'), resp.get('messages'))
    for msgmeta in resp.get('messages', []):
        msg = service.users().messages().get(userId='me', id=msgmeta['id'], format='full').execute()
        headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
        print('---')
        print('id', msg['id'])
        print('subject', headers.get('Subject'))
        print('from', headers.get('From'))
        print('snippet', msg.get('snippet'))
        print('mimeType', msg['payload'].get('mimeType'))
        parts = msg['payload'].get('parts', [])
        print('parts count', len(parts))
        def walk(parts, depth=0):
            for p in parts:
                print('  '*depth + 'part', p.get('mimeType'), p.get('filename') or '<no filename>', p.get('body', {}).get('size'), p.get('body', {}).get('attachmentId'))
                if p.get('parts'):
                    walk(p['parts'], depth+1)
        walk(parts)
        # print plain text if available
        def extract_text(part):
            if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                return urlsafe_b64decode(part['body']['data'].encode()).decode('utf-8', errors='ignore')
            if part.get('mimeType') == 'text/html' and part.get('body', {}).get('data'):
                html = urlsafe_b64decode(part['body']['data'].encode()).decode('utf-8', errors='ignore')
                return re.sub(r'<[^>]+>', '', html)
            for sp in part.get('parts', []):
                t = extract_text(sp)
                if t:
                    return t
            return None
        text = extract_text(msg['payload'])
        print('text snippet', (text or '')[:800])
