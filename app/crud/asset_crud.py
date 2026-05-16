from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.schemas.asset_schema import AssetCreate


def create_asset(db: Session, data: AssetCreate):
    asset = Asset(
        symbol=data.symbol,
        name=data.name,
        type=data.type
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


def get_assets(db: Session):
    return db.query(Asset).all()


def get_asset_by_id(db: Session, asset_id: int):
    return db.query(Asset).filter(Asset.id == asset_id).first()