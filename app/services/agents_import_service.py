from pathlib import Path

import pandas as pd

from app import db
from app.models.agent import Agent


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


def detect_header_row(file_path):
    """
    Automatically locate the Excel header row.
    """

    raw_df = pd.read_excel(file_path, header=None)

    for i in range(min(10, len(raw_df))):

        first_cell = str(raw_df.iloc[i, 0]).strip().upper()

        if first_cell == "AGENT":
            return i

    raise Exception("Could not detect the header row.")


def import_agents(file_path):
    """
    Imports agents from an Excel file.

    Returns a summary dictionary.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    header_row = detect_header_row(file_path)

    df = pd.read_excel(file_path, header=header_row)

    missing = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )

    existing_agents = {
        row[0]
        for row in db.session.query(
            Agent.agent_number
        ).all()
    }

    imported = 0
    skipped = 0
    errors = 0

    for _, row in df.iterrows():

        try:

            agent_number = str(row["AGENT"]).strip()

            if (
                not agent_number
                or agent_number.lower() == "nan"
            ):
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

            existing_agents.add(agent_number)

            imported += 1

        except Exception:
            errors += 1

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return {
        "rows": len(df),
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
