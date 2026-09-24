from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.dye_house import DyeHouse


class RecipeVersion(Base):
    __tablename__ = "recipe_versions"
    __table_args__ = (
        UniqueConstraint("dye_house_id", "recipe_name", "version_no", name="uq_house_recipe_version"),
        CheckConstraint("max_fabric_kg > 0", name="ck_recipe_version_max_fabric_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dye_house_id: Mapped[int] = mapped_column(ForeignKey("dye_houses.id"), nullable=False, index=True)
    recipe_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    max_fabric_kg: Mapped[float] = mapped_column(Float, nullable=False)

    dye_house: Mapped["DyeHouse"] = relationship("DyeHouse", back_populates="recipe_versions")
