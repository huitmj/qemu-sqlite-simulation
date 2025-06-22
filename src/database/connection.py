import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional

class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "simulation.db"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.db_path = db_path
                    cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    uuid TEXT PRIMARY KEY,
                    vm_name TEXT NOT NULL,
                    commands TEXT NOT NULL,
                    timeout INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'acknowledged', 'running', 'cancelled', 'hold', 'done'))
                )
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_requests_timestamp 
                AFTER UPDATE ON requests
                FOR EACH ROW
                BEGIN
                    UPDATE requests SET updated_at = CURRENT_TIMESTAMP WHERE uuid = NEW.uuid;
                END
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_work_log_table(self, request_uuid: str):
        table_name = f"work_log_{request_uuid.replace('-', '_')}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    output TEXT,
                    log_type TEXT CHECK (log_type IN ('boot', 'command', 'stdout', 'stderr'))
                )
            """)
            conn.commit()
        
        return table_name
    
    def get_work_log_table_name(self, request_uuid: str) -> str:
        return f"work_log_{request_uuid.replace('-', '_')}"