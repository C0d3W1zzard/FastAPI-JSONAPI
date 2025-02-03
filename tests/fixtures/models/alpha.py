from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from examples.api_for_sqlalchemy.models.base import Base

if TYPE_CHECKING:
    from .beta import Beta
    from .gamma import Gamma


class Alpha(Base):
    __tablename__ = "alpha"

    beta_id: Mapped[int] = mapped_column(ForeignKey("beta.id"), index=True)
    beta: Mapped[Beta] = relationship(back_populates="alphas")
    gamma_id: Mapped[int] = mapped_column(ForeignKey("gamma.id"))
    gamma: Mapped[Gamma] = relationship("Gamma")
