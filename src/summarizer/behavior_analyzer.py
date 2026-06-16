import os
import logging
from pathlib import Path
from typing import List
from ..ingester.normalizer import NormalizedEvent

logger = logging.getLogger(__name__)

class BehaviorAnalyzer:
    def __init__(self, provider: str = "ollama", model: str = None, host: str = None, api_key: str = None):
        self.provider = provider
        self.model = model
        self.host = host
        self.api_key = api_key
        self.prompt_template = self._load_prompt("summarization.txt")

    def _load_prompt(self, filename: str) -> str:
        # Resolve prompt path relative to source file
        possible_paths = [
            Path(__file__).resolve().parent.parent.parent / "config" / "prompts" / filename,
            Path("config/prompts") / filename,
            Path.home() / ".config" / "logpolicysmith" / "prompts" / filename
        ]
        for path in possible_paths:
            if path.exists():
                try:
                    return path.read_text(encoding="utf-8")
                except Exception as e:
                    logger.warning(f"Failed to read prompt from {path}: {e}")
        
        # Hardcoded fallback if templates are missing
        logger.warning(f"Prompt template {filename} not found. Using default internal prompt.")
        return "Analyze the following agent behaviors:\n\n{context}"

    def summarize(self, events: List[NormalizedEvent]) -> str:
        """Pass 1: Summarize behavior patterns from logs using Ollama or NVIDIA."""
        context = self._prepare_context(events)
        prompt = self.prompt_template.format(context=context)
        
        if self.provider == "nvidia":
            from openai import OpenAI
            key = self.api_key or os.environ.get("NVIDIA_API_KEY")
            if not key:
                raise ValueError("NVIDIA API key not set. Please set the NVIDIA_API_KEY environment variable or pass --api-key.")
            
            nvidia_model = self.model or "meta/llama-3.1-70b-instruct"
            base_url = self.host or "https://integrate.api.nvidia.com/v1"
            
            logger.info(f"Invoking NVIDIA model {nvidia_model} for behavior summarization...")
            client = OpenAI(base_url=base_url, api_key=key)
            try:
                response = client.chat.completions.create(
                    model=nvidia_model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error during NVIDIA behavior summarization: {e}")
                raise
        elif self.provider == "openai":
            from openai import OpenAI
            key = self.api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ValueError("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable or pass --api-key.")
            
            openai_model = self.model or "gpt-4o"
            base_url = self.host or "https://api.openai.com/v1"
            
            logger.info(f"Invoking OpenAI-compatible model {openai_model} for behavior summarization...")
            client = OpenAI(base_url=base_url, api_key=key)
            try:
                response = client.chat.completions.create(
                    model=openai_model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error during OpenAI behavior summarization: {e}")
                raise
        else:
            # Default to Ollama
            import ollama
            ollama_model = self.model or "llama3.2:3b"
            client = ollama.Client(host=self.host) if self.host else ollama
            try:
                logger.info(f"Invoking Ollama model {ollama_model} for behavior summarization...")
                response = client.chat(
                    model=ollama_model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response['message']['content']
            except Exception as e:
                logger.error(f"Error during Ollama behavior summarization: {e}")
                raise

    def _prepare_context(self, events: List[NormalizedEvent]) -> str:
        """Aggregate events into a compact summary for the LLM."""
        if not events:
            return "No event logs provided."
            
        action_counts = {}
        tool_counts = {}
        resources = set()
        outcomes = {}
        
        for e in events:
            action_counts[e.action_type] = action_counts.get(e.action_type, 0) + 1
            tool_counts[e.tool_name] = tool_counts.get(e.tool_name, 0) + 1
            if e.resource:
                resources.add(e.resource)
            outcomes[e.outcome] = outcomes.get(e.outcome, 0) + 1
        
        return f"""
Total Events: {len(events)}
Action Distribution: {action_counts}
Tool Usage: {tool_counts}
Outcome Distribution: {outcomes}
Resources Accessed (up to 20): {list(resources)[:20]}
Sample Events (first 5): {[e.model_dump() for e in events[:5]]}
"""
