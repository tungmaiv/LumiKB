"""System configuration model."""

from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from app.models.base import Base


class SystemConfig(Base):
    """System configuration settings stored in database."""

    __tablename__ = "system_config"

    key = Column(String(255), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_by = Column(String(255), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), nullable=True, default=lambda: datetime.now(UTC)
    )
