import re
from datetime import datetime

from app import db
from app.models.performance import PerformanceSnapshot
from app.services.import_history_service import log_import


def clean_number(value):
    """
    Convert Airtel numeric values into integers/floats.

    Examples

        95,000  -> 95000
        1,250   -> 1250
        81%     -> 81
        3.75%   -> 3.75
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


def extract(pattern, text, flags=re.IGNORECASE | re.DOTALL):
    """
    Return the first captured group while
    automatically cleaning excessive whitespace.
    """

    match = re.search(pattern, text, flags)

    if not match:
        return None

    return " ".join(match.group(1).split()).strip()


def import_performance(email_text):
    """
    Import a Partner Performance email into
    the PerformanceSnapshot table.
    """

    imported = 0
    skipped = 0
    errors = 0

    try:
        # --------------------------------------------------
        # Normalize Email
        # --------------------------------------------------

        email_text = re.sub(r"\r\n?", "\n", email_text)

        # --------------------------------------------------
        # Report Date
        # --------------------------------------------------

        report_date = datetime.today().date()

        report_date_text = extract(
            r"REPORT\s+AS\s+AT\s+(\d{1,2}[A-Z]{2}\s+\w+\s+\d{4})",
            email_text,
        )

        if report_date_text:

            try:

                cleaned_date = re.sub(
                    r"(\d{1,2})(ST|ND|RD|TH)",
                    r"\1",
                    report_date_text,
                    flags=re.IGNORECASE,
                )

                report_date = datetime.strptime(cleaned_date, "%d %B %Y").date()

            except Exception:
                pass

        # --------------------------------------------------
        # Partner Name
        # --------------------------------------------------

        partner_name = extract(
            r"\d{4}\s+([A-Z0-9\s&\-\(\)]+?),\s*Dear\s+Partner",
            email_text,
        )

        if partner_name:
            partner_name = partner_name.title()

        else:
            partner_name = "Unknown Partner"

        # --------------------------------------------------
        # Contract Status
        # --------------------------------------------------

        contract_status = extract(
            r"Signed\s+Contract\s+Status:\s*(.*?)\s*KPI",
            email_text,
        )

        if not contract_status:
            contract_status = "Unknown"

        # --------------------------------------------------
        # KPI Section
        # --------------------------------------------------

        gross_adds = clean_number(
            extract(
                r"Partner\s+Gross\s+Adds\s*([\d,]+)",
                email_text,
            )
        )

        sim_billing = clean_number(
            extract(
                r"Sim\s+Kits\s+Billing\s*([\d,]+)",
                email_text,
            )
        )

        active_agents_percent = clean_number(
            extract(
                r"%\s*Active\s+Agents\s*([\d\.]+%)",
                email_text,
            )
        )

        back_margin_rate = clean_number(
            extract(
                r"Back\s+Margin\s+Rate\s*([\d\.]+%)",
                email_text,
            )
        )

        # --------------------------------------------------
        # Apply Defaults
        # --------------------------------------------------

        gross_adds_target = 2000

        sim_billing_target = 2000

        active_agents_target = 100.0

        target_back_margin_rate = 3.75

        # --------------------------------------------------
        # Commercial Metrics
        # --------------------------------------------------

        primaries_purchased = clean_number(
            extract(
                r"Primaries\s+Purchased\s*([\d,]+)",
                email_text,
            )
        )

        agent_led_airtime = clean_number(
            extract(
                r"Agent\s+Led\s+Airtime(?:\s*\(Direct\))?\s*([\d,]+)",
                email_text,
            )
        )

        retailer_self_recharges = clean_number(
            extract(
                r"Retailer\s+Influenced\s+Self\s+Recharges\s*([\d,]+)",
                email_text,
            )
        )

        total_airtime = clean_number(
            extract(
                r"Total\s+Airtime\s*([\d,]+)",
                email_text,
            )
        )

        projected_commission = clean_number(
            extract(
                r"Projected\s+Back\s+Margin\s+Commission\s*([\d,]+)",
                email_text,
            )
        )

        # --------------------------------------------------
        # Airtel Money Opportunity
        # --------------------------------------------------

        total_agents = clean_number(
            extract(
                r"Total\s+Agents\s+in\s+Cluster\s*([\d,]+)",
                email_text,
            )
        )

        active_agents = clean_number(
            extract(
                r"Agents\s+Served\s+with\s+1K\s*\+\s*&\s*5TXN\s*([\d,]+)",
                email_text,
            )
        )

        # --------------------------------------------------
        # Create or Update Performance Snapshot
        # --------------------------------------------------

        snapshot = PerformanceSnapshot.query.filter_by(report_date=report_date).first()

        if snapshot is None:

            snapshot = PerformanceSnapshot(report_date=report_date)

            db.session.add(snapshot)

            imported += 1

        else:

            skipped += 1

        # --------------------------------------------------
        # Header Information
        # --------------------------------------------------

        snapshot.partner_name = partner_name
        snapshot.contract_status = contract_status

        # --------------------------------------------------
        # KPI Values
        # --------------------------------------------------

        snapshot.gross_adds = gross_adds
        snapshot.gross_adds_target = gross_adds_target

        snapshot.sim_billing = sim_billing
        snapshot.sim_billing_target = sim_billing_target

        snapshot.active_agents_percent = active_agents_percent
        snapshot.active_agents_target = active_agents_target

        snapshot.back_margin_rate = back_margin_rate
        snapshot.target_back_margin_rate = target_back_margin_rate

        # --------------------------------------------------
        # Commercial Metrics
        # --------------------------------------------------

        snapshot.primaries_purchased = primaries_purchased

        snapshot.agent_led_airtime = agent_led_airtime

        snapshot.retailer_self_recharges = retailer_self_recharges

        snapshot.total_airtime = total_airtime

        snapshot.projected_commission = projected_commission

        # --------------------------------------------------
        # Airtel Money Opportunity
        # --------------------------------------------------

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
