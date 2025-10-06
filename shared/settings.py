import os
import sqlite3
import hashlib
import secrets
from typing import Any, Dict, Optional, List


SETTINGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS app_users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL
);
"""

DEFAULT_SETTINGS: Dict[str, str] = {
    "client_directory": "",
    "server_ip": ""
}


class SettingsManager:
    """Persist application settings in notes.db and manage optional user accounts."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = db_path or os.path.join(base_dir, "notes.db")
        self._connection = sqlite3.connect(self.db_path)
        self._connection.execute("PRAGMA foreign_keys = ON;")
        self._connection.row_factory = sqlite3.Row
        self._ensure_schema()
        self._bootstrap_defaults()
        self._ensure_default_admin()

    # ------------------------------------------------------------------
    # Schema helpers
    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(SETTINGS_TABLE_SQL)
        cursor.execute(USERS_TABLE_SQL)
        self._connection.commit()
        cursor.close()

    def _bootstrap_defaults(self) -> None:
        cursor = self._connection.cursor()
        for key, value in DEFAULT_SETTINGS.items():
            cursor.execute(
                "INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)",
                (key, value)
            )
        self._connection.commit()
        cursor.close()

    # ------------------------------------------------------------------
    # General settings accessors
    # ------------------------------------------------------------------
    def get(self, key: str, default: Optional[Any] = None) -> str:
        cursor = self._connection.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return DEFAULT_SETTINGS.get(key, default if default is not None else "")
        return row["value"]

    def set(self, key: str, value: Any) -> None:
        value_str = "" if value is None else str(value)
        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO app_settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value_str)
        )
        self._connection.commit()
        cursor.close()

    # Convenience properties for common settings
    @property
    def client_directory(self) -> str:
        return self.get("client_directory")

    @client_directory.setter
    def client_directory(self, path: str) -> None:
        self.set("client_directory", path)

    @property
    def server_ip(self) -> str:
        return self.get("server_ip")

    @server_ip.setter
    def server_ip(self, ip: str) -> None:
        self.set("server_ip", ip)

    def _ensure_default_admin(self) -> None:
        if not self.list_users():
            self.create_user("admin", "admin")

    # ------------------------------------------------------------------
    # User account helpers (optional feature for distribution)
    # ------------------------------------------------------------------
    def create_user(self, username: str, password: str) -> bool:
        if not username or not password:
            return False
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        try:
            cursor = self._connection.cursor()
            cursor.execute(
                "INSERT INTO app_users(username, password_hash, salt) VALUES(?, ?, ?)",
                (username, password_hash, salt)
            )
            self._connection.commit()
            cursor.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username: str, password: str) -> bool:
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT password_hash, salt FROM app_users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return False
        expected_hash = row["password_hash"]
        salt = row["salt"]
        return secrets.compare_digest(expected_hash, self._hash_password(password, salt))

    def delete_user(self, username: str) -> None:
        cursor = self._connection.cursor()
        cursor.execute("DELETE FROM app_users WHERE username = ?", (username,))
        self._connection.commit()
        cursor.close()

    def list_users(self) -> List[str]:
        cursor = self._connection.cursor()
        cursor.execute("SELECT username FROM app_users ORDER BY username")
        rows = cursor.fetchall()
        cursor.close()
        return [row["username"] for row in rows]

    def _hash_password(self, password: str, salt: str) -> str:
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000)
        return dk.hex()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None
