from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from examples.api_for_sqlalchemy.models.base import Base


class BetaDeltaBinding(Base):
    __tablename__ = "beta_delta_binding"

    beta_id: Mapped[int] = mapped_column(ForeignKey("beta.id", ondelete="CASCADE"))
    delta_id: Mapped[int] = mapped_column(ForeignKey("delta.id", ondelete="CASCADE"))
