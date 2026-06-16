import json
import logging
from typing import Iterator, Dict, Any

logger = logging.getLogger(__name__)

def read_vaultmind_logs(filepath: str) -> Iterator[Dict[str, Any]]:
    """Stream JSONL logs from VaultMind or general audit trail."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    yield json.loads(clean_line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON line {line_num} in {filepath}: {e}")
    except FileNotFoundError:
        logger.error(f"Log file not found: {filepath}")
        raise
    except Exception as e:
        logger.error(f"Error reading log file {filepath}: {e}")
        raise
