"""LiteLLM Proxy Sync Service.

Synchronizes models from the database to the LiteLLM proxy runtime.
When a model is created/updated/deleted in the Admin UI, this service
ensures the LiteLLM proxy knows about it so connection tests work.

Option C Implementation: DB models are registered with LiteLLM proxy
at runtime, eliminating the need to manually edit litellm_config.yaml.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import httpx
import structlog

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.llm_model import LLMModel

logger = structlog.get_logger(__name__)

# Provider to LiteLLM model prefix mapping
# See: https://docs.litellm.ai/docs/providers
PROVIDER_PREFIXES = {
    "ollama": "ollama/",
    "openai": "openai/",
    "anthropic": "anthropic/",
    "gemini": "gemini/",
    "deepseek": "deepseek/",
    "qwen": "dashscope/",  # Qwen uses DashScope API via dashscope/ prefix
    "mistral": "mistral/",
    "cohere": "cohere/",
    "azure": "azure/",
    "lmstudio": "openai/",  # LM Studio uses OpenAI-compatible API
}

# Providers that need environment-specific api_base
# Resolved at registration time, not stored in DB
PROVIDERS_NEEDING_API_BASE = {"ollama", "lmstudio"}


def build_proxy_model_name(model: "LLMModel") -> str:
    """Generate unique proxy alias for a DB model.

    Format: db-{uuid} to avoid conflicts with YAML-defined models.

    Args:
        model: LLMModel instance.

    Returns:
        Unique alias for LiteLLM proxy registration.
    """
    return f"db-{model.id}"


def _build_litellm_model_name(model: "LLMModel") -> str:
    """Build the LiteLLM model name with provider prefix.

    Args:
        model: LLMModel instance.

    Returns:
        Provider-prefixed model name (e.g., 'ollama/mxbai-embed-large').
    """
    prefix = PROVIDER_PREFIXES.get(model.provider, "")
    # Some model IDs may already include provider prefix
    if "/" in model.model_id:
        return model.model_id
    return f"{prefix}{model.model_id}" if prefix else model.model_id


def _build_litellm_params(
    model: "LLMModel",
    decrypted_api_key: str | None,
) -> dict[str, Any]:
    """Build litellm_params for proxy registration.

    Environment-specific URLs are resolved here at registration time,
    not stored in the database. This allows the same DB model to work
    across different environments (dev, staging, prod).

    Args:
        model: LLMModel instance.
        decrypted_api_key: Decrypted API key if available.

    Returns:
        litellm_params dict for /model/new API.
    """
    params: dict[str, Any] = {
        "model": _build_litellm_model_name(model),
    }

    # Add api_base for providers that need it
    if model.provider == "ollama":
        # Use the proxy-specific Ollama URL for registration
        # This is typically host.docker.internal:11434 when LiteLLM runs in Docker
        # but the backend runs on the host
        params["api_base"] = settings.ollama_url_for_proxy
    elif model.provider == "lmstudio":
        # LM Studio uses custom endpoint from model config
        if model.api_endpoint:
            params["api_base"] = model.api_endpoint
    elif model.api_endpoint:
        # Custom endpoint provided for other providers
        params["api_base"] = model.api_endpoint

    # Add API key if available
    if decrypted_api_key:
        params["api_key"] = decrypted_api_key

    return params


async def register_model_with_proxy(
    model: "LLMModel",
    decrypted_api_key: str | None = None,
) -> bool:
    """Register a model with the LiteLLM proxy.

    Called when a model is created or updated in the Admin UI.
    The model is registered with a unique alias (db-{uuid}) that
    the connection tester uses to verify connectivity.

    Args:
        model: The LLMModel to register.
        decrypted_api_key: Decrypted API key if available.

    Returns:
        True if registration succeeded, False otherwise.
    """
    proxy_model_name = build_proxy_model_name(model)
    litellm_params = _build_litellm_params(model, decrypted_api_key)

    payload = {
        "model_name": proxy_model_name,
        "litellm_params": litellm_params,
        "model_info": {
            "description": f"DB Model: {model.name}",
            "db_id": str(model.id),
            "type": model.type,
            "provider": model.provider,
        },
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.litellm_url}/model/new",
                json=payload,
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                timeout=10.0,
            )

            if response.status_code in (200, 201):
                logger.info(
                    "model_registered_with_proxy",
                    model_id=str(model.id),
                    model_name=model.name,
                    proxy_alias=proxy_model_name,
                    litellm_model=litellm_params.get("model"),
                )
                return True
            else:
                logger.error(
                    "model_registration_failed",
                    model_id=str(model.id),
                    status=response.status_code,
                    response=response.text[:500],
                )
                return False

    except httpx.ConnectError as e:
        logger.warning(
            "litellm_proxy_unavailable",
            model_id=str(model.id),
            error=str(e),
            hint="Model saved but proxy registration failed. Will sync on next startup.",
        )
        return False
    except Exception as e:
        logger.error(
            "model_registration_error",
            model_id=str(model.id),
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


async def _get_model_info_id_from_proxy(proxy_model_name: str) -> str | None:
    """Look up the internal model_info.id for a model by its name.

    LiteLLM's /model/delete endpoint requires the internal model_info.id (a hash),
    not the model_name alias we set during registration.

    Args:
        proxy_model_name: The model name alias (e.g., 'db-{uuid}').

    Returns:
        The model_info.id hash if found, None otherwise.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.litellm_url}/model/info",
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                for m in models:
                    if m.get("model_name") == proxy_model_name:
                        model_info = m.get("model_info", {})
                        return model_info.get("id")
            return None
    except Exception as e:
        logger.warning(
            "failed_to_lookup_model_info_id",
            proxy_model_name=proxy_model_name,
            error=str(e),
        )
        return None


