from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from app.backend.core.settings import settings
from app.backend.core.timeutils import utc_now_iso
from app.backend.models.schemas import JobArtifact, JobEvent, JobState, JobStatus, JobType


JobHandler = Callable[[str, dict], list[JobArtifact]]


class JobManager:
    def __init__(self) -> None:
        self.db_path = settings.jobs_db_path
        self._executor = ThreadPoolExecutor(
            max_workers=settings.worker_pool_size,
            thread_name_prefix="voice-engine",
        )
        self._lock = threading.RLock()
        self._handlers: dict[JobType, JobHandler] = {}
        self._active_jobs: set[str] = set()
        self._stop_event = threading.Event()
        self._initialize_db()
        self._recover_running_jobs()
        self._dispatcher = threading.Thread(
            target=self._dispatch_loop,
            name="job-dispatcher",
            daemon=True,
        )
        self._dispatcher.start()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    payload TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS job_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_status_created
                ON jobs(status, created_at);

                CREATE INDEX IF NOT EXISTS idx_events_job_id_id
                ON job_events(job_id, id);

                CREATE INDEX IF NOT EXISTS idx_artifacts_job_id
                ON artifacts(job_id);
                """
            )

    def _recover_running_jobs(self) -> None:
        now = utc_now_iso()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id FROM jobs WHERE status = ?",
                (JobStatus.RUNNING.value,),
            ).fetchall()
            if not rows:
                return
            connection.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE status = ?",
                (JobStatus.QUEUED.value, now, JobStatus.RUNNING.value),
            )
            for row in rows:
                connection.execute(
                    """
                    INSERT INTO job_events(job_id, level, message, data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        "warning",
                        "Job was re-queued after API restart.",
                        None,
                        now,
                    ),
                )

    def register_handler(self, job_type: JobType, handler: JobHandler) -> None:
        with self._lock:
            self._handlers[job_type] = handler

    def create_job(self, job_type: JobType, payload: dict) -> JobState:
        now = utc_now_iso()
        job_id = str(uuid.uuid4())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs(id, type, status, phase, progress, payload, error, created_at, updated_at, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    job_type.value,
                    JobStatus.QUEUED.value,
                    "queued",
                    0,
                    json.dumps(payload, ensure_ascii=False),
                    None,
                    now,
                    now,
                    None,
                    None,
                ),
            )
        self.record_event(job_id, "Job created", level="info", data={"type": job_type.value})
        state = self.get_job(job_id)
        if state is None:
            raise RuntimeError(f"failed to load job {job_id}")
        return state

    def enqueue(self, state: JobState, handler: JobHandler) -> JobState:
        self.register_handler(state.type, handler)
        self.record_event(state.id, "Job queued", level="info")
        return state

    def _dispatch_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._dispatch_once()
            except Exception:
                # Avoid crashing dispatcher thread; errors are visible in failed job states.
                pass
            self._stop_event.wait(settings.job_poll_interval_seconds)

    def _dispatch_once(self) -> None:
        with self._lock:
            available_slots = max(0, settings.worker_pool_size - len(self._active_jobs))
            if available_slots < 1:
                return
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, type
                    FROM jobs
                    WHERE status = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                    """,
                    (JobStatus.QUEUED.value, available_slots),
                ).fetchall()
            for row in rows:
                job_id = str(row["id"])
                if job_id in self._active_jobs:
                    continue
                try:
                    job_type = JobType(row["type"])
                except ValueError:
                    self.update(
                        job_id,
                        status=JobStatus.FAILED,
                        error=f"Unknown job type '{row['type']}'",
                        finished_at=utc_now_iso(),
                    )
                    self.record_event(job_id, "Unknown job type", level="error")
                    continue
                handler = self._handlers.get(job_type)
                if handler is None:
                    continue
                now = utc_now_iso()
                with self._connect() as connection:
                    connection.execute(
                        """
                        UPDATE jobs
                        SET status = ?, started_at = COALESCE(started_at, ?), updated_at = ?
                        WHERE id = ? AND status = ?
                        """,
                        (
                            JobStatus.RUNNING.value,
                            now,
                            now,
                            job_id,
                            JobStatus.QUEUED.value,
                        ),
                    )
                self.record_event(job_id, "Job started", level="info")
                self._active_jobs.add(job_id)
                self._executor.submit(self._run_handler, job_id, handler)

    def _run_handler(self, job_id: str, handler: JobHandler) -> None:
        try:
            state = self.get_job(job_id)
            if state is None:
                return
            artifacts = handler(job_id, state.payload)
            self.update(
                job_id,
                status=JobStatus.COMPLETED,
                phase="completed",
                progress=100,
                artifacts=artifacts,
                finished_at=utc_now_iso(),
            )
            self.record_event(job_id, "Job completed", level="info")
        except Exception as exc:
            self.update(
                job_id,
                status=JobStatus.FAILED,
                error=str(exc),
                finished_at=utc_now_iso(),
            )
            self.record_event(job_id, "Job failed", level="error", data={"error": str(exc)})
        finally:
            with self._lock:
                self._active_jobs.discard(job_id)

    def _artifacts_for_job(self, connection: sqlite3.Connection, job_id: str) -> list[JobArtifact]:
        rows = connection.execute(
            "SELECT type, path FROM artifacts WHERE job_id = ? ORDER BY id ASC",
            (job_id,),
        ).fetchall()
        return [JobArtifact(type=row["type"], path=row["path"]) for row in rows]

    def _state_from_row(self, connection: sqlite3.Connection, row: sqlite3.Row) -> JobState:
        payload = json.loads(row["payload"])
        artifacts = self._artifacts_for_job(connection, row["id"])
        return JobState(
            id=row["id"],
            type=JobType(row["type"]),
            status=JobStatus(row["status"]),
            phase=row["phase"],
            progress=int(row["progress"]),
            payload=payload,
            error=row["error"],
            artifacts=artifacts,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )

    def get_job(self, job_id: str) -> JobState | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            return self._state_from_row(connection, row)

    def list_recent(self, limit: int = 20) -> list[JobState]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._state_from_row(connection, row) for row in rows]

    def update(self, job_id: str, **changes) -> JobState:
        with self._lock:
            state = self.get_job(job_id)
            if state is None:
                raise FileNotFoundError(job_id)
            previous_phase = state.phase
            previous_status = state.status
            previous_progress = state.progress
            data = state.dict()
            artifacts = changes.pop("artifacts", None)
            data.update(changes)
            data["updated_at"] = utc_now_iso()
            new_state = JobState.parse_obj(data)
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE jobs
                    SET status = ?, phase = ?, progress = ?, payload = ?, error = ?, updated_at = ?, started_at = ?, finished_at = ?
                    WHERE id = ?
                    """,
                    (
                        new_state.status.value,
                        new_state.phase,
                        new_state.progress,
                        json.dumps(new_state.payload, ensure_ascii=False),
                        new_state.error,
                        new_state.updated_at,
                        new_state.started_at,
                        new_state.finished_at,
                        new_state.id,
                    ),
                )
                if artifacts is not None:
                    connection.execute("DELETE FROM artifacts WHERE job_id = ?", (job_id,))
                    now = utc_now_iso()
                    for artifact in artifacts:
                        connection.execute(
                            "INSERT INTO artifacts(job_id, type, path, created_at) VALUES (?, ?, ?, ?)",
                            (job_id, artifact.type, artifact.path, now),
                        )
            current = self.get_job(job_id) or new_state
            if (
                current.phase != previous_phase
                or current.status != previous_status
                or current.progress != previous_progress
            ):
                self.record_event(
                    job_id,
                    "Progress update",
                    level="info",
                    data={
                        "status": current.status.value,
                        "phase": current.phase,
                        "progress": current.progress,
                    },
                )
            return current

    def record_event(
        self,
        job_id: str,
        message: str,
        *,
        level: str = "info",
        data: dict | None = None,
    ) -> JobEvent:
        created_at = utc_now_iso()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO job_events(job_id, level, message, data, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    level,
                    message,
                    json.dumps(data, ensure_ascii=False) if data is not None else None,
                    created_at,
                ),
            )
            event_id = int(cursor.lastrowid)
        return JobEvent(
            id=event_id,
            job_id=job_id,
            level=level,
            message=message,
            created_at=created_at,
            data=data,
        )

    def list_events(self, job_id: str, *, since_id: int = 0, limit: int = 500) -> list[JobEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, job_id, level, message, data, created_at
                FROM job_events
                WHERE job_id = ? AND id > ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (job_id, since_id, limit),
            ).fetchall()
        events: list[JobEvent] = []
        for row in rows:
            parsed = json.loads(row["data"]) if row["data"] else None
            events.append(
                JobEvent(
                    id=int(row["id"]),
                    job_id=row["job_id"],
                    level=row["level"],
                    message=row["message"],
                    created_at=row["created_at"],
                    data=parsed,
                )
            )
        return events


job_manager = JobManager()
