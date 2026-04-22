import sys
import os
from datetime import datetime

if sys.platform.startswith("linux"):
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "query_history.db")

def init_history_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            query      TEXT NOT NULL,
            task       TEXT NOT NULL,
            domain     TEXT NOT NULL,
            draft      TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

def save_query(query: str, task: str, domain: str, draft: str, confidence: int):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO history (query, task, domain, draft, confidence, created_at) VALUES (?,?,?,?,?,?)",
        (query, task, domain, draft, confidence, datetime.utcnow().isoformat())
    )
    con.commit()
    con.close()

def get_history(limit: int = 20) -> list:
    con = sqlite3.connect(DB_PATH)
    cur = con.execute(
        "SELECT id, query, task, domain, draft, confidence, created_at "
        "FROM history ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    con.close()
    return [
        {"id": r[0], "query": r[1], "task": r[2], "domain": r[3],
         "draft": r[4], "confidence": r[5], "created_at": r[6]}
        for r in rows
    ]
