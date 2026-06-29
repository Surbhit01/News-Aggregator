"""
LLM abstraction layer supporting multiple providers.
Uses OpenAI-compatible SDK for broad provider support
(OpenAI, Ollama, Kimi, Anthropic, local models, etc.)
"""
import logging
from typing import Optional
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """LLM provider wrapper using OpenAI-compatible API."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = base_url or settings.LLM_BASE_URL

        if not self.api_key:
            logger.warning("No LLM API key configured — using fallback mode")

        self.client = AsyncOpenAI(
            api_key=self.api_key or "sk-fallback",
            base_url=self.base_url,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 300,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using the LLM."""
        # Skip API call if no API key configured or LLM is disabled
        if not settings.LLM_ENABLED:
            logger.info("LLM call SKIPPED — LLM_ENABLED=false")
            return f"[LLM unavailable: disabled]"
        if not settings.LLM_API_KEY and not self.api_key:
            logger.info(f"LLM call SKIPPED — no API key. Model={self.model}, Base={self.base_url or 'default'}")
            return f"[LLM unavailable: no API key configured]"

        logger.info(f"LLM call: model={self.model}, tokens={max_tokens}, temp={temperature}")
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"[LLM unavailable: {e}]"

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
    ) -> str:
        """Generate structured text (JSON, bullet points) with lower temperature."""
        return await self.generate(
            prompt=prompt,
            system_prompt=(system_prompt or "Respond with concise, structured output."),
            max_tokens=max_tokens,
            temperature=0.3,
        )


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMProvider:
    """Factory to get the appropriate LLM provider.

    Uses OpenAI-compatible SDK for all providers.
    Configure via .env:
    - LLM_PROVIDER: openai (default), ollama, kimi, etc.
    - LLM_API_KEY: your API key
    - LLM_MODEL: model name (gpt-4o-mini, deepseek-chat, etc.)
    - LLM_BASE_URL: custom base URL for non-OpenAI providers

    Provider presets:
    - OpenAI:     LLM_BASE_URL not set (default)
    - Ollama:     LLM_BASE_URL=http://localhost:11434/v1
    - Kimi:       LLM_BASE_URL=https://api.moonshot.cn/v1
    - DeepSeek:   LLM_BASE_URL=https://api.deepseek.com/v1
    """
    _ = provider or settings.LLM_PROVIDER  # For future provider-specific logic
    return LLMProvider(model=model, base_url=base_url)