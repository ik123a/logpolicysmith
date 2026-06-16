# LogPolicySmith

*From Agent Behavior to Enforceable Policy — Automatically.*

LogPolicySmith is an offline-first tool designed to ingest AI agent execution logs (from VaultMind or generic JSONL logs) and generate security policies as code (such as OPA Rego) using local LLMs.

## Features
- **Offline First**: Uses local Ollama LLMs (e.g., `llama3.2:3b`) for policy synthesis.
- **Log Ingestion**: Normalizes diverse log schemas into a standard internal event schema.
- **2-Pass Architecture**:
  1. Aggregates logs and summarizes behavior patterns/anomalies.
  2. Compiles security policy rules from the behavior summary.
- **Extensible Formats**: Generate OPA Rego, CEL, or YAML configurations.
- **VaultMind Integration**: Directly fetch audit trails from VaultMind SQLite database.

## Installation
From source:
```bash
git clone https://github.com/ik123a/logpolicysmith.git
cd logpolicysmith
pip install -e .
```

## CLI Usage
```bash
# Generate policy from a JSONL log file
logpolicysmith generate --input logs.jsonl --format rego

# Fetch and generate policy from VaultMind
logpolicysmith generate --vaultmind --days 7 --format rego
```
