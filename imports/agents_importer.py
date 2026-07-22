from pathlib import Path
import sys

import pandas as pd

# ----------------------------------------------------------
# Allow this script to import the Flask application
# ----------------------------------------------------------

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.models.agent import Agent

# ==========================================================
# CONFIGURATION
# ==========================================================

FILE_PATH = Path("data/raw/TUDOR AGENTS.xlsx")

REQUIRED_COLUMNS = [
    "AGENT",
    "AGENT NAME",
    "SITE",
    "TSE",
    "AMA 1+",
    "QAMA",
    "QDRSO",
    "Agent Status",
]


# ==========================================================
# FIND HEADER ROW
# ==========================================================

def detect_header_row(file_path):
    """
    Automatically locate the header row by searching
    for the row whose first cell contains 'AGENT'.
    """

    raw_df = pd.read_excel(file_path, header=None)

    for i in range(min(10, len(raw_df))):
        first_cell = str(raw_df.iloc[i, 0]).strip().upper()

        if first_cell == "AGENT":
            return i

    raise Exception("Could not detect the header row.")


# ==========================================================
# MAIN IMPORT
# ==========================================================

app = create_app()

with app.app_context():

    print("=" * 60)
    print("TUDOR AGENTS IMPORT")
    print("=" * 60)

    # ------------------------------------------------------
    # Check file exists
    # ------------------------------------------------------

    if not FILE_PATH.exists():
        print(f"\nERROR: File not found:\n{FILE_PATH}")
        sys.exit()

    # ------------------------------------------------------
    # Read Excel
    # ------------------------------------------------------

    header_row = detect_header_row(FILE_PATH)

    df = pd.read_excel(FILE_PATH, header=header_row)

    # ------------------------------------------------------
    # Validate required columns
    # ------------------------------------------------------

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        print("\nERROR: Missing required columns:\n")

        for col in missing:
            print(f" - {col}")

        sys.exit()

    # ------------------------------------------------------
    # Load existing agent numbers (fast duplicate checking)
    # ------------------------------------------------------

    existing_agents = {
        row[0]
        for row in db.session.query(Agent.agent_number).all()
    }

    imported = 0
    skipped = 0
    errors = 0

    # ------------------------------------------------------
    # Import records
    # ------------------------------------------------------

    for _, row in df.iterrows():

        try:

            agent_number = str(row["AGENT"]).strip()

            if not agent_number or agent_number.lower() == "nan":
                skipped += 1
                continue

            if agent_number in existing_agents:
                skipped += 1
                continue

            agent = Agent(
                agent_number=agent_number,
                agent_name=str(row["AGENT NAME"]).strip(),
                site=str(row["SITE"]).strip(),
                tse=str(row["TSE"]).strip(),
                ama=str(row["AMA 1+"]).strip(),
                qama=str(row["QAMA"]).strip(),
                qdrso=str(row["QDRSO"]).strip(),
                status=str(row["Agent Status"]).strip(),
            )

            db.session.add(agent)

            # Update our in-memory lookup
            existing_agents.add(agent_number)

            imported += 1

        except Exception as e:

            errors += 1

            print(
                f"Error importing Agent {row.get('AGENT', 'Unknown')} : {e}"
            )

    # ------------------------------------------------------
    # Commit changes
    # ------------------------------------------------------

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print("\nDATABASE COMMIT FAILED")
        print(e)

        sys.exit()

    # ------------------------------------------------------
    # Import Summary
    # ------------------------------------------------------

    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)

    print(f"Rows Read : {len(df)}")
    print(f"Imported : {imported}")
    print(f"Skipped  : {skipped}")
    print(f"Errors   : {errors}")

    print("\nImport completed successfully.")
    print("=" * 60)