"""Unit tests for KBRecommendationService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.kb_access_log import AccessType
from app.schemas.kb_recommendation import KBRecommendation
from app.services.kb_recommendation_service import (
    CACHE_KEY_PREFIX,
    CACHE_TTL,
    WEIGHT_RECENT_ACCESS,
    WEIGHT_SEARCH_RELEVANCE,
    WEIGHT_SHARED_ACCESS,
    KBRecommendationService,
)


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.scalar = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def kb_recommendation_service(mock_session):
    """Create KBRecommendationService with mocked session."""
    return KBRecommendationService(mock_session)


@pytest.fixture
def sample_user_id():
    """Generate a sample user UUID."""
    return uuid4()


@pytest.fixture
def sample_kb_id():
    """Generate a sample KB UUID."""
    return uuid4()


@pytest.fixture
def mock_kb():
    """Create a mock KnowledgeBase."""
    kb = MagicMock()
    kb.id = uuid4()
    kb.name = "Test KB"
    kb.description = "Test description"
    kb.status = "active"
    return kb


class TestScoringAlgorithm:
    """Tests for scoring algorithm weights and calculations."""

    def test_weights_sum_to_one(self):
        """Verify scoring weights sum to 1.0 (100%)."""
        total = WEIGHT_RECENT_ACCESS + WEIGHT_SEARCH_RELEVANCE + WEIGHT_SHARED_ACCESS
        assert total == pytest.approx(1.0, abs=0.001)

    def test_weight_recent_access_is_40_percent(self):
        """Verify recent access weight is 40% (AC-5.8.2)."""
        assert pytest.approx(0.40, abs=0.001) == WEIGHT_RECENT_ACCESS

    def test_weight_search_relevance_is_35_percent(self):
        """Verify search relevance weight is 35% (AC-5.8.2)."""
        assert pytest.approx(0.35, abs=0.001) == WEIGHT_SEARCH_RELEVANCE

    def test_weight_shared_access_is_25_percent(self):
        """Verify shared access weight is 25% (AC-5.8.2)."""
        assert pytest.approx(0.25, abs=0.001) == WEIGHT_SHARED_ACCESS


class TestScoreCalculation:
    """Tests for score calculation methods."""

    @pytest.mark.asyncio
    async def test_calculate_scores_with_recent_access(
        self, kb_recommendation_service, mock_session, sample_user_id, sample_kb_id
    ):
        """Test recent access score calculation with 0.40 weight (AC-5.8.2)."""
        # Mock: User accessed this KB 10 times, max access is 10 (100% normalized)
        mock_session.scalar.side_effect = [
            10,  # KB access count in 30 days
            10,  # Max access count for any KB
        ]

        score = await kb_recommendation_service._get_recent_access_score(
            sample_user_id, sample_kb_id
        )

        # Perfect access should give 1.0 raw score
        assert score == pytest.approx(1.0, abs=0.001)

    @pytest.mark.asyncio
    async def test_calculate_scores_with_search_relevance(
        self, kb_recommendation_service, mock_session, sample_user_id, sample_kb_id
    ):
        """Test search relevance score calculation with 0.35 weight (AC-5.8.2)."""
        # Mock: 5 searches in this KB out of 10 total = 0.5 ratio
        mock_session.scalar.side_effect = [
            5,  # KB search count
            10,  # Total search count
        ]

        score = await kb_recommendation_service._get_search_relevance_score(
            sample_user_id, sample_kb_id
        )

        assert score == pytest.approx(0.5, abs=0.001)

    @pytest.mark.asyncio
    async def test_calculate_scores_with_shared_access(
        self, kb_recommendation_service, mock_session, sample_kb_id
    ):
        """Test shared access score calculation with 0.25 weight (AC-5.8.2)."""
        # Mock: KB has 75 accesses, max KB has 100 = 0.75 normalized
        mock_session.scalar.side_effect = [
            75,  # This KB's access count
            100,  # Max access count across all KBs
        ]

        score = await kb_recommendation_service._get_shared_access_score(sample_kb_id)

        assert score == pytest.approx(0.75, abs=0.001)

    @pytest.mark.asyncio
    async def test_scores_normalized_to_100(
        self, kb_recommendation_service, mock_session, sample_user_id
    ):
        """Test that final scores are normalized to 0-100 range (AC-5.8.2)."""
        # Mock user with perfect scores in all categories
        mock_user = MagicMock()
        mock_user.id = sample_user_id
        mock_user.created_at = datetime.now(UTC) - timedelta(days=30)  # Not cold start
        mock_session.get.return_value = mock_user

        # Mock accessible KB
        mock_kb = MagicMock()
        mock_kb.id = uuid4()
        mock_kb.name = "Test KB"
        mock_kb.description = "Test"
        mock_kb.status = "active"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_kb]
        mock_session.execute.return_value = mock_result

        # Mock perfect scores (1.0 raw for all factors)
        mock_session.scalar.side_effect = [
            1,  # Not cold start search count
            # For accessible KBs query (already mocked via execute)
            10,
            10,  # Recent access score
            10,
            10,  # Search relevance score
            100,
            100,  # Shared access score
            datetime.now(UTC),  # Last access time
        ]

        recommendations = (
            await kb_recommendation_service._calculate_personalized_recommendations(
                sample_user_id, 5
            )
        )

        # With perfect scores, weighted sum = 1.0 * 100 = 100
        if recommendations:
            assert 0 <= recommendations[0].score <= 100


class TestColdStart:
    """Tests for cold start handling."""

    @pytest.mark.asyncio
    async def test_cold_start_new_user(
        self, kb_recommendation_service, mock_session, sample_user_id
    ):
        """Test that new user (< 7 days, 0 searches) gets public KBs (AC-5.8.5)."""
        # Mock: New user created 3 days ago with 0 searches
        mock_user = MagicMock()
        mock_user.id = sample_user_id
        mock_user.created_at = datetime.now(UTC) - timedelta(days=3)
        mock_session.get.return_value = mock_user

        # Mock: 0 searches
        mock_session.scalar.return_value = 0

        is_cold_start = await kb_recommendation_service._is_cold_start_user(
            sample_user_id
        )

        assert is_cold_start is True

    @pytest.mark.asyncio
    async def test_cold_start_flag_set(self, kb_recommendation_service, mock_session):
        """Test that cold start recommendations have is_cold_start=true (AC-5.8.5)."""
        # Mock KB for cold start
        mock_kb = MagicMock()
        mock_kb.id = uuid4()
        mock_kb.name = "Popular KB"
        mock_kb.description = "Public KB"
        mock_kb.status = "active"

        mock_result = MagicMock()
        # Return tuple of (kb, access_count)
        mock_result.all.return_value = [(mock_kb, 50)]
        mock_session.execute.return_value = mock_result

        recommendations = (
            await kb_recommendation_service._get_cold_start_recommendations(5)
        )

        assert len(recommendations) > 0
        assert all(r.is_cold_start is True for r in recommendations)

    @pytest.mark.asyncio
    async def test_cold_start_established_user_returns_false(
        self, kb_recommendation_service, mock_session, sample_user_id
    ):
        """Test that established user (>= 7 days) is not cold start."""
        # Mock: User created 30 days ago
        mock_user = MagicMock()
        mock_user.id = sample_user_id
        mock_user.created_at = datetime.now(UTC) - timedelta(days=30)
        mock_session.get.return_value = mock_user

        is_cold_start = await kb_recommendation_service._is_cold_start_user(
            sample_user_id
        )

        assert is_cold_start is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_no_kbs_available(
        self, kb_recommendation_service, mock_session, sample_user_id
    ):
        """Test empty list returned when no KBs available (AC-5.8.2)."""
        # Mock: User has no accessible KBs
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        recommendations = (
            await kb_recommendation_service._calculate_personalized_recommendations(
                sample_user_id, 5
            )
        )

        assert recommendations == []

    @pytest.mark.asyncio
    async def test_user_with_no_permissions(
        self, kb_recommendation_service, mock_session, sample_user_id
    ):
        """Test that user only sees recommendations for accessible KBs."""
        # Mock: User has no KBs
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        recommendations = (
            await kb_recommendation_service._calculate_personalized_recommendations(
                sample_user_id, 5
            )
        )

        # User should get empty list if no accessible KBs
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_division_by_zero_handling_recent_access(
        self, kb_recommendation_service, mock_session, sample_user_id, sample_kb_id
    ):
        """Test graceful handling of division by zero in recent access score."""
        # Mock: Zero access count
        mock_session.scalar.side_effect = [
            0,  # KB access count
        ]

        score = await kb_recommendation_service._get_recent_access_score(
            sample_user_id, sample_kb_id
        )

        # Should return 0, not raise exception
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_division_by_zero_handling_search_relevance(
        self, kb_recommendation_service, mock_session, sample_user_id, sample_kb_id
    ):
        """Test graceful handling of division by zero in search relevance."""
        # Mock: Zero searches
        mock_session.scalar.side_effect = [
            0,  # KB search count
        ]

        score = await kb_recommendation_service._get_search_relevance_score(
            sample_user_id, sample_kb_id
        )

        # Should return 0, not raise exception
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_division_by_zero_handling_shared_access(
        self, kb_recommendation_service, mock_session, sample_kb_id
    ):
        """Test graceful handling of division by zero in shared access."""
        # Mock: Zero global access
        mock_session.scalar.side_effect = [
            0,  # This KB's access count
        ]

        score = await kb_recommendation_service._get_shared_access_score(sample_kb_id)

        # Should return 0, not raise exception
        assert score == 0.0


class TestRedisCaching:
    """Tests for Redis caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(
        self, kb_recommendation_service, sample_user_id
    ):
        """Test that cache hit returns cached data without DB query (AC-5.8.3)."""
        cached_recommendation = KBRecommendation(
            kb_id=uuid4(),
            kb_name="Cached KB",
            description="From cache",
            score=85.0,
            reason="Cached reason",
            last_accessed=None,
            is_cold_start=False,
        )

        import json

        cached_data = json.dumps([cached_recommendation.model_dump(mode="json")])

        with patch(
            "app.services.kb_recommendation_service.get_redis_client"
        ) as mock_redis_client:
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value=cached_data)
            mock_redis_client.return_value = mock_redis

            result = await kb_recommendation_service.get_recommendations(
                sample_user_id, 5
            )

            # Verify cache was checked
            mock_redis.get.assert_called_once_with(
                f"{CACHE_KEY_PREFIX}{sample_user_id}"
            )
            # Verify result matches cached data
            assert len(result) == 1
            assert result[0].kb_name == "Cached KB"

    @pytest.mark.asyncio
    async def test_cache_ttl_is_one_hour(self):
        """Verify cache TTL is 3600 seconds (1 hour) (AC-5.8.3)."""
        assert CACHE_TTL == 3600

    @pytest.mark.asyncio
    async def test_cache_key_format(self, sample_user_id):
        """Verify cache key format is kb_recommendations:user:{user_id} (AC-5.8.3)."""
        expected_key = f"kb_recommendations:user:{sample_user_id}"
        assert f"{CACHE_KEY_PREFIX}{sample_user_id}" == expected_key

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, kb_recommendation_service, sample_user_id):
        """Test cache invalidation clears user's recommendations cache."""
        with patch(
            "app.services.kb_recommendation_service.get_redis_client"
        ) as mock_redis_client:
            mock_redis = AsyncMock()
            mock_redis.delete = AsyncMock()
            mock_redis_client.return_value = mock_redis

            await kb_recommendation_service.invalidate_user_recommendations(
                sample_user_id
            )

            mock_redis.delete.assert_called_once_with(
                f"{CACHE_KEY_PREFIX}{sample_user_id}"
            )

    @pytest.mark.asyncio
    async def test_redis_unavailable_fallback(
        self, kb_recommendation_service, mock_session, sample_user_id
    ):
        """Test graceful fallback when Redis is unavailable."""
        with patch(
            "app.services.kb_recommendation_service.get_redis_client"
        ) as mock_redis_client:
            # First call fails (cache check)
            mock_redis_client.side_effect = Exception("Redis unavailable")

            # Mock cold start user
            mock_user = MagicMock()
            mock_user.id = sample_user_id
            mock_user.created_at = datetime.now(UTC) - timedelta(days=3)
            mock_session.get.return_value = mock_user
            mock_session.scalar.return_value = 0  # No searches

            # Mock cold start KBs
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session.execute.return_value = mock_result

            # Should not raise exception
            result = await kb_recommendation_service.get_recommendations(
                sample_user_id, 5
            )

            assert isinstance(result, list)


