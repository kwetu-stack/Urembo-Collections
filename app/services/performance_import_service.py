import re
from datetime import datetime

from app import db
from app.models.performance import PerformanceSnapshot
from app.services.import_history_service import log_import


def clean_number(value):
    if value is None:
        return None

    value = str(value).replace(",", "").replace("%", "").strip()

    if not value or value.lower() == "nan":
        return None

    try:
        if "." in value:
            return float(value)

        return int(value)

    except (ValueError, TypeError):
        return None


def normalize_text(text):
    """
    Normalize Gmail-extracted text so that Airtel's
    table-like report can be parsed reliably.
    """
    text = text or ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Normalize common non-breaking spaces
    text = text.replace("\xa0", " ")

    # Normalize repeated whitespace but preserve line breaks
    lines = []

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


def extract(pattern, text, flags=re.IGNORECASE | re.DOTALL):
    match = re.search(pattern, text, flags)

    if not match:
        return None

    return " ".join(match.group(1).split()).strip()


def extract_metric(label_patterns, text):
    """
    Extract a numeric value associated with a report label.

    Airtel's report is table-based, so the value may appear:
        Label 583
        Label    583
        Label
        583
        Label 583 0.75%

    We deliberately look only in a small area after the
    label so that unrelated numbers elsewhere in the email
    are not accidentally captured.
    """

    if isinstance(label_patterns, str):
        label_patterns = [label_patterns]

    for label in label_patterns:

        # Label followed immediately by the number
        pattern = rf"{label}\s*[:.]?\s*([\d,]+(?:\.\d+)?%?)"

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = clean_number(match.group(1))

            if value is not None:
                return value

        # Label followed by a newline and then the number
        pattern = rf"{label}\s*\n\s*([\d,]+(?:\.\d+)?%?)"

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            value = clean_number(match.group(1))

            if value is not None:
                return value

        # Look within a small window after the label.
        pattern = rf"{label}.{{0,100}}?([\d,]+(?:\.\d+)?%?)"

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            value = clean_number(match.group(1))

            if value is not None:
                return value

    return None


