from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from examples.api_for_sqlalchemy.models.base import Base

if TYPE_CHECKING:
    from .beta import Beta
    from .gamma import Gamma


class Delta(Base):
    __tablename__ = "delta"

    name: Mapped[str]

    gammas: Mapped[list[Gamma]] = relationship(
        "Gamma",
        back_populates="delta",
        lazy="noload",
    )
    betas: Mapped[list[Beta]] = relationship(
        "Beta",
        secondary="beta_delta_binding",
        back_populates="deltas",
        lazy="noload",
    )
