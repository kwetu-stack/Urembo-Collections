from app import create_app
from app.email_intelligence.gmail_service import get_gmail_service
app = create_app()
with app.app_context():
    service = get_gmail_service()
    print('service', service)
    try:
        resp = service.users().messages().list(userId='me', maxResults=5).execute()
        print('response_keys', resp.keys())
        print(resp)
    except Exception as e:
        import traceback
        traceback.print_exc()
