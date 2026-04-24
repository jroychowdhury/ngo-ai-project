# priority_engine.py

from typing import List, Dict, Any

# Severity keywords with individual weights
SEVERITY_KEYWORDS = {
    "death": 10,
    "died": 10,
    "dead": 10,
    "earthquake": 9,
    "flood": 8,
    "collapse": 8,
    "collapsed": 8,
    "fire": 8,
    "critical": 7,
    "trapped": 7,
    "missing": 7,
    "injured": 6,
    "hospital": 6,
    "storm": 6,
    "cyclone": 6,
    "no food": 6,
    "starvation": 7,
    "no water": 6,
    "disease": 6,
    "outbreak": 7,
    "homeless": 5,
    "shelter": 4,
    "damaged": 4,
    "urgent": 5,
}

def compute_keyword_score(report: Dict[str, Any]) -> float:
    """
    Scans summary + needs for severity keywords.
    Returns score 0-10.
    """
    # Build a single searchable string from relevant fields
    text_blob = " ".join([
        str(report.get("summary", "")),
        str(report.get("location", "")),
        " ".join(report.get("needs", [])),
    ]).lower()

    total = 0
    for keyword, weight in SEVERITY_KEYWORDS.items():
        if keyword in text_blob:
            total += weight

    # Cap at 10
    return min(total, 10)


def compute_people_score(report: Dict[str, Any]) -> float:
    """
    Normalizes affected_people to 0-10 scale.
    Assumes 1000+ people = maximum score.
    """
    raw = report.get("affected_people", 0)

    # Handle None or non-integer gracefully
    try:
        count = int(raw)
    except (TypeError, ValueError):
        count = 0

    # Normalize: 0-1000 mapped to 0-10
    return min(count / 100, 10)


def compute_urgency_score(report: Dict[str, Any]) -> float:
    """
    Extracts urgency from report safely.
    Defaults to 5 if missing or invalid.
    """
    raw = report.get("urgency", 5)
    try:
        score = float(raw)
        return max(1.0, min(score, 10.0))  # Clamp between 1-10
    except (TypeError, ValueError):
        return 5.0


def compute_priority_score(report: Dict[str, Any]) -> float:
    """
    Master scoring function.
    Combines urgency, people count, and keyword severity.
    """
    urgency = compute_urgency_score(report)
    people = compute_people_score(report)
    keywords = compute_keyword_score(report)

    score = (urgency * 0.5) + (people * 0.3) + (keywords * 0.2)
    return round(score, 2)


def rank_reports(reports: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Takes raw reports list, attaches priority_score to each,
    sorts descending, returns top_n.
    """
    if not reports:
        return []

    scored = []
    for report in reports:
        enriched = dict(report)  # Don't mutate original
        enriched["priority_score"] = compute_priority_score(report)
        enriched["score_breakdown"] = {
            "urgency_component": round(compute_urgency_score(report) * 0.5, 2),
            "people_component": round(compute_people_score(report) * 0.3, 2),
            "keyword_component": round(compute_keyword_score(report) * 0.2, 2),
        }
        scored.append(enriched)

    # Sort by priority_score descending
    scored.sort(key=lambda r: r["priority_score"], reverse=True)

    # Add rank field
    for i, report in enumerate(scored):
        report["rank"] = i + 1

    return scored[:top_n]