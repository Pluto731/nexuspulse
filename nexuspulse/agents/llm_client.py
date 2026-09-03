"""OpenAI/DeepSeek-compatible LLM client with intelligent fallback simulation."""

import json
import logging
from typing import Dict, Any, Optional
import httpx

from nexuspulse.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for querying OpenAI/DeepSeek compatible endpoints with fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.model = model or settings.llm_model

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid API key is present."""
        return bool(self.api_key and not self.api_key.startswith("your_"))

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        mock_fallback_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call LLM and parse output as JSON. Falls back to mock if not configured."""
        if not self.is_configured:
            if mock_fallback_data is not None:
                return mock_fallback_data
            return {"error": "LLM not configured and no mock provided"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system_prompt}\nYou MUST respond with valid raw JSON only."},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": settings.temperature,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"]
                return json.loads(raw_text)
        except Exception as e:
            logger.warning(f"LLM API request failed ({e}), using fallback simulation.")
            if mock_fallback_data is not None:
                return mock_fallback_data
            raise e
