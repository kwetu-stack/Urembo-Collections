import re
from datetime import datetime

from app import db
from app.models.performance import PerformanceSnapshot
from app.services.import_history_service import log_import


def clean_number(value):
    if value is None:
        return None

    value = str(value).replace(",", "").replace("%", "").strip()

    if value == "" or value.lower() == "nan":
        return None

    try:
        if "." in value:
            return float(value)

        return int(value)

    except Exception:
        return None


def extract(pattern, text, flags=re.IGNORECASE | re.DOTALL):
    match = re.search(pattern, text, flags)

    if not match:
        return None

    return " ".join(match.group(1).split()).strip()


def extract_metric(label_patterns, text):
    if isinstance(label_patterns, str):
        label_patterns = [label_patterns]

    for label in label_patterns:
        patterns = [
            rf"{label}\s*[:.]?\s*([\d,\.]+%?)",
            rf"{label}\s*\n+\s*([\d,\.]+%?)",
            rf"{label}.*?([\d,\.]+%?)\s*(?:\n|$)",
        ]

        for pattern in patterns:
            value = extract(pattern, text)

            if value is not None:
                cleaned = clean_number(value)

                if cleaned is not None:
                    return cleaned

    return None


def parse_report_date(email_text, subject=None):
    sources = [email_text or ""]

    if subject:
        sources.insert(0, subject)

    date_patterns = [
        r"AS\s+AT\s+(\d{1,2}(?:ST|ND|RD|TH)?\s+\w+\s+\d{4})",
        r"REPORT\s+AS\s+AT\s+(\d{1,2}(?:ST|ND|RD|TH)?\s+\w+\s+\d{4})",
    ]

    for source in sources:
        for pattern in date_patterns:
            report_date_text = extract(pattern, source)

            if not report_date_text:
                continue

            try:
                cleaned_date = re.sub(
                    r"(\d{1,2})(ST|ND|RD|TH)",
                    r"\1",
                    report_date_text,
                    flags=re.IGNORECASE,
                )

                return datetime.strptime(cleaned_date, "%d %B %Y").date()

            except Exception:
                continue

    return datetime.today().date()


def parse_partner_name(email_text):
    patterns = [
        r"([A-Z0-9][A-Z0-9\s&\-\(\)]{3,}?)\s*,\s*Dear\s+Partner",
        r"Dear\s+Partner\s*,?\s*([^\n\r]{3,80})",
        r"(UREMBO[\w\s\-&\(\)]{0,60})",
        r"(MIKINDANI[\w\s\-&\(\)]{0,60})",
    ]

    for pattern in patterns:
        partner_name = extract(pattern, email_text, flags=re.IGNORECASE | re.MULTILINE)

        if partner_name:
            return partner_name.title()

    return "Unknown Partner"


def import_performance(email_text, subject=None):
    imported = 0
    updated = 0
    skipped = 0
    errors = 0

    try:
        email_text = re.sub(r"\r\n?", "\n", email_text or "")

        report_date = parse_report_date(email_text, subject=subject)
        partner_name = parse_partner_name(email_text)

        contract_status = extract(
            r"Signed\s+Contract\s+Status\s*[:.]?\s*(.*?)\s*(?:KPI|Partner Gross Adds|$)",
            email_text,
        ) or "Unknown"

        gross_adds = extract_metric(
            [r"Partner\s+Gross\s+Adds", r"Gross\s+Adds"],
            email_text,
        )

        sim_billing = extract_metric(
            [r"Sim\s+Kits\s+Billing", r"SIM\s+Billing", r"Sim\s+Billing"],
            email_text,
        )

        active_agents_percent = extract_metric(
            [r"%?\s*Active\s+Agents", r"Active\s+Agents\s*%"],
            email_text,
        )

        back_margin_rate = extract_metric(
            [r"Back\s+Margin\s+Rate", r"Back\s+Margin"],
            email_text,
        )

        primaries_purchased = extract_metric(
            [r"Primaries\s+Purchased"],
            email_text,
        )

        agent_led_airtime = extract_metric(
            [r"Agent\s+Led\s+Airtime(?:\s*\(Direct\))?", r"Agent\s+Led\s+Airtime"],
            email_text,
        )

        retailer_self_recharges = extract_metric(
            [r"Retailer\s+Influenced\s+Self\s+Recharges", r"Retailer\s+Self\s+Recharges"],
            email_text,
        )

        total_airtime = extract_metric(
            [r"Total\s+Airt(?:me|r)", r"Total\s+Airtime"],
            email_text,
        )

        projected_commission = extract_metric(
            [r"Projected\s+Back\s+Margin\s+Commission", r"Projected\s+Commission"],
            email_text,
        )

        total_agents = extract_metric(
            [r"Total\s+Agents\s+in\s+Cluster"],
            email_text,
        )

        active_agents = extract_metric(
            [r"Agents\s+Served\s+with\s+1K\s*\+\s*&\s*5TXN"],
            email_text,
        )

        snapshot = PerformanceSnapshot.query.filter_by(report_date=report_date).first()

        if snapshot is None:
            snapshot = PerformanceSnapshot(report_date=report_date)
            db.session.add(snapshot)
            imported += 1
        else:
            updated += 1

        snapshot.partner_name = partner_name
        snapshot.contract_status = contract_status
        snapshot.gross_adds = gross_adds
        snapshot.gross_adds_target = 2000
        snapshot.sim_billing = sim_billing
        snapshot.sim_billing_target = 2000
        snapshot.active_agents_percent = active_agents_percent
        snapshot.active_agents_target = 100.0
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

        history = log_import(
            report_type="Partner Performance",
            filename=subject or "Email Body",
            imported=imported + updated,
            skipped=skipped,
            errors=errors,
            status="Success",
        )
        db.session.add(history)
        db.session.commit()

    except Exception as exc:
        db.session.rollback()
        errors += 1

        history = log_import(
            report_type="Partner Performance",
            filename=subject or "Email Body",
            imported=0,
            skipped=0,
            errors=errors,
            status=f"Failed: {exc}",
        )
        db.session.add(history)
        db.session.commit()

        raise

    return {
        "rows": 1,
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
