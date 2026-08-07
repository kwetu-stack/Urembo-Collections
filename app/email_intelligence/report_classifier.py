import re

SUPPORTED_REPORT_TYPES = {
    "Partner Performance",
    "SIM Issuance",
    "TUDOR AGENTS",
}

REPORT_TYPES = {
    "Partner Performance": [
        r"\bpartner performance\b",
        r"\bperformance report\b",
    ],
    "SIM Issuance": [
        r"\bsim[\s_-]*issuance\b",
        r"\bsim[\s_-]*insuance\b",
        r"\butilization report\b",
        r"\bsim kits billing\b",
    ],
    "TUDOR AGENTS": [
        r"\btudor[\s_-]*agents?\b",
        r"\bagent register\b",
    ],
}

AIRTEL_SENDER_PATTERN = re.compile(r"@(?:ke\.)?airtel\.com", re.IGNORECASE)

AIRTEL_ATTACHMENT_PATTERN = re.compile(
    r"(sim[\s_-]*(issuance|insuance|utilization)|tudor[\s_-]*agents?|agent[\s_-]*register|\d+_sim)",
    re.IGNORECASE,
)

NON_AIRTEL_ATTACHMENT_PATTERN = re.compile(
    r"(statement|certificate|credit.?card|withholding|invoice|receipt|payslip|ncba|kcb)",
    re.IGNORECASE,
)


def normalize_search_text(text):
    cleaned = re.sub(r"[^\w]+", " ", text or "").lower()
    return " ".join(cleaned.split())


def is_airtel_sender(sender):
    return bool(AIRTEL_SENDER_PATTERN.search(sender or ""))


def classify_report(sender, subject, attachment_name="", email_body=""):
    searchable_text = normalize_search_text(
        f"{sender} {subject} {attachment_name} {email_body}"
    )

    report_type = "Other"

    for report_name, keywords in REPORT_TYPES.items():
        if any(re.search(keyword, searchable_text) for keyword in keywords):
            report_type = report_name
            break

    if report_type == "Other" and attachment_name:
        attachment_name_lower = normalize_search_text(attachment_name)

        if re.search(r"\b(tudor|agent register)\b", attachment_name_lower):
            report_type = "TUDOR AGENTS"
        elif re.search(r"\b(sim|utilization|issuance|insuance)\b", attachment_name_lower):
            report_type = "SIM Issuance"

    return report_type


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

    return bool(AIRTEL_ATTACHMENT_PATTERN.search(lower))
