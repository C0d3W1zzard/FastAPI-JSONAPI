from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from examples.api_for_sqlalchemy.models.base import Base


class ContainsTimestamp(Base):
    __tablename__ = "contains_timestamp"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
