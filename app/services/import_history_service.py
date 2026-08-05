from app.models.import_history import ImportHistory


def log_import(
    report_type,
    filename,
    imported=0,
    skipped=0,
    errors=0,
    status="Success",
    source="Gmail",
):
    """
    Create an ImportHistory record.

    The caller is responsible for committing
    the database transaction.
    """

    return ImportHistory(
        report_type=report_type,
        source=source,
        filename=filename,
        imported=imported,
        skipped=skipped,
        errors=errors,
        status=status,
    )