async def unregister_model_from_proxy(model: "LLMModel") -> bool:
    """Remove a model from the LiteLLM proxy.

    Called when a model is deleted from the Admin UI.

    Note: LiteLLM's /model/delete endpoint requires the internal model_info.id
    (a hash), not the model_name alias. This function looks up the model_info_id
    before attempting deletion.

    Args:
        model: The LLMModel to unregister.

    Returns:
        True if unregistration succeeded, False otherwise.
    """
    proxy_model_name = build_proxy_model_name(model)

    # Look up the internal model_info.id required for deletion
    model_info_id = await _get_model_info_id_from_proxy(proxy_model_name)

    if not model_info_id:
        # Model not found in proxy - already deleted or never registered
        logger.info(
            "model_not_found_in_proxy",
            model_id=str(model.id),
            proxy_alias=proxy_model_name,
        )
        return True  # Treat as success (idempotent)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.litellm_url}/model/delete",
                json={"id": model_info_id},  # Use model_info.id, not model_name
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                timeout=10.0,
            )

            # 200/204 = success, 404 = already deleted (idempotent)
            if response.status_code in (200, 204, 404):
                logger.info(
                    "model_unregistered_from_proxy",
                    model_id=str(model.id),
                    proxy_alias=proxy_model_name,
                    model_info_id=model_info_id,
                )
                return True
            else:
                logger.warning(
                    "model_unregistration_failed",
                    model_id=str(model.id),
                    model_info_id=model_info_id,
                    status=response.status_code,
                    response=response.text[:500],
                )
                return False

    except httpx.ConnectError:
        logger.warning(
            "litellm_proxy_unavailable_for_unregister",
            model_id=str(model.id),
        )
        return False
    except Exception as e:
        logger.error(
            "model_unregistration_error",
            model_id=str(model.id),
            error=str(e),
        )
        return False


