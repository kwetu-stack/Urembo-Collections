from app import create_app
from app.email_intelligence.sync_service import sync_gmail_reports
app = create_app()
with app.app_context():
    summary = sync_gmail_reports()
    print(summary)
