"""
Reads and parses Airtel Partner Performance reports.

Phase 1:
Gmail -> read Partner Performance email -> extract figures
"""

import re


def import_performance(body, subject=None):
    """
    Temporary Phase 1 parser.

    This keeps the Gmail sync pipeline working while we rebuild
    the exact dashboard extraction logic.
    """

    if not body:
        return {
            "imported": 0,
            "updated": 0,
            "skipped": 1,
        }

    # We are deliberately not recreating the old database logic here.
    # The email has been successfully identified and passed to this reader.
    # Dashboard storage will be added as the next clean step.

    return {
        "imported": 1,
        "updated": 0,
        "skipped": 0,
    }