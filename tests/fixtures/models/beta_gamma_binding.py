from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from examples.api_for_sqlalchemy.models.base import Base


class BetaGammaBinding(Base):
    __tablename__ = "beta_gamma_binding"

    beta_id: Mapped[int] = mapped_column(ForeignKey("beta.id", ondelete="CASCADE"))
    gamma_id: Mapped[int] = mapped_column(ForeignKey("gamma.id", ondelete="CASCADE"))
