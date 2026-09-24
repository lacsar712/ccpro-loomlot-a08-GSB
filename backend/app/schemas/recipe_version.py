from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RecipeVersionCreate(BaseModel):
    dye_house_id: int = Field(..., alias="dyeHouseId")
    recipe_name: str = Field(..., min_length=1, max_length=128, alias="recipeName")
    version_no: int = Field(..., ge=1, alias="versionNo")
    is_active: bool = Field(True, alias="isActive")
    max_fabric_kg: float = Field(..., gt=0, alias="maxFabricKg")

    model_config = ConfigDict(populate_by_name=True)


class RecipeVersionUpdate(BaseModel):
    recipe_name: Optional[str] = Field(None, min_length=1, max_length=128, alias="recipeName")
    version_no: Optional[int] = Field(None, ge=1, alias="versionNo")
    is_active: Optional[bool] = Field(None, alias="isActive")
    max_fabric_kg: Optional[float] = Field(None, gt=0, alias="maxFabricKg")

    model_config = ConfigDict(populate_by_name=True)


class RecipeVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    dye_house_id: int = Field(serialization_alias="dyeHouseId")
    recipe_name: str = Field(serialization_alias="recipeName")
    version_no: int = Field(serialization_alias="versionNo")
    is_active: bool = Field(serialization_alias="isActive")
    max_fabric_kg: float = Field(serialization_alias="maxFabricKg")
