from io import BytesIO
from pathlib import Path

import pandas as pd

from app import db
from app.models.agent import Agent
from app.services.import_history_service import log_import

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

COLUMN_ALIASES = {
    "AMA 1+": ["AMA 1+", "AMA1+", "AMA 1", "AMA"],
}


def _resolve_source(file_path=None, file_data=None, filename="import.xlsx"):
    if file_data is not None:
        return BytesIO(file_data), filename

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    return file_path, file_path.name


def detect_header_row(source):
    raw_df = pd.read_excel(source, header=None)

    for i in range(min(15, len(raw_df))):
        first_cell = str(raw_df.iloc[i, 0]).strip().upper()

        if first_cell == "AGENT":
            return i

    raise Exception("Could not detect the header row.")


def _normalize_columns(df):
    rename_map = {}

    for required, aliases in COLUMN_ALIASES.items():
        if required in df.columns:
            continue

        for alias in aliases:
            if alias in df.columns:
                rename_map[alias] = required
                break

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def import_agents(file_path=None, file_data=None, filename=None):
    source, resolved_filename = _resolve_source(
        file_path=file_path,
        file_data=file_data,
        filename=filename or "TUDOR AGENTS.xlsx",
    )

    header_row = detect_header_row(source)

    if isinstance(source, BytesIO):
        source.seek(0)

    df = pd.read_excel(source, header=header_row)
    df = _normalize_columns(df)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    existing_agents = {
        agent.agent_number: agent
        for agent in Agent.query.all()
    }

    imported = 0
    updated = 0
    skipped = 0
    errors = 0

    for _, row in df.iterrows():
        try:
            agent_number = str(row["AGENT"]).strip()

            if not agent_number or agent_number.lower() == "nan":
                skipped += 1
                continue

            payload = {
                "agent_name": str(row["AGENT NAME"]).strip(),
                "site": str(row["SITE"]).strip(),
                "tse": str(row["TSE"]).strip(),
                "ama": str(row["AMA 1+"]).strip(),
                "qama": str(row["QAMA"]).strip(),
                "qdrso": str(row["QDRSO"]).strip(),
                "status": str(row["Agent Status"]).strip(),
            }

            if agent_number in existing_agents:
                agent = existing_agents[agent_number]

                for field, value in payload.items():
                    setattr(agent, field, value)

                updated += 1
            else:
                agent = Agent(agent_number=agent_number, **payload)
                db.session.add(agent)
                existing_agents[agent_number] = agent
                imported += 1

        except Exception:
            errors += 1

    try:
        history = log_import(
            report_type="TUDOR AGENTS",
            filename=resolved_filename,
            imported=imported + updated,
            skipped=skipped,
            errors=errors,
            status="Success",
        )

        db.session.add(history)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return {
        "rows": len(df),
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
