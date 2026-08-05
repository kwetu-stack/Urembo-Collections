from app import db


class ImportHistory(db.Model):

    __tablename__ = "import_history"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    report_type = db.Column(
        db.String(100),
        nullable=False
    )

    source = db.Column(
        db.String(100),
        nullable=False,
        default="Gmail"
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    imported = db.Column(
        db.Integer,
        default=0
    )

    skipped = db.Column(
        db.Integer,
        default=0
    )

    errors = db.Column(
        db.Integer,
        default=0
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Success"
    )

    imported_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def __repr__(self):
        return (
            f"<ImportHistory "
            f"{self.report_type} "
            f"{self.imported_at}>"
        )