import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PolicyWriter:
    def __init__(self, provider: str = "ollama", model: str = None, output_format: str = "rego", host: str = None, api_key: str = None):
        self.provider = provider
        self.model = model
        self.output_format = output_format
        self.host = host
        self.api_key = api_key
        self.prompt_template = self._load_prompt("generation.txt")

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
        return "Based on this summary, write a security policy in {format} format:\n\n{summary}"

    def generate(self, behavior_summary: str) -> str:
        """Pass 2: Generate policy-as-code from behavior summary using Ollama or NVIDIA."""
        prompt = self.prompt_template.format(
            summary=behavior_summary,
            format=self.output_format
        )
        
        if self.provider == "nvidia":
            from openai import OpenAI
            key = self.api_key or os.environ.get("NVIDIA_API_KEY")
            if not key:
                raise ValueError("NVIDIA API key not set. Please set the NVIDIA_API_KEY environment variable or pass --api-key.")
            
            nvidia_model = self.model or "meta/llama-3.1-70b-instruct"
            base_url = self.host or "https://integrate.api.nvidia.com/v1"
            
            logger.info(f"Invoking NVIDIA model {nvidia_model} for policy generation in format '{self.output_format}'...")
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
                logger.error(f"Error during NVIDIA policy generation: {e}")
                raise
        elif self.provider == "openai":
            from openai import OpenAI
            key = self.api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ValueError("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable or pass --api-key.")
            
            openai_model = self.model or "gpt-4o"
            base_url = self.host or "https://api.openai.com/v1"
            
            logger.info(f"Invoking OpenAI-compatible model {openai_model} for policy generation in format '{self.output_format}'...")
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
                logger.error(f"Error during OpenAI policy generation: {e}")
                raise
        else:
            # Default to Ollama
            import ollama
            ollama_model = self.model or "llama3.2:3b"
            client = ollama.Client(host=self.host) if self.host else ollama
            try:
                logger.info(f"Invoking Ollama model {ollama_model} for policy generation in format '{self.output_format}'...")
                response = client.chat(
                    model=ollama_model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response['message']['content']
            except Exception as e:
                logger.error(f"Error during Ollama policy generation: {e}")
                raise
