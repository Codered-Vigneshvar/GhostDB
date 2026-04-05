"""
Unified LLM Client

Centralizes all LLM calls into one module. Uses OpenAI-compatible API if available,
and falls back to Groq if not.
"""
import os
from typing import Optional

class LLMClient:
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        self.api_base_url = os.environ.get("API_BASE_URL")
        self.model_name = os.environ.get("MODEL_NAME")
        
        # User requested fallback using HF_TOKEN, but traditionally Groq uses GROQ_API_KEY.
        # We will check HF_TOKEN first to align with exact instructions, then fallback if needed.
        self.token = os.environ.get("HF_TOKEN") or os.environ.get("GROQ_API_KEY")
        
        if not self.token:
            raise ValueError("No valid LLM configuration found: Missing HF_TOKEN / API key.")
        if not self.model_name:
            raise ValueError("No valid LLM configuration found: Missing MODEL_NAME.")

        if self.api_base_url:
            print("[LLM] Using OpenAI-compatible endpoint")
            try:
                from openai import OpenAI
                self.client = OpenAI(base_url=self.api_base_url, api_key=self.token)
                self.mode = "openai"
            except ImportError:
                raise ImportError("openai package is not installed. Run `pip install openai`.")
        else:
            print("[LLM] Using Groq fallback")
            try:
                from groq import Groq
                self.client = Groq(api_key=self.token)
                self.mode = "groq"
            except ImportError:
                raise ImportError("groq package is not installed. Run `pip install groq`.")

    def generate(self, prompt: str) -> str:
        """
        Sends a simple system prompt and returns the text response.
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
