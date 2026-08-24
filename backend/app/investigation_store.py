from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


CREATE_INVESTIGATIONS_SQL = """
CREATE TABLE IF NOT EXISTS investigation_results (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
)
"""


class InvestigationResultStore:
    def __init__(self, session: Session):
        self.session = session

    def create_table(self) -> None:
        self.session.execute(text(CREATE_INVESTIGATIONS_SQL))
        self.session.commit()

    def save_once(self, result_id: str, event_id: str, status: str, result: dict[str, Any]) -> bool:
        response = self.session.execute(text("""
            INSERT INTO investigation_results (id, event_id, status, result_json, created_at)
            VALUES (:id, :event_id, :status, :result_json, :created_at)
            ON CONFLICT (event_id) DO NOTHING
        """), {
            "id": result_id,
            "event_id": event_id,
            "status": status,
            "result_json": json.dumps(result, default=str),
            "created_at": datetime.now(timezone.utc),
        })
        self.session.commit()
        return response.rowcount == 1
