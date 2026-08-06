from app import create_app
from app.email_intelligence.gmail_service import get_recent_messages
app = create_app()
with app.app_context():
    messages = get_recent_messages(limit=20)
    print('messages_count=', len(messages))
    for msg in messages:
        print('---')
        print('id=', msg['id'])
        print('subject=', msg['subject'])
        print('type=', msg['type'])
        print('has_attachment=', msg['has_attachment'])
        print('attachment_name=', msg['attachment_name'])
        print('debug=', msg['debug'][:200])
