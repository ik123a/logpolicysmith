from typing import Dict, Any

def format_cel(policy_data: Dict[str, Any]) -> str:
    """Format structured policy rules as Google CEL (Common Expression Language)."""
    expressions = []
    
    allows = policy_data.get("allows", [])
    for rule in allows:
        parts = []
        if "action" in rule:
            parts.append(f'action == "{rule["action"]}"')
        if "tool" in rule:
            parts.append(f'tool == "{rule["tool"]}"')
        if "path_prefix" in rule:
            parts.append(f'path.startsWith("{rule["path_prefix"]}")')
        if parts:
            expressions.append(" && ".join(parts))
            
    if not expressions:
        return "false"
        
    return " ||\n".join(f"({expr})" for expr in expressions)
