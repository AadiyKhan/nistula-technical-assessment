from __future__ import annotations

import re

QUERY_PATTERNS: dict[str, tuple[str, ...]] = {
    "complaint": (
        r"\bnot working\b",
        r"\bbroken\b",
        r"\bunacceptable\b",
        r"\brefund\b",
        r"\bcomplain\w*\b",
        r"\bno hot water\b",
        r"\bvery disappointed\b",
    ),
    "post_sales_checkin": (
        r"\bcheck[- ]?in\b",
        r"\bcheck[- ]?out\b",
        r"\bwi[- ]?fi\b",
        r"\bpassword\b",
        r"\barrival\b",
    ),
    "special_request": (
        r"\bearly check[- ]?in\b",
        r"\blate check[- ]?out\b",
        r"\bairport transfer\b",
        r"\btransfer\b",
        r"\bchef\b",
        r"\bspecial request\b",
    ),
    "pre_sales_pricing": (
        r"\brate\b",
        r"\bprice\b",
        r"\bcost\b",
        r"\bcharges?\b",
        r"\bfor 2 adults\b",
        r"\bper night\b",
    ),
    "pre_sales_availability": (
        r"\bavailable\b",
        r"\bavailability\b",
        r"\bfree on\b",
        r"\bdates?\b",
        r"\bbook\b",
    ),
}


def classify_message(message_text: str) -> str:
    text = message_text.lower().strip()

    for query_type in ("complaint", "post_sales_checkin", "special_request", "pre_sales_availability", "pre_sales_pricing"):
        for pattern in QUERY_PATTERNS[query_type]:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return query_type

    return "general_enquiry"


def confidence_for_query_type(query_type: str, message_text: str, drafted_reply: str, used_claude: bool) -> float:
    base_scores = {
        "pre_sales_availability": 0.91,
        "pre_sales_pricing": 0.89,
        "post_sales_checkin": 0.84,
        "special_request": 0.76,
        "general_enquiry": 0.71,
        "complaint": 0.48,
    }

    score = base_scores.get(query_type, 0.70)

    if used_claude:
        score += 0.03

    if len(message_text.split()) >= 12:
        score += 0.02

    if drafted_reply.strip():
        score += 0.01

    if query_type == "complaint":
        score = min(score, 0.59)

    return max(0.0, min(1.0, round(score, 2)))


def decide_action(query_type: str, confidence_score: float) -> str:
    if query_type == "complaint":
        return "escalate"
    if confidence_score >= 0.85:
        return "auto_send"
    if confidence_score >= 0.60:
        return "agent_review"
    return "escalate"
