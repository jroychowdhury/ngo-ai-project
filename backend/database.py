# database.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "reports.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            needs TEXT,
            affected_people INTEGER DEFAULT 0,
            urgency INTEGER DEFAULT 5,
            categories TEXT,
            summary TEXT,
            submitted_by TEXT,
            timestamp TEXT,
            ai_summary TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_report(report: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (location, needs, affected_people, urgency, categories, summary, submitted_by, timestamp, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report.get("location", "Unknown"),
        json.dumps(report.get("needs") or []),
        int(float(report.get("affected_people", 0) or 0)),  # FIX: handles "250.0" and None
        int(float(report.get("urgency", 5) or 5)),          # FIX: handles float strings and None
        json.dumps(report.get("categories") or []),
        report.get("summary", ""),
        report.get("submitted_by", "Unknown"),
        datetime.utcnow().isoformat(),
        report.get("ai_summary", ""),
    ))
    conn.commit()
    conn.close()

def get_all_reports():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, location, needs, affected_people, urgency, categories,
               summary, submitted_by, timestamp, ai_summary
        FROM reports ORDER BY urgency DESC, timestamp DESC
    """)                                        # FIX: added timestamp DESC as tiebreaker
    rows = cursor.fetchall()
    conn.close()

    reports = []
    for row in rows:
        reports.append({
            "id": row[0],
            "location": row[1],
            "needs": json.loads(row[2]) if row[2] else [],
            "affected_people": row[3],
            "urgency": row[4],
            "categories": json.loads(row[5]) if row[5] else [],
            "summary": row[6],
            "submitted_by": row[7],
            "timestamp": row[8],
            "ai_summary": row[9] if row[9] else "",
        })
    return reports