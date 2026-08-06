from app import create_app, db
from sqlalchemy import inspect, text

app = create_app()
with app.app_context():
    print("tables:", inspect(db.engine).get_table_names())
    print(
        "email_accounts:",
        db.session.execute(
            text("select id, email, connected, last_sync from email_accounts")
        ).all(),
    )
    print(
        "import_history:",
        db.session.execute(
            text(
                "select id, report_type, status, imported, skipped, errors, imported_at from import_history order by imported_at desc limit 20"
            )
        ).all(),
    )
