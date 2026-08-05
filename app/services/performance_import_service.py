import re
from datetime import datetime

from app import db
from app.models.performance import PerformanceSnapshot
from app.services.import_history_service import log_import


def clean_number(value):
    """
    Convert numbers like:

    95,000
    1,250
    3,563
    81%

    into numeric values.
    """

    if value is None:
        return None

    value = str(value).replace(",", "").replace("%", "").strip()

    if value == "":
        return None

    try:
        if "." in value:
            return float(value)

        return int(value)

    except Exception:
        return None


def extract(pattern, text, flags=re.IGNORECASE):

    match = re.search(pattern, text, flags)

    if match:
        return match.group(1).strip()

    return None


def import_performance(email_text):
    """
    Import a Partner Performance email into
    PerformanceSnapshot.
    """

    imported = 0
    skipped = 0
    errors = 0

    try:

        # -----------------------------------------
        # Report Date
        # -----------------------------------------

        report_date = datetime.today().date()

        match = re.search(
            r"REPORT AS AT\s+(\d{1,2}\w{2}\s+\w+\s+\d{4})",
            email_text,
            re.IGNORECASE,
        )

        if match:

            try:

                report_date = datetime.strptime(match.group(1), "%dth %B %Y").date()

            except Exception:
                pass

        # -----------------------------------------
        # Partner
        # -----------------------------------------

        partner_name = extract(
            r"JULY\s+\d+\w{2},\s+\d{4}\s+(.+?),\s+Dear Partner",
            email_text,
            re.IGNORECASE | re.DOTALL,
        )

        # -----------------------------------------
        # Contract Status
        # -----------------------------------------

        contract_status = extract(
            r"Signed Contract Status:\s*(.+)",
            email_text,
        )

        # -----------------------------------------
        # KPI Values
        # -----------------------------------------

        gross_adds = clean_number(
            extract(
                r"Partner Gross Adds\s+([\d,]+)",
                email_text,
            )
        )

        sim_billing = clean_number(
            extract(
                r"Sim Kits Billing\s+([\d,]+)",
                email_text,
            )
        )

        active_agents_percent = clean_number(
            extract(
                r"% Active Agents\s+([\d\.]+%)",
                email_text,
            )
        )

        back_margin_rate = clean_number(
            extract(
                r"Back Margin Rate\s+([\d\.]+%)",
                email_text,
            )
        )

        primaries_purchased = clean_number(
            extract(
                r"Primaries Purchased\s+([\d,]+)",
                email_text,
            )
        )

        agent_led_airtime = clean_number(
            extract(
                r"Agent Led Airtime.*?\s+([\d,]+)",
                email_text,
            )
        )

        retailer_self_recharges = clean_number(
            extract(
                r"Retailer Influenced Self Recharges\s+([\d,]+)",
                email_text,
            )
        )

        total_airtime = clean_number(
            extract(
                r"Total Airtime\s+([\d,]+)",
                email_text,
            )
        )

        projected_commission = clean_number(
            extract(
                r"Projected Back Margin Commission\s+([\d,]+)",
                email_text,
            )
        )

        total_agents = clean_number(
            extract(
                r"Total Agents in Cluster\s+([\d,]+)",
                email_text,
            )
        )

        active_agents = clean_number(
            extract(
                r"Agents Served with 1K \+ & 5TXN\s+([\d,]+)",
                email_text,
            )
        )

        # -----------------------------------------
        # Create or Update Performance Snapshot
        # -----------------------------------------

        snapshot = PerformanceSnapshot.query.filter_by(report_date=report_date).first()

        if snapshot is None:

            snapshot = PerformanceSnapshot(report_date=report_date)

            db.session.add(snapshot)

            imported += 1

        else:

            skipped += 1

        snapshot.partner_name = partner_name or "Unknown Partner"

        snapshot.contract_status = contract_status

        snapshot.gross_adds = gross_adds
        snapshot.gross_adds_target = 2000

        snapshot.sim_billing = sim_billing
        snapshot.sim_billing_target = 2000

        snapshot.active_agents_percent = active_agents_percent
        snapshot.active_agents_target = 100

        snapshot.back_margin_rate = back_margin_rate
        snapshot.target_back_margin_rate = 3.75

        snapshot.primaries_purchased = primaries_purchased

        snapshot.agent_led_airtime = agent_led_airtime

        snapshot.retailer_self_recharges = retailer_self_recharges

        snapshot.total_airtime = total_airtime

        snapshot.projected_commission = projected_commission

        snapshot.total_agents = total_agents

        snapshot.active_agents = active_agents

        db.session.commit()

        log_import(
            report_type="Partner Performance",
            filename="Email Body",
            imported=imported,
            skipped=skipped,
            errors=errors,
            status="Success",
        )

    except Exception as e:

        db.session.rollback()

        errors += 1

        log_import(
            report_type="Partner Performance",
            filename="Email Body",
            imported=0,
            skipped=0,
            errors=errors,
            status=f"Failed: {e}",
        )

        raise

    return {
        "rows": 1,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