def parse_report_date(email_text, subject=None):
    """
    Airtel report date is the date contained in:
        PARTNER PERFORMANCE REPORT AS AT 16TH JULY 2026

    This is different from the Gmail sent/received date.
    """

    sources = []

    if subject:
        sources.append(subject)

    if email_text:
        sources.append(email_text)

    date_patterns = [
        r"REPORT\s+AS\s+AT\s+(\d{1,2}(?:ST|ND|RD|TH)?\s+\w+\s+\d{4})",
        r"AS\s+AT\s+(\d{1,2}(?:ST|ND|RD|TH)?\s+\w+\s+\d{4})",
        r"AS\s+OF\s+(\d{1,2}(?:ST|ND|RD|TH)?\s+\w+\s+\d{4})",
    ]

    for source in sources:

        for pattern in date_patterns:

            match = re.search(
                pattern,
                source,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            date_text = match.group(1)

            cleaned_date = re.sub(
                r"(\d{1,2})(ST|ND|RD|TH)",
                r"\1",
                date_text,
                flags=re.IGNORECASE,
            )

            for date_format in (
                "%d %B %Y",
                "%d %b %Y",
            ):
                try:
                    return datetime.strptime(
                        cleaned_date,
                        date_format,
                    ).date()

                except ValueError:
                    continue

    # Only use today's date as a last-resort fallback.
    return datetime.today().date()


def parse_partner_name(email_text):
    """
    Actual Airtel format:

        MIKINDANI UREMBO COLLECTIONS,
        Dear Partner,

    Extract the text immediately before 'Dear Partner'.
    """

    text = normalize_text(email_text)

    patterns = [
        r"([A-Z0-9][A-Z0-9\s&()\-]{3,100}),\s*Dear\s+Partner",
        r"([A-Z0-9][A-Z0-9\s&()\-]{3,100})\s+Dear\s+Partner",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            partner_name = match.group(1).strip()

            # Remove obvious preceding report/date text
            partner_name = re.sub(
                r"^.*?\b(?:JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE)\b",
                "",
                partner_name,
                flags=re.IGNORECASE,
            ).strip()

            if partner_name:
                return partner_name.title()

    # Strong fallback for this distributor
    match = re.search(
        r"(MIKINDANI\s+UREMBO\s+COLLECTIONS)",
        text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).title()

    return "Unknown Partner"


def import_performance(email_text, subject=None):
    imported = 0
    updated = 0
    skipped = 0
    errors = 0

    try:
        email_text = normalize_text(email_text)

        # --------------------------------------------------
        # Report identity
        # --------------------------------------------------

        report_date = parse_report_date(
            email_text,
            subject=subject,
        )

        partner_name = parse_partner_name(email_text)

        # --------------------------------------------------
        # Contract
        # --------------------------------------------------

        contract_status = extract(
            r"Signed\s+Contract\s+Status\s*[:.]?\s*(.*?)(?:\n|KPI|Partner\s+Gross\s+Adds)",
            email_text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if contract_status:
            contract_status = contract_status.strip()
        else:
            contract_status = "Unknown"

        # --------------------------------------------------
        # KPI metrics
        # --------------------------------------------------

        gross_adds = extract_metric(
            [
                r"Partner\s+Gross\s+Adds",
                r"Gross\s+Adds",
            ],
            email_text,
        )

        sim_billing = extract_metric(
            [
                r"Sim\s+Kits\s+Billing",
                r"SIM\s+Kits\s+Billing",
                r"SIM\s+Billing",
                r"Sim\s+Billing",
            ],
            email_text,
        )

        active_agents_percent = extract_metric(
            [
                r"%\s*Active\s+Agents",
                r"Active\s+Agents",
            ],
            email_text,
        )

        back_margin_rate = extract_metric(
            [
                r"Back\s+Margin\s+Rate",
                r"Back\s+Margin",
            ],
            email_text,
        )

        primaries_purchased = extract_metric(
            r"Primaries\s+Purchased",
            email_text,
        )

        agent_led_airtime = extract_metric(
            [
                r"Agent\s+Led\s+Airtime\s*\(Direct\)",
                r"Agent\s+Led\s+Airtime",
            ],
            email_text,
        )

        retailer_self_recharges = extract_metric(
            [
                r"Retailer\s+Influenced\s+Self\s+Recharges",
                r"Retailer\s+Self\s+Recharges",
            ],
            email_text,
        )

        total_airtime = extract_metric(
            [
                r"Total\s+Airtime",
            ],
            email_text,
        )

        projected_commission = extract_metric(
            [
                r"Projected\s+Back\s+Margin\s+Commission",
                r"Projected\s+Commission",
            ],
            email_text,
        )

        total_agents = extract_metric(
            [
                r"Total\s+Agents\s+in\s+Cluster",
            ],
            email_text,
        )

        active_agents = extract_metric(
            [
                r"Agents\s+Served\s+with\s+1K\s*\+\s*&\s*5TXN",
            ],
            email_text,
        )

        # --------------------------------------------------
        # Logging for diagnosis
        # --------------------------------------------------

        current_values = {
            "report_date": report_date,
            "partner_name": partner_name,
            "contract_status": contract_status,
            "gross_adds": gross_adds,
            "sim_billing": sim_billing,
            "active_agents_percent": active_agents_percent,
            "back_margin_rate": back_margin_rate,
            "primaries_purchased": primaries_purchased,
            "agent_led_airtime": agent_led_airtime,
            "retailer_self_recharges": retailer_self_recharges,
            "total_airtime": total_airtime,
            "projected_commission": projected_commission,
            "total_agents": total_agents,
            "active_agents": active_agents,
        }

        print("==========================================")
        print("PERFORMANCE REPORT PARSED")
        print("==========================================")

        for key, value in current_values.items():
            print(f"{key}: {value}")

        print("==========================================")

        # --------------------------------------------------
        # Save current snapshot
        # --------------------------------------------------

        snapshot = (
            PerformanceSnapshot.query
            .filter_by(report_date=report_date)
            .first()
        )

        if snapshot is None:

            snapshot = PerformanceSnapshot(
                report_date=report_date
            )

            db.session.add(snapshot)

            imported += 1

        else:

            updated += 1

        # --------------------------------------------------
        # Populate snapshot
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Import history
        # --------------------------------------------------

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