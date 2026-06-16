import yaml
from typing import Dict, Any

def format_yaml(policy_data: Dict[str, Any]) -> str:
    """Format structured policy rules as standard YAML configuration."""
    return yaml.safe_dump(policy_data, default_flow_style=False, sort_keys=False)

def format_vaultmind_yaml(policy_data: Dict[str, Any]) -> str:
    """Format structured policy rules as native VaultMind policy.yaml."""
    rules = []
    
    # Process allows
    allows = policy_data.get("allows", [])
    allow_patterns = []
    for rule in allows:
        action = rule.get("action") or "read"
        path = rule.get("path_prefix") or rule.get("resource") or "*"
        
        if path == "*":
            pattern = f"{action}(*)"
        else:
            if not path.endswith("*"):
                suffix = "*" if path.endswith("/") else "/*"
                pattern = f"{action}({path}{suffix})"
            else:
                pattern = f"{action}({path})"
        allow_patterns.append(pattern)
        
    if allow_patterns:
        rules.append({
            "id": "generated-allow-rules",
            "allow": allow_patterns
        })
        
    # Process denies
    denies = policy_data.get("denies", [])
    deny_patterns = []
    for rule in denies:
        action = rule.get("action") or "exec"
        path = rule.get("path_prefix") or rule.get("resource") or rule.get("tool") or "*"
        
        if path == "*":
            pattern = f"{action}(*)"
        else:
            if not path.endswith("*"):
                suffix = "*" if path.endswith("/") else "/*"
                pattern = f"{action}({path}{suffix})"
            else:
                pattern = f"{action}({path})"
        deny_patterns.append(pattern)
        
    if deny_patterns:
        rules.append({
            "id": "generated-deny-rules",
            "deny": deny_patterns
        })
        
    # Build complete VaultMind structure
    vaultmind_policy = {
        "version": "1.0",
        "rules": rules,
        "default_action": "deny"
    }
    
    return yaml.safe_dump(vaultmind_policy, default_flow_style=False, sort_keys=False)

