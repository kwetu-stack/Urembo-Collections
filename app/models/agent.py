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
    "AMA 1+",
    "QAMA",
    "QDRSO",
    "Agent Status",
]


def clean_string(value):
    if pd.isna(value):
        return None

    text = str(value).strip()

    if text.lower() == "nan":
        return None

    if text.endswith(".0"):
        text = text[:-2]

    return text


def _resolve_source(file_path=None, file_data=None, filename="TUDOR AGENTS.xlsx"):
    if file_data is not None:
        return BytesIO(file_data), filename

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    return file_path, file_path.name


def _detect_header_row(source):
    raw_df = pd.read_excel(source, header=None)

    for i in range(min(15, len(raw_df))):
        row_values = [
            str(value).strip().upper()
            for value in raw_df.iloc[i].tolist()
            if str(value).strip().lower() != "nan"
        ]

        if "AGENT" in row_values and "AGENT NAME" in row_values:
            return i

    return 0


def _normalize_columns(df):
    rename_map = {}

    for column in df.columns:
        clean = str(column).strip()

        upper = clean.upper()

        if upper == "AGENT STATUS":
            rename_map[column] = "Agent Status"

        elif upper == "AMA":
            rename_map[column] = "AMA 1+"

        elif upper == "AMA1+":
            rename_map[column] = "AMA 1+"

        elif upper == "AMA 1":
            rename_map[column] = "AMA 1+"

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def _row_payload(row):
    return {
        "agent_name": clean_string(row.get("AGENT NAME")),
        "site": clean_string(row.get("SITE")),
        "tse": clean_string(row.get("TSE")),
        "ama": clean_string(row.get("AMA 1+")),
        "qama": clean_string(row.get("QAMA")),
        "qdrso": clean_string(row.get("QDRSO")),
        "status": clean_string(row.get("Agent Status")),
    }


def import_agents(file_path=None, file_data=None, filename=None):

    source, resolved_filename = _resolve_source(
        file_path=file_path,
        file_data=file_data,
        filename=filename or "TUDOR AGENTS.xlsx",
    )

    header_row = _detect_header_row(source)

    if isinstance(source, BytesIO):
        source.seek(0)

    df = pd.read_excel(source, header=header_row)

    df = _normalize_columns(df)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )

    existing_agents = {
        agent.agent_number: agent
        for agent in Agent.query.all()
    }

    imported = 0
    updated = 0
    skipped = 0
    errors = 0

    for _, row in df.iterrows():

        agent_number = clean_string(row.get("AGENT"))

        if not agent_number:
            skipped += 1
            continue

        payload = _row_payload(row)

        try:

            if agent_number in existing_agents:

                agent = existing_agents[agent_number]

                for field, value in payload.items():
                    if value is not None:
                        setattr(agent, field, value)

                updated += 1

            else:

                agent = Agent(
                    agent_number=agent_number,
                    **payload,
                )

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

        history = log_import(
            report_type="TUDOR AGENTS",
            filename=resolved_filename,
            imported=imported + updated,
            skipped=skipped,
            errors=errors,
            status="Failed",
        )

        db.session.add(history)

        db.session.commit()

        raise

    return {
        "rows": len(df),
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }