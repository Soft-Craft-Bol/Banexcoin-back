from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate


def create_data_source(db: Session, data: DataSourceCreate):
    data_source = DataSource(
        name=data.name,
        type=data.type
    )

    db.add(data_source)
    db.commit()
    db.refresh(data_source)

    return data_source


def get_data_sources(db: Session):
    return db.query(DataSource).all()


def get_data_source_by_id(db: Session, data_source_id: int):
    return db.query(DataSource).filter(DataSource.id == data_source_id).first()