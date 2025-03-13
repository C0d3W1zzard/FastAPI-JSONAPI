from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UUID as UUIDType

from examples.api_for_sqlalchemy.models.base import Base


class CustomUUIDItem(Base):
    __tablename__ = "custom_uuid_item"

    id: Mapped[UUID] = mapped_column(UUIDType(as_uuid=True), primary_key=True)
    extra_id: Mapped[Optional[UUID]] = mapped_column(UUIDType(as_uuid=True), unique=True)
