import os
import sys

import pandas as pd

# ------------------------------------------------------
# Allow imports from project root
# ------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models.sim import SimIssuance

FILE = "data/raw/1140749_SIM Insuance and Utilization Report as of_07-05-2026.xlsx"

REQUIRED_COLUMNS = [
    "dsoid",
    "item_serial_number",
    "distributorname",
    "orderdate",
    "EMAIL",
    "orderheadernum",
    "kyc_msisdn",
    "servedmsisdn",
    "kyc_createdon",
    "Activation_Time",
    "devicetechnology",
    "rechargeamount",
    "retailer_msisdn",
    "promotermsisdn",
    "zone_name",
]


def clean_string(value):
    """Convert Excel values safely to strings."""

    if pd.isna(value):
        return None

    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    return text


app = create_app()

with app.app_context():

    print("\n========== SIM ISSUANCE IMPORT ==========\n")

    df = pd.read_excel(FILE)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        print("Missing columns:")
        print(missing)
        raise SystemExit()

    existing_serials = {
        row[0]
        for row in db.session.query(SimIssuance.sim_serial).all()
    }

    imported = 0
    skipped = 0
    errors = 0

    for _, row in df.iterrows():

        serial = clean_string(row["item_serial_number"])

        if not serial:
            skipped += 1
            continue

        if serial in existing_serials:
            skipped += 1
            continue

        try:

            sim = SimIssuance(

                dso_id=clean_string(row["dsoid"]),

                sim_serial=serial,

                distributor_name=clean_string(row["distributorname"]),

                order_date=clean_string(row["orderdate"]),

                email=clean_string(row["EMAIL"]),

                order_reference=clean_string(row["orderheadernum"]),

                kyc_msisdn=clean_string(row["kyc_msisdn"]),

                served_msisdn=clean_string(row["servedmsisdn"]),

                kyc_created_on=clean_string(row["kyc_createdon"]),

                activation_time=clean_string(row["Activation_Time"]),

                device_technology=clean_string(row["devicetechnology"]),

                recharge_amount=(
                    float(row["rechargeamount"])
                    if pd.notna(row["rechargeamount"])
                    else 0
                ),

                retailer_msisdn=clean_string(row["retailer_msisdn"]),

                promoter_msisdn=clean_string(row["promotermsisdn"]),

                zone_name=clean_string(row["zone_name"]),
            )

            db.session.add(sim)

            existing_serials.add(serial)

            imported += 1

        except Exception:

            errors += 1

    db.session.commit()

    print(f"Rows Read : {len(df)}")
    print(f"Imported : {imported}")
    print(f"Skipped : {skipped}")
    print(f"Errors : {errors}")