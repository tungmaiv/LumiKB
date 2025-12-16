"""Model Connection Testing Service.

Tests connectivity to LLM models via LiteLLM proxy for both
embedding and generation model types.

All DB models are registered with the LiteLLM proxy using a db-{uuid}
alias, so connection tests always go through the proxy.
"""

import time
from typing import Any

import structlog
from litellm import acompletion, aembedding

from app.core.config import settings
from app.models.llm_model import LLMModel, ModelType
from app.schemas.llm_model import ConnectionTestResult
from app.services.litellm_proxy_service import build_proxy_model_name
from app.services.model_registry_service import ModelRegistryService

logger = structlog.get_logger(__name__)

# Test prompts for different model types
EMBEDDING_TEST_TEXT = "This is a test sentence for embedding validation."
GENERATION_TEST_PROMPT = [
    {"role": "user", "content": "Say 'test successful' in exactly two words."}
]


def _build_proxy_model_path(model: LLMModel) -> str:
    """Build the model path for LiteLLM proxy.

    Uses the db-{uuid} alias that was registered with the proxy,
    prefixed with "openai/" to use the OpenAI-compatible API endpoints.

    Args:
        model: LLMModel instance.

    Returns:
        Model path for LiteLLM SDK (e.g., "openai/db-abc123").
    """
    proxy_alias = build_proxy_model_name(model)
    return f"openai/{proxy_alias}"


async def test_model_connection(
    model: LLMModel,
    _service: ModelRegistryService,
) -> ConnectionTestResult:
    """Test connection to an LLM model via LiteLLM proxy.

    AC-7.9.8: "Test Connection" button validates model accessibility
    and returns latency/status.

    All models are tested through the LiteLLM proxy using their
    db-{uuid} alias. This ensures consistent behavior regardless
    of the underlying provider.

    Args:
        model: LLMModel to test.
        service: ModelRegistryService (kept for API compatibility).

    Returns:
        ConnectionTestResult with success/failure status.
    """
    try:
        if model.type == ModelType.EMBEDDING.value:
            return await _test_embedding_model(model)
        elif model.type == ModelType.GENERATION.value:
            return await _test_generation_model(model)
        elif model.type == ModelType.NER.value:
            return await _test_ner_model(model)
        else:
            return ConnectionTestResult(
                success=False,
                message=f"Unknown model type: {model.type}",
            )
    except Exception as e:
        logger.error(
            "model_connection_test_failed",
            model_id=str(model.id),
            error=str(e),
        )
        return ConnectionTestResult(
            success=False,
            message=f"Connection test failed: {str(e)}",
        )


async def _test_embedding_model(model: LLMModel) -> ConnectionTestResult:
    """Test embedding model by generating a test embedding.

    Args:
        model: Embedding model to test.

    Returns:
        ConnectionTestResult with embedding dimensions.
    """
    start_time = time.time()
    model_path = _build_proxy_model_path(model)

    try:
        response = await aembedding(
            model=model_path,
            input=[EMBEDDING_TEST_TEXT],
            api_base=settings.litellm_url,
            api_key=settings.litellm_api_key,
            timeout=10,
        )

        latency_ms = (time.time() - start_time) * 1000
        embedding = response.data[0]["embedding"]
        dimensions = len(embedding)

        # Validate dimensions match config
        expected_dims = model.config.get("dimensions")
        dims_match = expected_dims is None or dimensions == expected_dims

        details: dict[str, Any] = {
            "dimensions": dimensions,
            "expected_dimensions": expected_dims,
            "dimensions_match": dims_match,
            "model_path": model_path,
            "proxy_alias": build_proxy_model_name(model),
        }

        if not dims_match:
            return ConnectionTestResult(
                success=False,
                message=(
                    f"Dimension mismatch: The model '{model.name}' returned {dimensions} dimensions, "
                    f"but you configured {expected_dims} dimensions. "
                    f"Please update the 'Dimensions' field to {dimensions} to match the actual model output, "
                    f"or verify you selected the correct model."
                ),
                latency_ms=round(latency_ms, 2),
                details=details,
            )

        logger.info(
            "embedding_model_test_success",
            model_id=str(model.id),
            dimensions=dimensions,
            latency_ms=round(latency_ms, 2),
        )

        return ConnectionTestResult(
            success=True,
            message=f"Embedding generated successfully ({dimensions} dimensions)",
            latency_ms=round(latency_ms, 2),
            details=details,
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)

        # Provide helpful error messages for common issues
        if "Invalid model name" in error_msg or "not found" in error_msg.lower():
            error_msg = (
                f"Model not registered with proxy. "
                f"Try saving the model again or restart the backend to re-sync. "
                f"Original error: {error_msg}"
            )

        return ConnectionTestResult(
            success=False,
            message=f"Embedding test failed: {error_msg}",
            latency_ms=round(latency_ms, 2),
            details={
                "error_type": type(e).__name__,
                "model_path": model_path,
            },
        )


