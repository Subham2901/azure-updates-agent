"""SQLite-backed memory of seen updates.

Answers the agent's core question: which fetched records are NEW,
which are CHANGED, and which are already known and unchanged.
All writes are transactional (crash-safe) and idempotent (rerun-safe).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from azure_updates_agent.models import AzureUpdate

_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_updates (
    id          TEXT PRIMARY KEY,
    modified    TEXT,
    status      TEXT NOT NULL,
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Delta:
    """Result of reconciling fetched updates against stored state."""

    new: tuple[AzureUpdate, ...] = ()
    changed: tuple[AzureUpdate, ...] = ()
    unchanged_count: int = 0


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def reconcile(self, updates: list[AzureUpdate]) -> Delta:
        """Classify updates as new/changed/unchanged and record them.

        Atomic: if this raises, no partial state is written.
        Idempotent: reconciling the same list twice yields
        (first call: N new) then (second call: all unchanged).
        """
        now = datetime.now(timezone.utc).isoformat()
        new: list[AzureUpdate] = []
        changed: list[AzureUpdate] = []
        unchanged = 0

        with self._conn:  # one transaction for the whole batch
            for u in updates:
                row = self._conn.execute(
                    "SELECT modified, status FROM seen_updates WHERE id = ?",
                    (u.id,),
                ).fetchone()

                u_modified = u.modified.isoformat() if u.modified else None

                if row is None:
                    new.append(u)
                elif row[0] != u_modified or row[1] != u.status.value:
                    changed.append(u)
                else:
                    unchanged += 1

                self._conn.execute(
                    """
                    INSERT INTO seen_updates (id, modified, status, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        modified = excluded.modified,
                        status   = excluded.status,
                        last_seen = excluded.last_seen
                    """,
                    (u.id, u_modified, u.status.value, now, now),
                )

        return Delta(new=tuple(new), changed=tuple(changed), unchanged_count=unchanged)