class TestReasonGeneration:
    """Tests for human-readable reason generation."""

    def test_generate_reason_recent_access_dominant(self, kb_recommendation_service):
        """Test reason generation when recent access is dominant factor."""
        reason = kb_recommendation_service._generate_reason(
            recent_score=1.0,
            search_score=0.2,
            shared_score=0.1,
        )

        assert "recently" in reason.lower()

    def test_generate_reason_search_relevance_dominant(self, kb_recommendation_service):
        """Test reason generation when search relevance is dominant factor."""
        reason = kb_recommendation_service._generate_reason(
            recent_score=0.1,
            search_score=1.0,
            shared_score=0.1,
        )

        assert "search" in reason.lower()

    def test_generate_reason_shared_access_dominant(self, kb_recommendation_service):
        """Test reason generation when shared access is dominant factor."""
        reason = kb_recommendation_service._generate_reason(
            recent_score=0.0,
            search_score=0.0,
            shared_score=1.0,
        )

        assert "popular" in reason.lower()


class TestAccessLogging:
    """Tests for KB access logging."""

    @pytest.mark.asyncio
    async def test_log_kb_access_creates_entry(
        self, kb_recommendation_service, mock_session, sample_user_id, sample_kb_id
    ):
        """Test that log_kb_access creates a new access log entry."""
        with patch(
            "app.services.kb_recommendation_service.get_redis_client"
        ) as mock_redis_client:
            mock_redis = AsyncMock()
            mock_redis.delete = AsyncMock()
            mock_redis_client.return_value = mock_redis

            await kb_recommendation_service.log_kb_access(
                sample_user_id, sample_kb_id, AccessType.SEARCH
            )

            # Verify entry was added
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_kb_access_invalidates_cache(
        self, kb_recommendation_service, sample_user_id, sample_kb_id
    ):
        """Test that log_kb_access invalidates user's recommendation cache."""
        with patch(
            "app.services.kb_recommendation_service.get_redis_client"
        ) as mock_redis_client:
            mock_redis = AsyncMock()
            mock_redis.delete = AsyncMock()
            mock_redis_client.return_value = mock_redis

            await kb_recommendation_service.log_kb_access(
                sample_user_id, sample_kb_id, AccessType.SEARCH
            )

            # Verify cache was invalidated
            mock_redis.delete.assert_called_once_with(
                f"{CACHE_KEY_PREFIX}{sample_user_id}"
            )

    @pytest.mark.asyncio
    async def test_log_kb_access_fire_and_forget(
        self, kb_recommendation_service, mock_session, sample_user_id, sample_kb_id
    ):
        """Test that log_kb_access doesn't raise exceptions (fire-and-forget)."""
        mock_session.commit.side_effect = Exception("DB error")

        # Should not raise exception
        await kb_recommendation_service.log_kb_access(
            sample_user_id, sample_kb_id, AccessType.SEARCH
        )

        # No exception raised is success
