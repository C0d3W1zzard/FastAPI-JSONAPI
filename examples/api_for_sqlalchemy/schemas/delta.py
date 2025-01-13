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
    from .gamma import GammaSchema


class DeltaSchema(BaseModel):
    name: str

    gammas: Annotated[
        Optional[GammaSchema],
        RelationshipInfo(
            resource_type="gamma",
            many=True,
        ),
    ] = None
    betas: Annotated[
        Optional[BetaSchema],
        RelationshipInfo(
            resource_type="beta",
            many=True,
        ),
    ] = None
