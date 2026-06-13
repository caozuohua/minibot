"""Google Gemini model provider."""

import logging

import google.generativeai as genai

from src.models.base_provider import ModelProvider

logger = logging.getLogger(__name__)


class GeminiProvider(ModelProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def name(self) -> str:
        return "gemini"

    def chat(self, messages: list, model: str | None = None) -> str:
        """Send chat completion request."""
        logger.debug(f"[Gemini] chat request, model={model}")

        gemini_model = genai.GenerativeModel(model)

        # Separate system message from conversation
        system_instruction = None
        conversation = []
        for msg in messages:
            if msg.get("role") == "system":
                system_instruction = msg.get("content", "")
            else:
                conversation.append(msg)

        # Build Gemini contents
        contents = []
        for msg in conversation:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(
                {
                    "role": role,
                    "parts": [msg.get("content", "")],
                }
            )

        config = {
            "temperature": 0.7,
        }
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = gemini_model.generate_content(
            contents=contents,
            generation_config=genai.types.GenerationConfig(
                **{k: v for k, v in config.items() if k != "system_instruction"}
            ),
        )

        content = response.text
        logger.debug(f"[Gemini] chat response length: {len(content)} chars")
        return content or ""

    def embed(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding vector."""
        logger.debug(f"[Gemini] embed request, model={model}")
        embedding = genai.embed_content(model=model, content=text)
        values = embedding["values"]
        logger.debug(f"[Gemini] embed dimension: {len(values)}")
        return values
