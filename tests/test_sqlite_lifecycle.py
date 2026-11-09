import sqlite3
from unittest.mock import patch

import pytest

from src.integrations.vaultmind import fetch_vaultmind_logs


@pytest.mark.parametrize('schema', ['missing_table', 'missing_columns', 'valid'])
def test_database_connection_is_closed_on_every_query_path(tmp_path, schema):
    database = tmp_path / 'synthetic-audit.db'
    connection = sqlite3.connect(database)
    if schema == 'missing_columns':
        connection.execute('CREATE TABLE audit_log (timestamp TEXT)')
    elif schema == 'valid':
        connection.execute('CREATE TABLE audit_log (timestamp TEXT, agent_id TEXT, action TEXT, tool TEXT, path TEXT, decision TEXT)')
        connection.execute("INSERT INTO audit_log VALUES (datetime('now'), 'synthetic-agent', 'read', 'file', '/sample', 'allow')")
    connection.commit()
    connection.close()

    original_connect = sqlite3.connect
    opened = []

    def track_connection(*args, **kwargs):
        result = original_connect(*args, **kwargs)
        opened.append(result)
        return result

    with patch('src.integrations.vaultmind.sqlite3.connect', side_effect=track_connection):
        result = fetch_vaultmind_logs(db_path=database)
    assert len(result) == (1 if schema == 'valid' else 0)
    assert len(opened) == 1
    try:
        with pytest.raises(sqlite3.ProgrammingError, match='closed'):
            opened[0].execute('SELECT 1')
    finally:
        opened[0].close()
