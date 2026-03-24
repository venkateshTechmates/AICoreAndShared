"""
LLM Provider Abstraction — Unified interface for 8+ LLM providers.

Supports: OpenAI, Anthropic, Azure, Bedrock, Vertex AI, Groq, Ollama, Together
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from ai_core.schemas import LLMConfig, LLMProvider, LLMResponse, TokenUsage


class BaseLLM(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        ...

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        ...
        yield ""  # pragma: no cover

    async def generate_structured(
        self,
        prompt: str,
        output_schema: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a structured response conforming to *output_schema*."""
        import json

        schema_instruction = (
            f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(output_schema, indent=2)}"
        )
        resp = await self.generate(f"{schema_instruction}\n\n{prompt}", **kwargs)
        return json.loads(resp.text)


# ── Provider Implementations ─────────────────────────────────────────────────


class OpenAILLM(BaseLLM):
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        import openai  # type: ignore[import-untyped]

        self._client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        start = time.perf_counter()
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            top_p=kwargs.get("top_p", self.config.top_p),
        )
        elapsed = (time.perf_counter() - start) * 1000
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            text=choice.message.content or "",
            usage=TokenUsage(
                input=usage.prompt_tokens if usage else 0,
                output=usage.completion_tokens if usage else 0,
                total=usage.total_tokens if usage else 0,
            ),
            latency_ms=elapsed,
            model=resp.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


class AnthropicLLM(BaseLLM):
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        import anthropic  # type: ignore[import-untyped]

        self._client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        start = time.perf_counter()
        resp = await self._client.messages.create(
            model=self.config.model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
        )
        elapsed = (time.perf_counter() - start) * 1000
        text = resp.content[0].text if resp.content else ""
        return LLMResponse(
            text=text,
            usage=TokenUsage(
                input=resp.usage.input_tokens,
                output=resp.usage.output_tokens,
                total=resp.usage.input_tokens + resp.usage.output_tokens,
            ),
            latency_ms=elapsed,
            model=resp.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        ) as stream:
            async for text in stream.text_stream:
                yield text


class AzureOpenAILLM(BaseLLM):
    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        import openai  # type: ignore[import-untyped]

        self._client = openai.AsyncAzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.base_url or "",
            api_version="2024-06-01",
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        start = time.perf_counter()
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        elapsed = (time.perf_counter() - start) * 1000
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            text=choice.message.content or "",
            usage=TokenUsage(
                input=usage.prompt_tokens if usage else 0,
                output=usage.completion_tokens if usage else 0,
                total=usage.total_tokens if usage else 0,
            ),
            latency_ms=elapsed,
            model=resp.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


class GroqLLM(BaseLLM):
    """Groq uses the OpenAI-compatible API."""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        import openai  # type: ignore[import-untyped]

        self._client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://api.groq.com/openai/v1",
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        start = time.perf_counter()
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        elapsed = (time.perf_counter() - start) * 1000
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            text=choice.message.content or "",
            usage=TokenUsage(
                input=usage.prompt_tokens if usage else 0,
                output=usage.completion_tokens if usage else 0,
                total=usage.total_tokens if usage else 0,
            ),
            latency_ms=elapsed,
            model=resp.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            temperature=self.config.temperature,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


class OllamaLLM(BaseLLM):
    """Ollama local inference via its HTTP API."""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._base_url = config.base_url or "http://localhost:11434"

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        import httpx

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            resp = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self.config.model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
        elapsed = (time.perf_counter() - start) * 1000
        return LLMResponse(
            text=data.get("response", ""),
            usage=TokenUsage(
                input=data.get("prompt_eval_count", 0),
                output=data.get("eval_count", 0),
                total=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            ),
            latency_ms=elapsed,
            model=self.config.model,
        )

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        import httpx

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={"model": self.config.model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
        elapsed = (time.perf_counter() - start) * 1000
        return LLMResponse(
            text=data.get("message", {}).get("content", ""),
            latency_ms=elapsed,
            model=self.config.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        import httpx

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={"model": self.config.model, "prompt": prompt, "stream": True},
            ) as resp:
                import json

                async for line in resp.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        if token := chunk.get("response"):
                            yield token


class TogetherLLM(BaseLLM):
    """Together AI — OpenAI-compatible endpoint."""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        import openai  # type: ignore[import-untyped]

        self._client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or "https://api.together.xyz/v1",
            timeout=config.timeout,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        start = time.perf_counter()
        resp = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        elapsed = (time.perf_counter() - start) * 1000
        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            text=choice.message.content or "",
            usage=TokenUsage(
                input=usage.prompt_tokens if usage else 0,
                output=usage.completion_tokens if usage else 0,
                total=usage.total_tokens if usage else 0,
            ),
            latency_ms=elapsed,
            model=resp.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


class BedrockLLM(BaseLLM):
    """AWS Bedrock — supports Anthropic Claude, Meta Llama, Mistral on AWS."""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        import boto3  # type: ignore[import-untyped]

        session_kwargs: dict[str, Any] = {}
        if config.api_key:
            session_kwargs["aws_access_key_id"] = config.api_key
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=config.base_url or "us-east-1",
            **session_kwargs,
        )

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        import asyncio
        import json

        start = time.perf_counter()
        body = json.dumps(
            {
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "anthropic_version": "bedrock-2023-05-31",
            }
        )
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.invoke_model(
                modelId=self.config.model,
                body=body,
                contentType="application/json",
            ),
        )
        elapsed = (time.perf_counter() - start) * 1000
        result = json.loads(resp["body"].read())
        text = ""
        if "content" in result and result["content"]:
            text = result["content"][0].get("text", "")
        usage = result.get("usage", {})
        return LLMResponse(
            text=text,
            usage=TokenUsage(
                input=usage.get("input_tokens", 0),
                output=usage.get("output_tokens", 0),
                total=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            ),
            latency_ms=elapsed,
            model=self.config.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        import asyncio
        import json

        body = json.dumps(
            {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "anthropic_version": "bedrock-2023-05-31",
            }
        )
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._client.invoke_model_with_response_stream(
                modelId=self.config.model,
                body=body,
                contentType="application/json",
            ),
        )
        stream = resp.get("body")
        if stream:
            for event in stream:
                chunk = json.loads(event["chunk"]["bytes"])
                if chunk.get("type") == "content_block_delta":
                    delta_text = chunk.get("delta", {}).get("text", "")
                    if delta_text:
                        yield delta_text


