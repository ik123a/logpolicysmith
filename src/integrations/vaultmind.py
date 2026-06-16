import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def fetch_vaultmind_logs(days: int = 7, db_path: Path = None) -> List[Dict[str, Any]]:
    """Fetch logs from VaultMind's SQLite database."""
    if db_path is None:
        db_path = Path.home() / ".vaultmind" / "audit.db"
    
    if not db_path.exists():
        logger.warning(f"VaultMind SQLite database not found at: {db_path}")
        return []
        
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verify if audit_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        if not cursor.fetchone():
            logger.warning("Table 'audit_log' not found in VaultMind database.")
            return []
            
        cursor.execute("""
            SELECT timestamp, agent_id, action, tool, path, decision
            FROM audit_log
            WHERE timestamp > datetime('now', ?)
            ORDER BY timestamp
        """, (f'-{days} days',))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "timestamp": r[0],
            "agent_id": r[1],
            "action": r[2],
            "tool": r[3],
            "path": r[4],
            "decision": r[5]
        } for r in rows]
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error querying VaultMind database: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error reading VaultMind database: {e}")
        return []
