"""
VERITAS AI - Database Package.
Local SQLite database management for forensic analysis history and auditing.
"""

from .db_manager import ForensicDatabaseManager, DEFAULT_DB_PATH

__all__ = ["ForensicDatabaseManager", "DEFAULT_DB_PATH"]
