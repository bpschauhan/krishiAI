from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.farm import Farm
from app.models.farmer import Farmer
from app.models.language import Language
from app.models.location import District
from app.models.plot import Plot
from app.schemas.onboarding import (
    DistrictRead,
    FarmCreate,
    FarmRead,
    FarmerCreate,
    FarmerDetail,
    FarmerRead,
    LanguageRead,
    PlotCreate,
    PlotRead,
)

router = APIRouter()


@router.get("/districts", response_model=list[DistrictRead])
def list_districts(db: Session = Depends(get_db)) -> list[District]:
    return list(
        db.scalars(
            select(District)
            .where(District.is_active.is_(True), District.state == "Uttar Pradesh")
            .order_by(District.name)
        )
    )


@router.get("/languages", response_model=list[LanguageRead])
def list_languages(db: Session = Depends(get_db)) -> list[Language]:
    return list(db.scalars(select(Language).where(Language.is_active.is_(True)).order_by(Language.name)))


@router.post("/farmers", response_model=FarmerRead, status_code=status.HTTP_201_CREATED)
def create_farmer(payload: FarmerCreate, db: Session = Depends(get_db)) -> Farmer:
    _get_required(db, District, payload.district_id, "District")
    _get_required(db, Language, payload.language_id, "Language")

    farmer = Farmer(**payload.model_dump())
    db.add(farmer)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farmer with this phone number already exists",
        ) from exc
    db.refresh(farmer)
    return farmer


@router.get("/farmers/{farmer_id}", response_model=FarmerDetail)
def get_farmer(farmer_id: int, db: Session = Depends(get_db)) -> FarmerDetail:
    farmer = db.scalar(
        select(Farmer)
        .options(joinedload(Farmer.district), joinedload(Farmer.language))
        .where(Farmer.id == farmer_id)
    )
    if farmer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")

    farm_count = db.scalar(select(func.count(Farm.id)).where(Farm.farmer_id == farmer_id)) or 0
    plot_count = (
        db.scalar(
            select(func.count(Plot.id)).join(Farm, Plot.farm_id == Farm.id).where(Farm.farmer_id == farmer_id)
        )
        or 0
    )
    return FarmerDetail.model_validate(
        {
            **FarmerRead.model_validate(farmer).model_dump(),
            "district": farmer.district,
            "language": farmer.language,
            "farm_count": farm_count,
            "plot_count": plot_count,
        }
    )


@router.post("/farms", response_model=FarmRead, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, db: Session = Depends(get_db)) -> Farm:
    _get_required(db, Farmer, payload.farmer_id, "Farmer")
    _get_required(db, District, payload.district_id, "District")

    farm = Farm(**payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.post("/plots", response_model=PlotRead, status_code=status.HTTP_201_CREATED)
def create_plot(payload: PlotCreate, db: Session = Depends(get_db)) -> Plot:
    _get_required(db, Farm, payload.farm_id, "Farm")

    plot = Plot(**payload.model_dump())
    db.add(plot)
    db.commit()
    db.refresh(plot)
    return plot


def _get_required(db: Session, model: type[District] | type[Farm] | type[Farmer] | type[Language], item_id: int, name: str):
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} not found")
    return item
