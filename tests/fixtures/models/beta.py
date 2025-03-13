from sqlalchemy.orm import Mapped, relationship

from examples.api_for_sqlalchemy.models.base import Base

from .alpha import Alpha
from .delta import Delta
from .gamma import Gamma


class Beta(Base):
    __tablename__ = "beta"

    alphas: Mapped[Alpha] = relationship("Alpha")
    deltas: Mapped[list[Delta]] = relationship(
        "Delta",
        secondary="beta_delta_binding",
        lazy="noload",
    )
    gammas: Mapped[list[Gamma]] = relationship(
        "Gamma",
        secondary="beta_gamma_binding",
        back_populates="betas",
        lazy="noload",
    )
