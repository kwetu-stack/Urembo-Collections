from pathlib import Path
import sys

# ----------------------------------------------------------
# Allow this script to import the Flask application
# ----------------------------------------------------------

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.services.agents_import_service import import_agents


# ==========================================================
# CONFIGURATION
# ==========================================================

FILE_PATH = Path("data/raw/TUDOR AGENTS.xlsx")


# ==========================================================
# MAIN IMPORT
# ==========================================================

app = create_app()

with app.app_context():

    print("=" * 60)
    print("TUDOR AGENTS IMPORT")
    print("=" * 60)

    try:

        summary = import_agents(FILE_PATH)

        print("\n" + "=" * 60)
        print("IMPORT SUMMARY")
        print("=" * 60)

        print(f"Rows Read : {summary['rows']}")
        print(f"Imported : {summary['imported']}")
        print(f"Skipped  : {summary['skipped']}")
        print(f"Errors   : {summary['errors']}")

        print("\nImport completed successfully.")
        print("=" * 60)

    except Exception as e:

        print("\nIMPORT FAILED")
        print(e)