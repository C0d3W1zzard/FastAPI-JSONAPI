from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional

from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import RelationshipInfo

if TYPE_CHECKING:
    from .alpha import AlphaSchema
    from .delta import DeltaSchema
    from .gamma import GammaSchema


class BetaSchema(BaseModel):
    alphas: Annotated[
        Optional[AlphaSchema],
        RelationshipInfo(
            resource_type="alpha",
        ),
    ] = None
    gammas: Annotated[
        Optional[GammaSchema],
        RelationshipInfo(
            resource_type="gamma",
            many=True,
        ),
    ] = None
    deltas: Annotated[
        Optional[DeltaSchema],
        RelationshipInfo(
            resource_type="delta",
            many=True,
        ),
    ] = None
