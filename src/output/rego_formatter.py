from typing import Dict, Any, List

def format_rego(policy_data: Dict[str, Any]) -> str:
    """Format structured policy rules as OPA Rego.
    
    Expects format:
    {
        "package": "agent.policy",
        "allows": [{"action": "read", "tool": "file_reader", "path_prefix": "/data/approved/"}],
        "denies": [{"action": "exec"}]
    }
    """
    pkg = policy_data.get("package", "agent.policy")
    rego_lines = [
        f"package {pkg}",
        "",
        "# Default deny",
        "default allow = false",
        ""
    ]
    
    allows = policy_data.get("allows", [])
    for idx, rule in enumerate(allows):
        rego_lines.append("# Allow rule derived from observed behavior")
        rego_lines.append("allow {")
        if "action" in rule:
            rego_lines.append(f'    input.action == "{rule["action"]}"')
        if "tool" in rule:
            rego_lines.append(f'    input.tool == "{rule["tool"]}"')
        if "path_prefix" in rule:
            rego_lines.append(f'    startswith(input.path, "{rule["path_prefix"]}")')
        rego_lines.append("}")
        rego_lines.append("")
        
    denies = policy_data.get("denies", [])
    for idx, rule in enumerate(denies):
        rego_lines.append("# Deny rule for risky actions")
        rego_lines.append("deny {")
        if "action" in rule:
            rego_lines.append(f'    input.action == "{rule["action"]}"')
        if "tool" in rule:
            rego_lines.append(f'    input.tool == "{rule["tool"]}"')
        rego_lines.append("}")
        rego_lines.append("")

    return "\n".join(rego_lines)
