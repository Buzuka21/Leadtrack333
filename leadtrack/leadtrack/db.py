"""SQLite storage layer for leadtrack."""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_DIR = Path.home() / ".leadtrack"
DB_PATH = DB_DIR / "leads.db"

STAGES = ["new", "contacted", "meeting", "proposal", "won", "lost"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company TEXT,
    email TEXT,
    phone TEXT,
    stage TEXT NOT NULL DEFAULT 'new',
    followup_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
);
"""


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def now():
    return datetime.now().isoformat(timespec="seconds")


def add_lead(name, company=None, email=None, phone=None, stage="new"):
    if stage not in STAGES:
        raise ValueError(f"Invalid stage '{stage}'. Must be one of: {', '.join(STAGES)}")
    conn = get_connection()
    ts = now()
    cur = conn.execute(
        "INSERT INTO leads (name, company, email, phone, stage, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, company, email, phone, stage, ts, ts),
    )
    conn.commit()
    lead_id = cur.lastrowid
    conn.close()
    return lead_id


def list_leads(stage=None, search=None):
    conn = get_connection()
    query = "SELECT * FROM leads"
    conditions = []
    params = []
    if stage:
        conditions.append("stage = ?")
        params.append(stage)
    if search:
        conditions.append("(name LIKE ? OR company LIKE ? OR email LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_lead(lead_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    return row


def update_lead(lead_id, **fields):
    if not fields:
        return
    if "stage" in fields and fields["stage"] not in STAGES:
        raise ValueError(f"Invalid stage '{fields['stage']}'. Must be one of: {', '.join(STAGES)}")
    conn = get_connection()
    fields["updated_at"] = now()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [lead_id]
    conn.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", params)
    conn.commit()
    conn.close()


def delete_lead(lead_id):
    conn = get_connection()
    conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()


def add_note(lead_id, note):
    conn = get_connection()
    conn.execute(
        "INSERT INTO notes (lead_id, note, created_at) VALUES (?, ?, ?)",
        (lead_id, note, now()),
    )
    conn.execute("UPDATE leads SET updated_at = ? WHERE id = ?", (now(), lead_id))
    conn.commit()
    conn.close()


def get_notes(lead_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notes WHERE lead_id = ? ORDER BY created_at DESC", (lead_id,)
    ).fetchall()
    conn.close()
    return rows


def get_followups_due(before_date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM leads WHERE followup_date IS NOT NULL AND followup_date <= ? "
        "AND stage NOT IN ('won', 'lost') ORDER BY followup_date ASC",
        (before_date,),
    ).fetchall()
    conn.close()
    return rows


def stats():
    conn = get_connection()
    rows = conn.execute(
        "SELECT stage, COUNT(*) as count FROM leads GROUP BY stage"
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()["c"]
    conn.close()
    return {"total": total, "by_stage": {r["stage"]: r["count"] for r in rows}}
