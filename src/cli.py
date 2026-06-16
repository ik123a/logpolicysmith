import click
import yaml
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .ingester.jsonl_reader import read_vaultmind_logs
from .ingester.normalizer import normalize_event
from .summarizer.behavior_analyzer import BehaviorAnalyzer
from .generator.policy_writer import PolicyWriter
from .integrations.vaultmind import fetch_vaultmind_logs

console = Console()

def load_config():
    config_path = Path(__file__).resolve().parent.parent / "config" / "default.yaml"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

@click.group()
def cli():
    """LogPolicySmith — Generate policies from AI agent behavior logs."""
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), help='Path to JSONL log file')
@click.option('--vaultmind', '-v', is_flag=True, help='Fetch from VaultMind')
@click.option('--days', '-d', default=7, help='Days of logs to analyze')
@click.option('--format', '-f', default=None, type=click.Choice(['rego', 'cel', 'yaml', 'vaultmind']), help='Output format: rego, cel, yaml, vaultmind')
@click.option('--model', '-m', default=None, help='LLM model name')
@click.option('--host', '-h', default=None, help='LLM API endpoint/host URL')
@click.option('--provider', '-p', default=None, type=click.Choice(['ollama', 'nvidia', 'openai']), help='LLM provider')
@click.option('--api-key', '-k', default=None, help='Cloud provider API key')
@click.option('--db-path', default=None, type=click.Path(exists=True), help='Override filepath for VaultMind SQLite database')
@click.option('--mock', is_flag=True, help='Run in mock mode without calling LLM')
def generate(input, vaultmind, days, format, model, host, provider, api_key, db_path, mock):
    """Generate policy from agent behavior logs."""
    config = load_config()
    
    # Resolve default values from config if not provided in CLI
    llm_config = config.get("llm", {})
    policy_config = config.get("policy", {})
    
    selected_provider = provider or llm_config.get("provider", "ollama")
    selected_format = format or policy_config.get("default_format", "rego")
    
    if selected_provider == "nvidia":
        selected_model = model or llm_config.get("nvidia_model", "meta/llama-3.1-70b-instruct")
        selected_host = host or llm_config.get("nvidia_base_url", "https://integrate.api.nvidia.com/v1")
    elif selected_provider == "openai":
        selected_model = model or llm_config.get("openai_model", "gpt-4o")
        selected_host = host or llm_config.get("openai_base_url", "https://api.openai.com/v1")
    else:
        selected_model = model or llm_config.get("model", "llama3.2:3b")
        selected_host = host or llm_config.get("ollama_host", "http://localhost:11434")
    
    # Ingest raw logs
    raw_logs = []
    if vaultmind:
        sqlite_path = Path(db_path) if db_path else None
        raw_logs = fetch_vaultmind_logs(days, db_path=sqlite_path)
        console.print(f"[green][OK][/green] Fetched [bold]{len(raw_logs)}[/bold] events from VaultMind SQLite database.")
    elif input:
        try:
            raw_logs = list(read_vaultmind_logs(input))
            console.print(f"[green][OK][/green] Loaded [bold]{len(raw_logs)}[/bold] events from {input}.")
        except Exception as e:
            console.print(f"[red]Error reading logs:[/red] {e}")
            return
    else:
        console.print("[red]Error:[/red] Please provide either --input or --vaultmind flag.")
        return

    if not raw_logs:
        console.print("[yellow]No logs found or fetched to analyze.[/yellow]")
        return
        
    # Normalize logs
    events = [normalize_event(raw) for raw in raw_logs]
    
    # Step 1: Summarize behavior (Pass 1)
    if mock:
        console.print("[yellow][MOCK][/yellow] Simulating behavior summarization...")
        summary = (
            "- **Frequent Actions**: Read files (2 occurrences), write files (1 occurrence)\n"
            "- **Typical Workflow**: Reads from '/data/approved/' and writes to '/data/output/'\n"
            "- **Data Access Patterns**: Accessed '/data/approved/sensitive.csv'\n"
            "- **Risk Indicators**: Attempted executing terminal commands\n"
            "- **Anomalies**: Execution of terminal_runner detected and blocked"
        )
        console.print("[green][OK][/green] Behavior summary successfully generated (mock).")
    else:
        console.print(f"[bold]Pass 1[/bold]: Summarizing behavior patterns using provider '{selected_provider}' and model '{selected_model}'...")
        try:
            analyzer = BehaviorAnalyzer(provider=selected_provider, model=selected_model, host=selected_host, api_key=api_key)
            summary = analyzer.summarize(events)
            console.print("[green][OK][/green] Behavior summary successfully generated.")
        except Exception as e:
            console.print(f"[red]Error generating behavior summary:[/red] {e}")
            return
        
    # Step 2: Generate policy (Pass 2)
    if mock:
        console.print("[yellow][MOCK][/yellow] Synthesizing security policy...")
        from .output.rego_formatter import format_rego
        from .output.cel_formatter import format_cel
        from .output.yaml_formatter import format_yaml, format_vaultmind_yaml
        
        mock_policy_data = {
            "package": "agent.policy",
            "allows": [
                {"action": "read", "tool": "file_reader", "path_prefix": "/data/approved/"},
                {"action": "write", "tool": "file_writer", "path_prefix": "/data/output/"}
            ],
            "denies": [
                {"action": "exec", "tool": "terminal_runner"}
            ]
        }
        
        if selected_format == "rego":
            policy = format_rego(mock_policy_data)
        elif selected_format == "cel":
            policy = format_cel(mock_policy_data)
        elif selected_format == "vaultmind":
            policy = format_vaultmind_yaml(mock_policy_data)
        else:
            policy = format_yaml(mock_policy_data)
        console.print("[green][OK][/green] Policy successfully generated (mock).")
    else:
        console.print(f"[bold]Pass 2[/bold]: Synthesizing security policy in format '{selected_format}'...")
        try:
            writer = PolicyWriter(provider=selected_provider, model=selected_model, output_format=selected_format, host=selected_host, api_key=api_key)
            policy = writer.generate(summary)
            console.print("[green][OK][/green] Policy successfully generated.")
        except Exception as e:
            console.print(f"[red]Error generating policy:[/red] {e}")
            return
        
    # Output the result
    console.print("\n" + "="*50)
    console.print(Panel(policy, title=f"Generated {selected_format.upper()} Policy", expand=False))
    console.print("="*50)

if __name__ == "__main__":
    cli()
