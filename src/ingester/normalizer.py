from typing import Dict, Any
from pydantic import BaseModel, Field

class NormalizedEvent(BaseModel):
    agent_id: str = Field(default="unknown")
    timestamp: str = Field(default="")
    action_type: str = Field(default="unknown")  # e.g., read, write, exec, network
    tool_name: str = Field(default="unknown")
    resource: str = Field(default="")
    outcome: str = Field(default="unknown")        # e.g., allow, deny, error
    metadata: Dict[str, Any] = Field(default_factory=dict)

def normalize_event(raw: Dict[str, Any]) -> NormalizedEvent:
    """Normalize raw log fields from VaultMind or general format into standard NormalizedEvent schema."""
    agent_id = raw.get('agent_id') or raw.get('agent') or 'unknown'
    timestamp = raw.get('timestamp') or raw.get('time') or ''
    
    # Action type mappings
    action_type = raw.get('action') or raw.get('action_type') or 'unknown'
    
    # Tool name mappings
    tool_name = raw.get('tool') or raw.get('tool_name') or 'unknown'
    
    # Resource mappings
    resource = raw.get('path') or raw.get('resource') or raw.get('url') or ''
    
    # Outcome/decision mapping
    outcome = raw.get('decision') or raw.get('outcome') or raw.get('status') or 'unknown'
    
    return NormalizedEvent(
        agent_id=str(agent_id),
        timestamp=str(timestamp),
        action_type=str(action_type),
        tool_name=str(tool_name),
        resource=str(resource),
        outcome=str(outcome),
        metadata=raw
    )
