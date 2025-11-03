"""
LLM configuration and integration.
Uses Qwen3-VL for multimodal capabilities.
"""
import os
from typing import Any, Dict, List, Optional
import httpx
import json


class QwenVLClient:
    """
    Client for Qwen3-VL multimodal model.
    Supports both text and image inputs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen-vl-plus"
    ):
        """
        Initialize Qwen VL client.

        Args:
            api_key: API key for Qwen (defaults to QWEN_API_KEY env var)
            base_url: Base URL for API (defaults to QWEN_BASE_URL env var)
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("QWEN_API_KEY")
        self.base_url = base_url or os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        self.model = model

        if not self.api_key:
            raise ValueError("QWEN_API_KEY must be set")

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate response from Qwen VL model.

        Args:
            messages: Conversation messages
            system: System prompt
            tools: Available tools for function calling
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Model response
        """
        # Prepare request
        request_messages = []

        # Add system message if provided
        if system:
            request_messages.append({
                "role": "system",
                "content": system
            })

        # Add conversation messages
        request_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": request_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/services/aigc/multimodal-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"input": payload},
                timeout=60.0
            )

            response.raise_for_status()
            result = response.json()

            return self._parse_response(result)

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Qwen API response.

        Args:
            response: Raw API response

        Returns:
            Parsed response
        """
        output = response.get("output", {})
        choices = output.get("choices", [])

        if not choices:
            return {
                "content": "",
                "tool_calls": [],
                "finish_reason": "error"
            }

        choice = choices[0]
        message = choice.get("message", {})

        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
            "finish_reason": choice.get("finish_reason", "stop"),
            "usage": output.get("usage", {})
        }


class OpenRouterClient:
    """
    Client for OpenRouter API (alternative LLM provider).
    Can be used as fallback or for specific tasks.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "google/gemini-2.0-flash-exp:free"
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: API key for OpenRouter
            model: Model name to use
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = model

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY must be set")

    async def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate response from OpenRouter model.

        Args:
            messages: Conversation messages
            system: System prompt
            tools: Available tools
            max_tokens: Maximum tokens
            temperature: Temperature

        Returns:
            Model response
        """
        request_messages = []

        if system:
            request_messages.append({
                "role": "system",
                "content": system
            })

        request_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": request_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60.0
            )

            response.raise_for_status()
            result = response.json()

            return self._parse_response(result)

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenRouter API response"""
        choices = response.get("choices", [])

        if not choices:
            return {
                "content": "",
                "tool_calls": [],
                "finish_reason": "error"
            }

        choice = choices[0]
        message = choice.get("message", {})

        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
            "finish_reason": choice.get("finish_reason", "stop"),
            "usage": response.get("usage", {})
        }


# Default model instances
models = {
    "qwen_vl": None,  # Lazy initialized
    "openrouter": None,  # Lazy initialized
}


def get_qwen_client() -> QwenVLClient:
    """Get or create Qwen VL client"""
    if models["qwen_vl"] is None:
        models["qwen_vl"] = QwenVLClient()
    return models["qwen_vl"]


def get_openrouter_client() -> OpenRouterClient:
    """Get or create OpenRouter client"""
    if models["openrouter"] is None:
        models["openrouter"] = OpenRouterClient()
    return models["openrouter"]
