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
    Scans summary + needs + location for severity keywords.
    Returns score 0-10.
    """
    text_blob = " ".join([
        str(report.get("summary") or ""),
        str(report.get("location") or ""),
        " ".join(report.get("needs") or []),   # FIX: handles None needs without crash
    ]).lower()

    total = 0
    for keyword, weight in SEVERITY_KEYWORDS.items():
        if keyword in text_blob:
            total += weight

    return min(total, 10)


def compute_people_score(report: Dict[str, Any]) -> float:
    """
    Normalizes affected_people to 0-10 scale.
    10,000+ people = maximum score.
    """
    raw = report.get("affected_people", 0)

    try:
        count = int(float(raw or 0))           # FIX: handles "250.0" and None
    except (TypeError, ValueError):
        count = 0

    return min(count / 1000, 10)              # FIX: 1000 people ≠ 10000 people, scale raised


def compute_urgency_score(report: Dict[str, Any]) -> float:
    """
    Extracts urgency from report safely.
    Defaults to 5 if missing or invalid.
    """
    raw = report.get("urgency", 5)
    try:
        score = float(raw)
        return max(1.0, min(score, 10.0))
    except (TypeError, ValueError):
        return 5.0


def compute_priority_score(report: Dict[str, Any]) -> float:
    """
    Master scoring function.
    Combines urgency (50%), people count (30%), keyword severity (20%).
    """
    urgency = compute_urgency_score(report)
    people = compute_people_score(report)
    keywords = compute_keyword_score(report)

    score = (urgency * 0.5) + (people * 0.3) + (keywords * 0.2)
    return round(score, 2)


def rank_reports(reports: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Attaches priority_score + score_breakdown to each report,
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

    scored.sort(key=lambda r: r["priority_score"], reverse=True)

    for i, report in enumerate(scored):
        report["rank"] = i + 1

    return scored[:top_n]
