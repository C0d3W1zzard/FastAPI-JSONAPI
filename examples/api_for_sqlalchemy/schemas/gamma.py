from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Annotated,
    Optional,
)

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .beta import BetaSchema
    from .delta import DeltaSchema


class GammaSchema(BaseModel):
    betas: Annotated[
        Optional[BetaSchema],
        RelationshipInfo(
            resource_type="beta",
            many=True,
        ),
    ] = None
    delta: Annotated[
        Optional[DeltaSchema],
        RelationshipInfo(
            resource_type="delta",
        ),
    ] = None
