"""
VERITAS AI - SQLite Forensic History Database Manager.

Persists structured forensic logs, metrics, verdicts, and audit records locally.
Does NOT store raw image payloads to keep disk footprint minimal and respect privacy.
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

DEFAULT_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "veritas_history.db")


class ForensicDatabaseManager:
    """
    Manages SQLite database connection and operations for forensic history records.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forensic_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_uuid TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_format TEXT NOT NULL,
                    dimensions TEXT NOT NULL,
                    file_size_kb REAL NOT NULL,
                    prediction TEXT NOT NULL,
                    confidence_score REAL,
                    manipulated_probability REAL,
                    ela_mean_error REAL,
                    noise_inconsistency_score REAL,
                    copy_move_detected INTEGER DEFAULT 0,
                    num_suspicious_zones INTEGER DEFAULT 0,
                    metadata_risk TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    notes_summary TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON forensic_records(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prediction ON forensic_records(prediction)")
            conn.commit()

    def record_analysis(
        self,
        analysis_uuid: str,
        filename: str,
        file_format: str,
        dimensions: str,
        file_size_kb: float,
        prediction: str,
        confidence_score: Optional[float],
        manipulated_probability: Optional[float],
        ela_mean_error: float,
        noise_inconsistency_score: float,
        copy_move_detected: bool,
        num_suspicious_zones: int,
        metadata_risk: str,
        model_version: str,
        notes_summary: str,
    ) -> int:
        """Inserts a new forensic record and returns its record ID."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO forensic_records (
                    analysis_uuid, timestamp, filename, file_format, dimensions,
                    file_size_kb, prediction, confidence_score, manipulated_probability,
                    ela_mean_error, noise_inconsistency_score, copy_move_detected,
                    num_suspicious_zones, metadata_risk, model_version, notes_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis_uuid,
                ts,
                filename,
                file_format,
                dimensions,
                file_size_kb,
                prediction,
                confidence_score,
                manipulated_probability,
                ela_mean_error,
                noise_inconsistency_score,
                1 if copy_move_detected else 0,
                num_suspicious_zones,
                metadata_risk,
                model_version,
                notes_summary,
            ))
            conn.commit()
            return cursor.lastrowid

    def get_records(
        self,
        limit: int = 100,
        search_query: str = "",
        verdict_filter: str = "ALL",
    ) -> List[Dict[str, Any]]:
        """Queries forensic history records with optional search and verdict filtering."""
        query = "SELECT * FROM forensic_records WHERE 1=1"
        params: List[Any] = []

        if search_query:
            query += " AND (filename LIKE ? OR analysis_uuid LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if verdict_filter and verdict_filter != "ALL":
            query += " AND prediction = ?"
            params.append(verdict_filter)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single forensic record by primary key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM forensic_records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_record(self, record_id: int) -> bool:
        """Deletes a specific forensic record."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM forensic_records WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def purge_history(self) -> int:
        """Deletes all records from history database and returns number of removed rows."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM forensic_records")
            deleted = cursor.rowcount
            conn.commit()
            return deleted

    def get_statistics(self) -> Dict[str, Any]:
        """Calculates aggregate statistics across the historical dataset."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM forensic_records")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM forensic_records WHERE prediction = 'Authentic'")
            auth_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM forensic_records WHERE prediction = 'Potentially Manipulated'")
            manip_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM forensic_records WHERE prediction = 'Inconclusive'")
            inconclusive_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM forensic_records WHERE prediction = 'MODEL NOT TRAINED'")
            untrained_count = cursor.fetchone()[0]

            return {
                "total_analyses": total,
                "authentic_count": auth_count,
                "manipulated_count": manip_count,
                "inconclusive_count": inconclusive_count,
                "untrained_count": untrained_count,
            }
