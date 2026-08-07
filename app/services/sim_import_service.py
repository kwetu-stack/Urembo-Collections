from io import BytesIO
from pathlib import Path

import pandas as pd

from app import db
from app.models.sim import SimIssuance
from app.services.import_history_service import log_import

REQUIRED_COLUMNS = [
    "dsoid",
    "item_serial_number",
    "distributorname",
    "orderdate",
    "email",
    "orderheadernum",
    "kyc_msisdn",
    "servedmsisdn",
    "kyc_createdon",
    "activation_time",
    "devicetechnology",
    "rechargeamount",
    "retailer_msisdn",
    "promotermsisdn",
    "zone_name",
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


def _resolve_source(file_path=None, file_data=None, filename="sim_report.xlsx"):
    if file_data is not None:
        return BytesIO(file_data), filename

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    return file_path, file_path.name


def _normalize_columns(df):
    rename_map = {}

    for column in df.columns:
        rename_map[column] = str(column).strip().lower()

    df = df.rename(columns=rename_map)

    alias_map = {
        "activation_time": "Activation_Time".lower(),
        "item serial number": "item_serial_number",
        "distributor name": "distributorname",
        "order date": "orderdate",
        "order header num": "orderheadernum",
    }

    for old_name, new_name in alias_map.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})

    return df


def _detect_header_row(source):
    raw_df = pd.read_excel(source, header=None)

    for i in range(min(15, len(raw_df))):
        row_values = [
            str(value).strip().lower()
            for value in raw_df.iloc[i].tolist()
            if str(value).strip().lower() != "nan"
        ]

        if "item_serial_number" in row_values or "item serial number" in row_values:
            return i

        joined = " ".join(row_values)

        if "item_serial" in joined or "sim serial" in joined:
            return i

    return 0


def _row_payload(row):
    return {
        "dso_id": clean_string(row.get("dsoid")),
        "distributor_name": clean_string(row.get("distributorname")),
        "order_date": clean_string(row.get("orderdate")),
        "email": clean_string(row.get("email")),
        "order_reference": clean_string(row.get("orderheadernum")),
        "kyc_msisdn": clean_string(row.get("kyc_msisdn")),
        "served_msisdn": clean_string(row.get("servedmsisdn")),
        "kyc_created_on": clean_string(row.get("kyc_createdon")),
        "activation_time": clean_string(row.get("activation_time")),
        "device_technology": clean_string(row.get("devicetechnology")),
        "recharge_amount": (
            float(row["rechargeamount"])
            if pd.notna(row.get("rechargeamount"))
            else 0
        ),
        "retailer_msisdn": clean_string(row.get("retailer_msisdn")),
        "promoter_msisdn": clean_string(row.get("promotermsisdn")),
        "zone_name": clean_string(row.get("zone_name")),
    }


def import_sim(file_path=None, file_data=None, filename=None):
    source, resolved_filename = _resolve_source(
        file_path=file_path,
        file_data=file_data,
        filename=filename or "sim_report.xlsx",
    )

    header_row = _detect_header_row(source)

    if isinstance(source, BytesIO):
        source.seek(0)

    df = pd.read_excel(source, header=header_row)
    df = _normalize_columns(df)

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    existing_sims = {
        sim.sim_serial: sim
        for sim in SimIssuance.query.all()
    }

    imported = 0
    updated = 0
    skipped = 0
    errors = 0

    for _, row in df.iterrows():
        serial = clean_string(row.get("item_serial_number"))

        if not serial:
            skipped += 1
            continue

        payload = _row_payload(row)

        try:
            if serial in existing_sims:
                sim = existing_sims[serial]

                for field, value in payload.items():
                    if value is not None:
                        setattr(sim, field, value)

                updated += 1
            else:
                sim = SimIssuance(sim_serial=serial, **payload)
                db.session.add(sim)
                existing_sims[serial] = sim
                imported += 1

        except Exception:
            errors += 1

    try:
        history = log_import(
            report_type="SIM Issuance",
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
            report_type="SIM Issuance",
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
