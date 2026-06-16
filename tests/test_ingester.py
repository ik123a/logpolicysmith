import pytest
from src.ingester.jsonl_reader import read_vaultmind_logs
from src.ingester.normalizer import normalize_event, NormalizedEvent

def test_read_vaultmind_logs(tmp_path):
    log_file = tmp_path / "test.jsonl"
    log_file.write_text('{"action": "read", "tool": "file"}\n')
    
    logs = list(read_vaultmind_logs(str(log_file)))
    assert len(logs) == 1
    assert logs[0]['action'] == 'read'

def test_normalize_event():
    raw_vaultmind_log = {
        "timestamp": "2026-06-16T10:00:00Z",
        "agent_id": "agent-123",
        "action": "read",
        "tool": "file_reader",
        "path": "/data/sensitive.csv",
        "decision": "allow"
    }
    
    normalized = normalize_event(raw_vaultmind_log)
    assert isinstance(normalized, NormalizedEvent)
    assert normalized.agent_id == "agent-123"
    assert normalized.action_type == "read"
    assert normalized.tool_name == "file_reader"
    assert normalized.resource == "/data/sensitive.csv"
    assert normalized.outcome == "allow"
    assert normalized.metadata == raw_vaultmind_log

def test_normalize_event_fallback():
    raw_generic_log = {
        "time": "2026-06-16T10:05:00Z",
        "agent": "agent-456",
        "action_type": "write",
        "tool_name": "db_writer",
        "resource": "users_table",
        "outcome": "deny"
    }
    
    normalized = normalize_event(raw_generic_log)
    assert normalized.agent_id == "agent-456"
    assert normalized.action_type == "write"
    assert normalized.tool_name == "db_writer"
    assert normalized.resource == "users_table"
    assert normalized.outcome == "deny"
