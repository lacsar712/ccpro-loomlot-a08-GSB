from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models.dye_house import DyeHouse
from app.models.recipe_version import RecipeVersion
from app.models.user import User
from app.schemas.recipe_version import (
    RecipeVersionCreate,
    RecipeVersionUpdate,
    RecipeVersionOut,
)

router = APIRouter(prefix="/api/recipe-versions", tags=["recipe-versions"])


def ensure_active_recipe_version(
    db: Session,
    dye_house_id: int,
    recipe_name: str,
    fabric_kg: float,
) -> RecipeVersion:
    """染程开立/更新共用：配方名必须命中所属染坊的启用版本，且布重不超过版本上限。"""
    version = (
        db.query(RecipeVersion)
        .filter(
            RecipeVersion.dye_house_id == dye_house_id,
            RecipeVersion.recipe_name == recipe_name,
            RecipeVersion.is_active.is_(True),
        )
        .first()
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"配方「{recipe_name}」在所属染坊无启用版本，无法开立染程",
        )
    if fabric_kg > version.fabric_kg_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"布重 {fabric_kg}kg 超过配方「{recipe_name}」v{version.version_no}"
                f" 单次布重上限 {version.fabric_kg_max}kg"
            ),
        )
    return version


@router.get("", response_model=List[RecipeVersionOut])
def list_recipe_versions(
    dye_house_id: Optional[int] = Query(None, alias="dyeHouseId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(RecipeVersion)
    if dye_house_id is not None:
        q = q.filter(RecipeVersion.dye_house_id == dye_house_id)
    return (
        q.order_by(
            RecipeVersion.dye_house_id,
            RecipeVersion.recipe_name,
            RecipeVersion.version_no,
        )
        .all()
    )


@router.post("", response_model=RecipeVersionOut, status_code=status.HTTP_201_CREATED)
def create_recipe_version(
    payload: RecipeVersionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    house = db.query(DyeHouse).filter(DyeHouse.id == payload.dye_house_id).first()
    if not house:
        raise HTTPException(status_code=400, detail="染坊不存在")
    item = RecipeVersion(
        dye_house_id=payload.dye_house_id,
        recipe_name=payload.recipe_name,
        version_no=payload.version_no,
        is_active=payload.is_active,
        fabric_kg_max=payload.fabric_kg_max,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="同坊同配方名下版本号已存在")
    db.refresh(item)
    return item


@router.get("/{version_id}", response_model=RecipeVersionOut)
def get_recipe_version(
    version_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(RecipeVersion).filter(RecipeVersion.id == version_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="配方版本不存在")
    return item


@router.put("/{version_id}", response_model=RecipeVersionOut)
def update_recipe_version(
    version_id: int,
    payload: RecipeVersionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = db.query(RecipeVersion).filter(RecipeVersion.id == version_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="配方版本不存在")
    data = payload.model_dump(exclude_unset=True)
    if "dye_house_id" in data:
        house = db.query(DyeHouse).filter(DyeHouse.id == data["dye_house_id"]).first()
        if not house:
            raise HTTPException(status_code=400, detail="染坊不存在")
    for k, v in data.items():
        setattr(item, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="同坊同配方名下版本号已存在")
    db.refresh(item)
    return item


@router.post("/{version_id}/enable", response_model=RecipeVersionOut)
def enable_recipe_version(
    version_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = db.query(RecipeVersion).filter(RecipeVersion.id == version_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="配方版本不存在")
    item.is_active = True
    db.commit()
    db.refresh(item)
    return item


@router.post("/{version_id}/disable", response_model=RecipeVersionOut)
def disable_recipe_version(
    version_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = db.query(RecipeVersion).filter(RecipeVersion.id == version_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="配方版本不存在")
    item.is_active = False
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe_version(
    version_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    item = db.query(RecipeVersion).filter(RecipeVersion.id == version_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="配方版本不存在")
    db.delete(item)
    db.commit()
