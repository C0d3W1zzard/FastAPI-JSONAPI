from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from pydantic import ConfigDict

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import ClientCanSetId


class CustomUUIDItemAttributesSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    extra_id: Optional[UUID] = None


class CustomUUIDItemSchema(CustomUUIDItemAttributesSchema):
    id: Annotated[UUID, ClientCanSetId()]