async def _get_db_models_from_proxy() -> list[dict[str, str]]:
    """Get list of all DB model entries currently in the proxy.

    Returns:
        List of dicts with 'model_name' and 'model_info_id' for models starting with 'db-'.
        The model_info_id is required for deletion via /model/delete endpoint.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.litellm_url}/model/info",
                headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                # Get DB models with their internal IDs for deletion
                db_models = []
                seen_names: set[str] = set()
                for m in models:
                    model_name = m.get("model_name", "")
                    if model_name.startswith("db-") and model_name not in seen_names:
                        seen_names.add(model_name)
                        # model_info.id is required for /model/delete endpoint
                        model_info = m.get("model_info", {})
                        model_info_id = model_info.get("id", "")
                        if model_info_id:
                            db_models.append(
                                {
                                    "model_name": model_name,
                                    "model_info_id": model_info_id,
                                }
                            )
                return db_models
            return []
    except Exception as e:
        logger.warning("failed_to_get_proxy_models", error=str(e))
        return []


async def _clear_db_models_from_proxy() -> int:
    """Clear all DB models from the LiteLLM proxy.

    This removes stale entries before re-registering fresh ones.
    Only removes models with 'db-' prefix (created by this sync service).

    Note: LiteLLM's /model/delete endpoint requires the internal model_info.id
    (a hash), not the model_name alias. This function now correctly uses
    the model_info_id for deletion.

    Returns:
        Number of models cleared.
    """
    db_models = await _get_db_models_from_proxy()
    if not db_models:
        return 0

    cleared = 0
    async with httpx.AsyncClient() as client:
        for model_entry in db_models:
            model_name = model_entry["model_name"]
            model_info_id = model_entry["model_info_id"]
            try:
                response = await client.post(
                    f"{settings.litellm_url}/model/delete",
                    json={"id": model_info_id},  # Use model_info.id, not model_name
                    headers={"Authorization": f"Bearer {settings.litellm_api_key}"},
                    timeout=10.0,
                )
                if response.status_code in (200, 204):
                    cleared += 1
                    logger.debug(
                        "proxy_model_deleted",
                        model_name=model_name,
                        model_info_id=model_info_id,
                    )
                elif response.status_code == 404:
                    # Model already deleted, log but count as success
                    logger.debug(
                        "proxy_model_already_deleted",
                        model_name=model_name,
                        model_info_id=model_info_id,
                    )
                    cleared += 1
                else:
                    logger.warning(
                        "proxy_model_delete_failed",
                        model_name=model_name,
                        model_info_id=model_info_id,
                        status=response.status_code,
                        response=response.text[:200],
                    )
            except Exception as e:
                logger.warning(
                    "failed_to_clear_proxy_model",
                    model_name=model_name,
                    model_info_id=model_info_id,
                    error=str(e),
                )

    logger.info("proxy_models_cleared", count=cleared, total=len(db_models))
    return cleared


async def sync_all_models_to_proxy(
    models: list["LLMModel"],
    get_decrypted_key: Callable[["LLMModel"], str | None],
) -> dict[str, int]:
    """Sync all DB models to LiteLLM proxy.

    Called on application startup to re-register models after proxy restart.
    This ensures models registered via Admin UI continue to work even if
    the LiteLLM proxy container is restarted.

    This function first clears all existing DB models from the proxy to
    prevent duplicate entries, then registers fresh copies.

    Args:
        models: List of all LLMModels from database.
        get_decrypted_key: Function to decrypt API keys.

    Returns:
        Dict with success/failed/total/cleared counts.
    """
    if not models:
        logger.info("proxy_sync_skipped", reason="no_models_in_db")
        return {"success": 0, "failed": 0, "total": 0, "cleared": 0}

    # Clear existing DB models first to prevent duplicates
    cleared = await _clear_db_models_from_proxy()

    results = {"success": 0, "failed": 0, "total": len(models), "cleared": cleared}

    for model in models:
        decrypted_key = get_decrypted_key(model) if model.api_key_encrypted else None
        success = await register_model_with_proxy(model, decrypted_key)
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1

    logger.info(
        "proxy_sync_completed",
        total=results["total"],
        success=results["success"],
        failed=results["failed"],
        cleared=results["cleared"],
    )

    return results


async def check_proxy_health() -> bool:
    """Check if LiteLLM proxy is available.

    Returns:
        True if proxy is healthy, False otherwise.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.litellm_url}/health",
                timeout=5.0,
            )
            return response.status_code == 200
    except Exception:
        return False
