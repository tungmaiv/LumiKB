"""Unit tests for AdminStatsService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.document import DocumentStatus
from app.schemas.admin import AdminStats
from app.services.admin_stats_service import AdminStatsService


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    session.scalar = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def admin_stats_service(mock_session):
    """Create AdminStatsService with mocked session."""
    return AdminStatsService(mock_session)


@pytest.mark.asyncio
async def test_get_dashboard_stats_cache_hit(admin_stats_service, mock_session):
    """Test that cache hit returns cached data without DB query."""
    cached_stats = AdminStats(
        users={'total': 100, 'active': 80, 'inactive': 20},
        knowledge_bases={'total': 50, 'by_status': {'active': 45, 'archived': 5}},
        documents={
            'total': 1000,
            'by_status': {'READY': 900, 'PENDING': 50, 'FAILED': 50},
        },
        storage={'total_bytes': 1000000, 'avg_doc_size_bytes': 1000},
        activity={
            'searches': {'last_24h': 10, 'last_7d': 70, 'last_30d': 300},
            'generations': {'last_24h': 5, 'last_7d': 35, 'last_30d': 150},
        },
        trends={'searches': [10] * 30, 'generations': [5] * 30},
    )

    with patch(
        'app.services.admin_stats_service.get_redis_client'
    ) as mock_redis_client:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached_stats.model_dump_json())
        mock_redis_client.return_value = mock_redis

        result = await admin_stats_service.get_dashboard_stats()

        # Verify cache hit
        mock_redis.get.assert_called_once_with('admin:stats:dashboard')
        # Verify no DB queries made
        mock_session.scalar.assert_not_called()
        # Verify result matches cached data
        assert result.users.total == 100
        assert result.users.active == 80


@pytest.mark.asyncio
async def test_get_dashboard_stats_cache_miss(admin_stats_service, mock_session):
    """Test that cache miss triggers DB aggregation and caches result."""
    # Mock Redis cache miss
    with patch(
        'app.services.admin_stats_service.get_redis_client'
    ) as mock_redis_client:
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # Cache miss
        mock_redis.setex = AsyncMock()
        mock_redis_client.return_value = mock_redis

        # Mock DB queries
        mock_session.scalar.side_effect = [
            100,  # total_users
            80,  # active_users
            50,  # total_kbs
            1000,  # total_docs
            1000000,  # total_bytes
        ]

        # Mock status counts
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ('active', 45),
            ('archived', 5),
        ]
        mock_session.execute.return_value = mock_result

        # Mock audit event counts
        with patch.object(
            admin_stats_service, '_count_audit_events', return_value=10
        ):
            with patch.object(
                admin_stats_service, '_get_daily_counts', return_value=[5] * 30
            ):
                result = await admin_stats_service.get_dashboard_stats()

        # Verify cache miss
        mock_redis.get.assert_called_once()
        # Verify DB queries made
        assert mock_session.scalar.call_count >= 5
        # Verify result cached
        mock_redis.setex.assert_called_once()
        assert mock_redis.setex.call_args[0][0] == 'admin:stats:dashboard'
        assert mock_redis.setex.call_args[0][1] == 300  # 5 minutes TTL


@pytest.mark.asyncio
async def test_aggregate_stats_user_counts(admin_stats_service, mock_session):
    """Test user statistics aggregation."""
    # Mock total users
    mock_session.scalar.side_effect = [
        150,  # total_users
        120,  # active_users (created in last 30 days)
        45,  # total_kbs
        1250,  # total_docs
        524288000,  # total_bytes
    ]

    # Mock other queries
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch.object(admin_stats_service, '_count_audit_events', return_value=0):
        with patch.object(admin_stats_service, '_get_daily_counts', return_value=[0] * 30):
            stats = await admin_stats_service._aggregate_stats()

    assert stats.users.total == 150
    assert stats.users.active == 120
    assert stats.users.inactive == 30


@pytest.mark.asyncio
async def test_aggregate_stats_activity_metrics(admin_stats_service, mock_session):
    """Test activity metrics aggregation."""
    # Mock basic counts
    mock_session.scalar.side_effect = [
        100,  # total_users
        80,  # active_users
        50,  # total_kbs
        1000,  # total_docs
        1000000,  # total_bytes
    ]

    # Mock status counts
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    # Mock audit event counts
    with patch.object(admin_stats_service, '_count_audit_events') as mock_count:
        mock_count.side_effect = [
            42,  # searches_24h
            285,  # searches_7d
            1150,  # searches_30d
            15,  # generations_24h
            98,  # generations_7d
            420,  # generations_30d
        ]

        with patch.object(
            admin_stats_service, '_get_daily_counts', return_value=[10] * 30
        ):
            stats = await admin_stats_service._aggregate_stats()

    assert stats.activity.searches.last_24h == 42
    assert stats.activity.searches.last_7d == 285
    assert stats.activity.searches.last_30d == 1150
    assert stats.activity.generations.last_24h == 15
    assert stats.activity.generations.last_7d == 98
    assert stats.activity.generations.last_30d == 420


@pytest.mark.asyncio
async def test_count_by_status(admin_stats_service, mock_session):
    """Test grouping by status column."""
    from app.models.document import Document

    mock_result = MagicMock()
    mock_result.all.return_value = [
        (DocumentStatus.READY, 1100),
        (DocumentStatus.PENDING, 50),
        (DocumentStatus.FAILED, 100),
    ]
    mock_session.execute.return_value = mock_result

    counts = await admin_stats_service._count_by_status(Document, Document.status)

    assert counts['READY'] == 1100
    assert counts['PENDING'] == 50
    assert counts['FAILED'] == 100


@pytest.mark.asyncio
async def test_count_audit_events_with_hours(admin_stats_service, mock_session):
    """Test counting audit events within hours period."""
    mock_session.scalar.return_value = 42

    count = await admin_stats_service._count_audit_events('search.query', hours=24)

    assert count == 42
    # Verify query included time filter
    assert mock_session.scalar.called


@pytest.mark.asyncio
async def test_count_audit_events_with_days(admin_stats_service, mock_session):
    """Test counting audit events within days period."""
    mock_session.scalar.return_value = 285

    count = await admin_stats_service._count_audit_events('search.query', days=7)

    assert count == 285


@pytest.mark.asyncio
async def test_get_daily_counts_sparkline(admin_stats_service, mock_session):
    """Test daily counts for sparkline visualization."""
    # Mock query result with some days having data
    mock_result = MagicMock()
    today = datetime.now(UTC).date()
    mock_result.all.return_value = [
        (MagicMock(day=MagicMock(date=lambda: today - timedelta(days=2))), 38),
        (MagicMock(day=MagicMock(date=lambda: today - timedelta(days=1))), 42),
        (MagicMock(day=MagicMock(date=lambda: today)), 35),
    ]
    mock_session.execute.return_value = mock_result

    daily_counts = await admin_stats_service._get_daily_counts('search.query', days=30)

    # Verify returned 30 elements
    assert len(daily_counts) == 30
    # Verify all elements are integers
    assert all(isinstance(c, int) for c in daily_counts)


@pytest.mark.asyncio
async def test_redis_unavailable_fallback(admin_stats_service, mock_session):
    """Test graceful fallback when Redis is unavailable."""
    # Mock Redis failure
    with patch(
        'app.services.admin_stats_service.get_redis_client'
    ) as mock_redis_client:
        mock_redis_client.side_effect = Exception('Redis connection failed')

        # Mock DB queries
        mock_session.scalar.side_effect = [
            100,  # total_users
            80,  # active_users
            50,  # total_kbs
            1000,  # total_docs
            1000000,  # total_bytes
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        with patch.object(
            admin_stats_service, '_count_audit_events', return_value=0
        ):
            with patch.object(
                admin_stats_service, '_get_daily_counts', return_value=[0] * 30
            ):
                # Should not raise exception, should fall back to DB
                result = await admin_stats_service.get_dashboard_stats()

        # Verify result is valid
        assert result.users.total == 100
        assert result.users.active == 80


@pytest.mark.asyncio
async def test_empty_audit_data_graceful_handling(admin_stats_service, mock_session):
    """Test graceful handling when no audit data exists."""
    mock_session.scalar.side_effect = [
        100,  # total_users
        80,  # active_users
        50,  # total_kbs
        1000,  # total_docs
        1000000,  # total_bytes
    ]

    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    # Mock zero counts for all audit queries
    with patch.object(admin_stats_service, '_count_audit_events', return_value=0):
        with patch.object(
            admin_stats_service, '_get_daily_counts', return_value=[0] * 30
        ):
            stats = await admin_stats_service._aggregate_stats()

    # Verify stats returned with zero activity
    assert stats.activity.searches.last_24h == 0
    assert stats.activity.searches.last_7d == 0
    assert stats.activity.searches.last_30d == 0
    assert stats.trends.searches == [0] * 30
    assert stats.trends.generations == [0] * 30
