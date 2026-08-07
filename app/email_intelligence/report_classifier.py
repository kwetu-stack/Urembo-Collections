import re

SUPPORTED_REPORT_TYPES = {
    "Partner Performance",
    "SIM Issuance",
    "TUDOR AGENTS",
}


def normalize_search_text(text):
    cleaned = re.sub(r"[^\w]+", " ", text or "").lower()
    return " ".join(cleaned.split())


AIRTEL_SENDER_PATTERN = re.compile(
    r"@(?:ke\.)?airtel\.com",
    re.IGNORECASE,
)


NON_AIRTEL_ATTACHMENT_PATTERN = re.compile(
    r"(statement|certificate|credit.?card|withholding|invoice|receipt|payslip|ncba|kcb)",
    re.IGNORECASE,
)


def is_airtel_sender(sender):
    return bool(AIRTEL_SENDER_PATTERN.search(sender or ""))


def classify_report(sender, subject, attachment_name="", email_body=""):
    text = normalize_search_text(
        f"{sender} {subject} {attachment_name} {email_body}"
    )

    if "partner performance" in text or "performance report" in text:
        return "Partner Performance"

    if (
        "sim issuance" in text
        or "sim insuance" in text
        or "utilization" in text
        or "sim kits billing" in text
    ):
        return "SIM Issuance"

    if (
        "tudor agents" in text
        or "tudor agent" in text
        or "agent register" in text
    ):
        return "TUDOR AGENTS"

    return "Other"


def is_supported_report(report_type):
    return report_type in SUPPORTED_REPORT_TYPES


def is_airtel_attachment(filename):
    if not filename:
        return False

    lower = filename.lower()

    if not lower.endswith((".xlsx", ".xls", ".csv")):
        return False

    if NON_AIRTEL_ATTACHMENT_PATTERN.search(lower):
        return False

    if "tudor" in lower:
        return True

    if "agent" in lower:
        return True

    if "sim" in lower:
        return True

    if "utilization" in lower:
        return True

    if "issuance" in lower:
        return True

    if "insuance" in lower:
        return True

    return False
