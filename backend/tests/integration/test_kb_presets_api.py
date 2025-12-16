"""Story 7-16 ATDD: KB Presets API Integration Tests.

Generated: 2025-12-10

Tests:
- AC-7.16.1: GET /api/v1/knowledge-bases/presets returns all presets
- AC-7.16.2-6: Each preset has correct configuration values
- AC-7.16.8: Preset detection logic via detect endpoint
"""

from httpx import AsyncClient


class TestListPresets:
    """Tests for GET /api/v1/knowledge-bases/presets endpoint (AC-7.16.1)."""

    async def test_list_presets_returns_all_five(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.1: Verify API returns all five presets."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()
        presets = data["presets"]

        assert len(presets) == 5

        preset_ids = [p["id"] for p in presets]
        assert "legal" in preset_ids
        assert "technical" in preset_ids
        assert "creative" in preset_ids
        assert "code" in preset_ids
        assert "general" in preset_ids

    async def test_list_presets_format(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """Each preset has id, name, and description fields."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()
        presets = data["presets"]

        for preset in presets:
            assert "id" in preset
            assert "name" in preset
            assert "description" in preset
            assert isinstance(preset["id"], str)
            assert isinstance(preset["name"], str)
            assert isinstance(preset["description"], str)
            assert len(preset["name"]) > 0
            assert len(preset["description"]) > 0


class TestGetPreset:
    """Tests for GET /api/v1/knowledge-bases/presets/{preset_id} endpoint (AC-7.16.2-6)."""

    async def test_get_legal_preset(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.2: Legal preset has correct values."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets/legal",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        preset = response.json()

        assert preset["id"] == "legal"
        assert preset["name"] == "Legal"

        settings = preset["settings"]
        assert settings["chunking"]["chunk_size"] == 1000
        assert settings["chunking"]["chunk_overlap"] == 200
        assert settings["retrieval"]["top_k"] == 15
        assert settings["retrieval"]["similarity_threshold"] == 0.75
        assert settings["generation"]["temperature"] == 0.3
        assert settings["prompts"]["citation_style"] == "footnote"
        assert settings["prompts"]["uncertainty_handling"] == "acknowledge"
        assert settings["preset"] == "legal"

    async def test_get_technical_preset(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.3: Technical preset has correct values."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets/technical",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        preset = response.json()

        assert preset["id"] == "technical"
        settings = preset["settings"]
        assert settings["chunking"]["chunk_size"] == 800
        assert settings["generation"]["temperature"] == 0.5
        assert settings["prompts"]["citation_style"] == "inline"
        assert settings["preset"] == "technical"

    async def test_get_creative_preset(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.4: Creative preset has high temperature."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets/creative",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        preset = response.json()

        settings = preset["settings"]
        assert settings["generation"]["temperature"] == 0.9
        assert settings["chunking"]["strategy"] == "semantic"
        assert settings["prompts"]["citation_style"] == "none"
        assert settings["prompts"]["uncertainty_handling"] == "best_effort"
        assert settings["preset"] == "creative"

    async def test_get_code_preset(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.5: Code preset has very low temperature."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets/code",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        preset = response.json()

        settings = preset["settings"]
        assert settings["generation"]["temperature"] == 0.2
        assert settings["prompts"]["uncertainty_handling"] == "refuse"
        assert settings["preset"] == "code"

    async def test_get_general_preset(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.6: General preset uses defaults."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets/general",
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        preset = response.json()

        assert preset["settings"]["preset"] == "general"

    async def test_get_nonexistent_preset_returns_404(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """Nonexistent preset returns 404."""
        response = await client.get(
            "/api/v1/knowledge-bases/presets/nonexistent",
            cookies=authenticated_headers,
        )

        assert response.status_code == 404


class TestDetectPreset:
    """Tests for POST /api/v1/knowledge-bases/presets/detect endpoint (AC-7.16.8)."""

    async def test_detect_legal_preset(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.8: Detect correctly identifies legal preset settings."""
        # Get legal preset settings first
        preset_response = await client.get(
            "/api/v1/knowledge-bases/presets/legal",
            cookies=authenticated_headers,
        )
        legal_settings = preset_response.json()["settings"]

        # Detect preset
        response = await client.post(
            "/api/v1/knowledge-bases/presets/detect",
            json=legal_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["detected_preset"] == "legal"

    async def test_detect_technical_preset(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.8: Detect correctly identifies technical preset."""
        preset_response = await client.get(
            "/api/v1/knowledge-bases/presets/technical",
            cookies=authenticated_headers,
        )
        settings = preset_response.json()["settings"]

        response = await client.post(
            "/api/v1/knowledge-bases/presets/detect",
            json=settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        assert response.json()["detected_preset"] == "technical"

    async def test_detect_custom_settings(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.8: Detect returns 'custom' for non-preset settings."""
        custom_settings = {
            "chunking": {
                "strategy": "recursive",
                "chunk_size": 999,  # Non-standard value
                "chunk_overlap": 123,
            },
            "retrieval": {
                "top_k": 7,
                "similarity_threshold": 0.65,
                "method": "vector",
                "mmr_enabled": False,
                "mmr_lambda": 0.5,
            },
            "generation": {
                "temperature": 0.42,  # Non-standard value
                "top_p": 0.88,
                "max_tokens": 2048,
            },
            "prompts": {
                "system_prompt": "Custom prompt",
                "citation_style": "inline",
                "uncertainty_handling": "acknowledge",
            },
            "preset": "custom",
        }

        response = await client.post(
            "/api/v1/knowledge-bases/presets/detect",
            json=custom_settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        assert response.json()["detected_preset"] == "custom"

    async def test_detect_modified_preset_returns_custom(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ) -> None:
        """AC-7.16.8: Detect returns 'custom' if preset settings are modified."""
        # Get legal preset and modify it
        preset_response = await client.get(
            "/api/v1/knowledge-bases/presets/legal",
            cookies=authenticated_headers,
        )
        settings = preset_response.json()["settings"]

        # Modify chunk size
        settings["chunking"]["chunk_size"] = settings["chunking"]["chunk_size"] + 100

        response = await client.post(
            "/api/v1/knowledge-bases/presets/detect",
            json=settings,
            cookies=authenticated_headers,
        )

        assert response.status_code == 200
        assert response.json()["detected_preset"] == "custom"


class TestPresetAuthentication:
    """Tests for authentication requirements."""

    async def test_list_presets_requires_auth(
        self,
        client: AsyncClient,
    ) -> None:
        """Unauthenticated request to list presets returns 401."""
        response = await client.get("/api/v1/knowledge-bases/presets")

        assert response.status_code == 401

    async def test_get_preset_requires_auth(
        self,
        client: AsyncClient,
    ) -> None:
        """Unauthenticated request to get preset returns 401."""
        response = await client.get("/api/v1/knowledge-bases/presets/legal")

        assert response.status_code == 401

    async def test_detect_preset_requires_auth(
        self,
        client: AsyncClient,
    ) -> None:
        """Unauthenticated request to detect preset returns 401."""
        response = await client.post(
            "/api/v1/knowledge-bases/presets/detect",
            json={"chunking": {"chunk_size": 512}},
        )

        assert response.status_code == 401
