from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models.dye_house import DyeHouse
from app.models.recipe_version import RecipeVersion
from app.models.user import User
from app.schemas.recipe_version import RecipeVersionCreate, RecipeVersionUpdate, RecipeVersionOut

router = APIRouter(prefix="/api/recipe-versions", tags=["recipe-versions"])


@router.get("", response_model=List[RecipeVersionOut])
def list_recipe_versions(
    dye_house_id: Optional[int] = Query(None, alias="dyeHouseId"),
    is_active: Optional[bool] = Query(None, alias="isActive"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(RecipeVersion)
    if dye_house_id is not None:
        q = q.filter(RecipeVersion.dye_house_id == dye_house_id)
    if is_active is not None:
        q = q.filter(RecipeVersion.is_active.is_(is_active))
    return q.order_by(
        RecipeVersion.dye_house_id, RecipeVersion.recipe_name, RecipeVersion.version_no
    ).all()


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
        max_fabric_kg=payload.max_fabric_kg,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="同坊同配方名下该版本号已存在")
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
    """主管可改配方名/版本号/上限，亦可启停版本（isActive）。"""
    item = db.query(RecipeVersion).filter(RecipeVersion.id == version_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="配方版本不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="同坊同配方名下该版本号已存在")
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
