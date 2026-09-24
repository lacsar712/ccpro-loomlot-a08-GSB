"""染程配方命中规则：新建与更新染程共用的启用版本命中 + 布重上限校验。"""

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.recipe_version import RecipeVersion
from app.models.vat import Vat


def resolve_active_version(
    db: Session, dye_house_id: int, recipe_name: str
) -> Optional[RecipeVersion]:
    """命中规则：同坊同配方名下取版本号最高的启用版本；无启用版本返回 None。"""
    return (
        db.query(RecipeVersion)
        .filter(
            RecipeVersion.dye_house_id == dye_house_id,
            RecipeVersion.recipe_name == recipe_name,
            RecipeVersion.is_active.is_(True),
        )
        .order_by(RecipeVersion.version_no.desc())
        .first()
    )


def validate_lot_against_version(
    db: Session, vat: Vat, recipe_name: str, fabric_kg: float
) -> RecipeVersion:
    """染程开立/更新共用校验。

    - 配方名未命中该染缸所属染坊的启用版本（含已停用）→ 409
    - 布重超过命中版本的单次布重上限 → 400
    """
    version = resolve_active_version(db, vat.dye_house_id, recipe_name)
    if version is None:
        raise HTTPException(
            status_code=409,
            detail=f"配方「{recipe_name}」在该染坊无启用版本，不可开立染程",
        )
    if fabric_kg > version.max_fabric_kg:
        raise HTTPException(
            status_code=400,
            detail=(
                f"布重 {fabric_kg}kg 超过配方「{recipe_name}」启用版本 "
                f"v{version.version_no} 的单次上限 {version.max_fabric_kg}kg"
            ),
        )
    return version
