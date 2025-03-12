from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from examples.api_for_sqlalchemy.models.base import Base

if TYPE_CHECKING:
    from .alpha import Alpha
    from .beta import Beta
    from .delta import Delta


class Gamma(Base):
    __tablename__ = "gamma"

    alpha: Mapped[Alpha] = relationship("Alpha")
    betas: Mapped[list[Beta]] = relationship(
        "Beta",
        secondary="beta_gamma_binding",
        back_populates="gammas",
        lazy="raise",
    )
    delta_id: Mapped[int] = mapped_column(
        ForeignKey(
            "delta.id",
            ondelete="CASCADE",
        ),
        index=True,
    )
    delta: Mapped[Delta] = relationship("Delta")
