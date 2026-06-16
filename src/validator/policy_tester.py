import subprocess
import tempfile
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def validate_rego(policy: str) -> bool:
    """Validate Rego policy using OPA check."""
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, "temp_policy.rego")
    
    try:
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write(policy)
            
        # Run OPA check command
        result = subprocess.run(
            ['opa', 'check', temp_file_path],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            return True
        else:
            logger.warning(f"Rego validation failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.warning("OPA CLI ('opa') not found in PATH. Skipping local validation.")
        return False
    except Exception as e:
        logger.error(f"Error validating policy: {e}")
        return False
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

def test_policy_against_logs(policy: str, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Test policy against historical logs."""
    results = {
        "total": len(logs),
        "allowed": 0,
        "denied": 0,
        "errors": 0
    }
    
    # Basic keyword/pattern simulation for demonstration/fallback
    for log in logs:
        action = log.get("action") or log.get("action_type") or "unknown"
        
        # Simple simulated decision
        if action == "exec" and "deny" in policy.lower():
            results["denied"] += 1
        elif action in ["read", "write"] and action in policy.lower():
            results["allowed"] += 1
        else:
            results["denied"] += 1
            
    return results