class VertexAILLM(BaseLLM):
    """Google Vertex AI / GenAI — supports Gemini models."""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self._project = config.base_url or "default-project"

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return await self.chat([{"role": "user", "content": prompt}], **kwargs)

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        import asyncio

        start = time.perf_counter()

        def _invoke() -> dict[str, Any]:
            import google.generativeai as genai  # type: ignore[import-untyped]

            genai.configure(api_key=self.config.api_key)
            model = genai.GenerativeModel(self.config.model)
            # Convert messages to Gemini format
            parts = [m["content"] for m in messages]
            response = model.generate_content(
                "\n".join(parts),
                generation_config=genai.GenerationConfig(
                    temperature=kwargs.get("temperature", self.config.temperature),
                    max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                ),
            )
            usage_meta = getattr(response, "usage_metadata", None)
            return {
                "text": response.text if response.text else "",
                "input_tokens": getattr(usage_meta, "prompt_token_count", 0) if usage_meta else 0,
                "output_tokens": getattr(usage_meta, "candidates_token_count", 0) if usage_meta else 0,
            }

        result = await asyncio.get_event_loop().run_in_executor(None, _invoke)
        elapsed = (time.perf_counter() - start) * 1000
        return LLMResponse(
            text=result["text"],
            usage=TokenUsage(
                input=result["input_tokens"],
                output=result["output_tokens"],
                total=result["input_tokens"] + result["output_tokens"],
            ),
            latency_ms=elapsed,
            model=self.config.model,
        )

    async def stream(self, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        import asyncio

        def _stream_invoke() -> list[str]:
            import google.generativeai as genai  # type: ignore[import-untyped]

            genai.configure(api_key=self.config.api_key)
            model = genai.GenerativeModel(self.config.model)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=kwargs.get("temperature", self.config.temperature),
                    max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                ),
                stream=True,
            )
            chunks: list[str] = []
            for chunk in response:
                if chunk.text:
                    chunks.append(chunk.text)
            return chunks

        chunks = await asyncio.get_event_loop().run_in_executor(None, _stream_invoke)
        for chunk in chunks:
            yield chunk


# ── Factory ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[LLMProvider, type[BaseLLM]] = {
    LLMProvider.OPENAI: OpenAILLM,
    LLMProvider.ANTHROPIC: AnthropicLLM,
    LLMProvider.AZURE: AzureOpenAILLM,
    LLMProvider.GROQ: GroqLLM,
    LLMProvider.OLLAMA: OllamaLLM,
    LLMProvider.TOGETHER: TogetherLLM,
    LLMProvider.BEDROCK: BedrockLLM,
    LLMProvider.VERTEX_AI: VertexAILLM,
}


class LLMFactory:
    """Create LLM instances by provider name."""

    @staticmethod
    def create(
        provider: str | LLMProvider,
        model: str,
        config: LLMConfig | None = None,
    ) -> BaseLLM:
        prov = LLMProvider(provider)
        if config is None:
            config = LLMConfig(provider=prov, model=model)
        else:
            config = config.model_copy(update={"provider": prov, "model": model})
        cls = _REGISTRY.get(prov)
        if cls is None:
            raise ValueError(f"Unsupported LLM provider: {prov}")
        return cls(config)

    @staticmethod
    def register(provider: LLMProvider, cls: type[BaseLLM]) -> None:
        _REGISTRY[provider] = cls
