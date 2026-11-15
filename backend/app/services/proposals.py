import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Optional
from app.config import settings
from app.models import PolicyProposal, ProposalAction

def get_db_connection():
    settings.DATA_DIR_PATH = settings.CONFIG_DIR.parent / "data"
    settings.DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
    db_path = settings.DATA_DIR_PATH / "clearpath.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            trigger TEXT NOT NULL,
            grap_stage TEXT NOT NULL,
            actions_json TEXT NOT NULL,
            status TEXT NOT NULL,
            decided_at TEXT,
            officer_note TEXT
        )
    """)
    conn.commit()
    
    # Check if empty, seed initial proposal
    cursor.execute("SELECT COUNT(*) FROM proposals")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_proposals = [
            {
                "id": "pp_001",
                "created_at": "2026-11-15T11:30:00Z",
                "trigger": "Forecast PM2.5 exceeds Very Poor band (>250 µg/m³) at Anand Vihar Hub in 6 h",
                "grap_stage": "Stage II (Very Poor: AQI 301-400)",
                "actions": [
                    {
                        "type": "divert_heavy_vehicles",
                        "target": "Anand Vihar ISBT & Ghazipur Freight Inflow",
                        "rationale": "Divert non-destined commercial trucks to Eastern Peripheral Expressway (EPE) to avoid Anand Vihar severe hotspot cluster and adjacent educational institutions.",
                        "est_impact": {
                            "pm25_reduction_pct": 14.5,
                            "added_delay_min": 18.0,
                            "confidence": "medium"
                        },
                        "source_refs": [
                            "CAQM GRAP Stage II Directive Item 4: Regulate diesel generator sets and divert non-essential commercial vehicles from severe pollution hot spots."
                        ]
                    },
                    {
                        "type": "adjust_signal_timing",
                        "target": "Vikas Marg & Road 56 Intersections",
                        "rationale": "Extend green signal split on outflow arterials by 20% to prevent idling exhaust build-up under stagnant wind conditions.",
                        "est_impact": {
                            "pm25_reduction_pct": 6.2,
                            "added_delay_min": -4.0,
                            "confidence": "medium"
                        },
                        "source_refs": [
                            "CPCB Comprehensive Action Plan (CAP) for Air Pollution Control in Delhi-NCR (Traffic Management Protocols)."
                        ]
                    },
                    {
                        "type": "publish_advisory",
                        "target": "East Delhi Citizens & Commuters",
                        "rationale": "Advise schools in Anand Vihar and Patparganj to suspend outdoor physical training between 16:00 and 20:00 IST.",
                        "est_impact": {
                            "pm25_reduction_pct": 0.0,
                            "added_delay_min": 0.0,
                            "confidence": "high"
                        },
                        "source_refs": [
                            "CPCB National AQI Health Advisory Guide for Very Poor / Severe Category Air."
                        ]
                    }
                ],
                "status": "pending",
                "decided_at": None,
                "officer_note": None
            }
        ]
        for p in seed_proposals:
            cursor.execute(
                "INSERT INTO proposals VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    p["id"],
                    p["created_at"],
                    p["trigger"],
                    p["grap_stage"],
                    json.dumps(p["actions"]),
                    p["status"],
                    p["decided_at"],
                    p["officer_note"]
                )
            )
        conn.commit()
    conn.close()

def list_proposals(status_filter: Optional[str] = None) -> List[PolicyProposal]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("SELECT * FROM proposals WHERE status = ? ORDER BY created_at DESC", (status_filter,))
    else:
        cursor.execute("SELECT * FROM proposals ORDER BY created_at DESC")
    rows = cursor.fetchall()
    proposals = []
    for r in rows:
        proposals.append(PolicyProposal(
            id=r["id"],
            created_at=r["created_at"],
            trigger=r["trigger"],
            grap_stage=r["grap_stage"],
            actions=[ProposalAction(**a) for a in json.loads(r["actions_json"])],
            status=r["status"],
            decided_at=r["decided_at"],
            officer_note=r["officer_note"]
        ))
    conn.close()
    return proposals

def add_proposal(prop: PolicyProposal) -> PolicyProposal:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO proposals VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            prop.id,
            prop.created_at,
            prop.trigger,
            prop.grap_stage,
            json.dumps([a.model_dump() for a in prop.actions]),
            prop.status,
            prop.decided_at,
            prop.officer_note
        )
    )
    conn.commit()
    conn.close()
    return prop

def decide_proposal(proposal_id: str, decision: str, officer_note: Optional[str] = None) -> Optional[PolicyProposal]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "UPDATE proposals SET status = ?, decided_at = ?, officer_note = ? WHERE id = ?",
        (decision, now_iso, officer_note, proposal_id)
    )
    conn.commit()
    conn.close()
    props = list_proposals()
    return next((p for p in props if p.id == proposal_id), None)