async def _test_generation_model(model: LLMModel) -> ConnectionTestResult:
    """Test generation model by making a simple completion request.

    Args:
        model: Generation model to test.

    Returns:
        ConnectionTestResult with response preview.
    """
    start_time = time.time()
    model_path = _build_proxy_model_path(model)

    try:
        response = await acompletion(
            model=model_path,
            messages=GENERATION_TEST_PROMPT,
            api_base=settings.litellm_url,
            api_key=settings.litellm_api_key,
            timeout=15,
            max_tokens=20,
            temperature=0.1,
        )

        latency_ms = (time.time() - start_time) * 1000

        # Extract response content
        content = ""
        reasoning_content = ""
        if response.choices:
            message = response.choices[0].message
            content = message.content or ""
            # DeepSeek Reasoner models use reasoning_content field
            if hasattr(message, "reasoning_content") and message.reasoning_content:
                reasoning_content = message.reasoning_content

        # Use reasoning content as fallback if main content is empty
        preview_content = content or reasoning_content
        details: dict[str, Any] = {
            "response_preview": preview_content[:100]
            if preview_content
            else "(empty response - model may use reasoning field)",
            "model_path": model_path,
            "proxy_alias": build_proxy_model_name(model),
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        }
        if reasoning_content:
            details["has_reasoning"] = True

        logger.info(
            "generation_model_test_success",
            model_id=str(model.id),
            latency_ms=round(latency_ms, 2),
        )

        return ConnectionTestResult(
            success=True,
            message="Generation completed successfully",
            latency_ms=round(latency_ms, 2),
            details=details,
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)

        # Provide helpful error messages for common issues
        if "Invalid model name" in error_msg or "not found" in error_msg.lower():
            error_msg = (
                f"Model not registered with proxy. "
                f"Try saving the model again or restart the backend to re-sync. "
                f"Original error: {error_msg}"
            )

        return ConnectionTestResult(
            success=False,
            message=f"Generation test failed: {error_msg}",
            latency_ms=round(latency_ms, 2),
            details={
                "error_type": type(e).__name__,
                "model_path": model_path,
            },
        )


async def _test_ner_model(model: LLMModel) -> ConnectionTestResult:
    """Test NER model by making a simple entity extraction request.

    NER models are generation models specialized for entity extraction,
    so we test them similarly to generation models but with a structured
    JSON output expectation.

    Args:
        model: NER model to test.

    Returns:
        ConnectionTestResult with response preview.
    """
    start_time = time.time()
    model_path = _build_proxy_model_path(model)

    # NER test prompt - simple entity extraction
    ner_test_prompt = [
        {
            "role": "user",
            "content": 'Extract entities from: "John works at Apple in California." Return JSON: {"entities": [{"text": "...", "type": "..."}]}',
        }
    ]

    try:
        # Get config values for NER-specific parameters
        config = model.config or {}
        temperature = config.get("temperature_default", 0.0)
        top_p = config.get("top_p_default", 0.15)

        response = await acompletion(
            model=model_path,
            messages=ner_test_prompt,
            api_base=settings.litellm_url,
            api_key=settings.litellm_api_key,
            timeout=15,
            max_tokens=100,
            temperature=temperature,
            top_p=top_p,
        )

        latency_ms = (time.time() - start_time) * 1000

        # Extract response content
        content = ""
        if response.choices:
            content = response.choices[0].message.content or ""

        # Check if response looks like JSON
        is_json_response = content.strip().startswith(
            "{"
        ) or content.strip().startswith("[")

        details: dict[str, Any] = {
            "response_preview": content[:200] if content else "",
            "model_path": model_path,
            "proxy_alias": build_proxy_model_name(model),
            "tokens_used": response.usage.total_tokens if response.usage else 0,
            "is_json_response": is_json_response,
        }

        logger.info(
            "ner_model_test_success",
            model_id=str(model.id),
            latency_ms=round(latency_ms, 2),
            is_json_response=is_json_response,
        )

        return ConnectionTestResult(
            success=True,
            message="NER model test completed successfully",
            latency_ms=round(latency_ms, 2),
            details=details,
        )

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)

        # Provide helpful error messages for common issues
        if "Invalid model name" in error_msg or "not found" in error_msg.lower():
            error_msg = (
                f"Model not registered with proxy. "
                f"Try saving the model again or restart the backend to re-sync. "
                f"Original error: {error_msg}"
            )

        return ConnectionTestResult(
            success=False,
            message=f"NER test failed: {error_msg}",
            latency_ms=round(latency_ms, 2),
            details={
                "error_type": type(e).__name__,
                "model_path": model_path,
            },
        )
