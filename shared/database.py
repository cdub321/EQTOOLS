import mysql.connector
from mysql.connector import Error
from tkinter import messagebox


class DatabaseManager:
    """Singleton database manager for EQ Tools Suite"""

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings_manager = None
            cls._instance._last_host = None
        return cls._instance

    def configure(self, settings_manager):
        self._settings_manager = settings_manager

    def connect(self):
        """Get or create database connection using configured settings"""
        host = ""
        if self._settings_manager:
            host = (self._settings_manager.server_ip or "").strip()

        if not host:
            messagebox.showerror(
                "Database Configuration",
                "Server IP address is not set. Please configure it in the Admin tab before connecting.",
            )
            return None

        if self._connection and self._connection.is_connected() and host != self._last_host:
            self.close()

        if self._connection is None or not self._connection.is_connected():
            try:
                self._connection = mysql.connector.connect(
                    host=host,
                    user="eqemu",
                    password="eqemu",
                    database="peq"
                )
                self._last_host = host
            except Error as err:
                messagebox.showerror("Database Error", f"Failed to connect to database:\n{err}")
                return None
        return self._connection
    
    def get_cursor(self, dictionary=True):
        """Get a cursor for database operations"""
        conn = self.connect()
        if conn:
            return conn.cursor(dictionary=dictionary)
        return None
    
    def execute_query(self, query, params=(), fetch_all=True):
        """Execute a SELECT query and return results"""
        cursor = self.get_cursor()
        if not cursor:
            return []
        
        try:
            cursor.execute(query, params)
            if fetch_all:
                return cursor.fetchall()
            else:
                return cursor.fetchone()
        except Error as err:
            messagebox.showerror("Database Error", f"Query failed:\n{err}")
            return [] if fetch_all else None
        finally:
            cursor.close()
    
    def execute_update(self, query, params=()):
        """Execute an INSERT, UPDATE, or DELETE query"""
        cursor = self.get_cursor()
        if not cursor:
            return False
        
        try:
            cursor.execute(query, params)
            self._connection.commit()
            return True
        except Error as err:
            messagebox.showerror("Database Error", f"Update failed:\n{err}")
            self._connection.rollback()
            return False
        finally:
            cursor.close()
    
    def close(self):
        """Close the database connection"""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            self._connection = None
            self._last_host = None
