from sqlalchemy.orm import Session
from app.models.reconciliation import Reconciliation


def delete_reconciliations_by_upload(db: Session, upload_id: int):
    db.query(Reconciliation).filter(
        Reconciliation.upload_id == upload_id
    ).delete()
    db.commit()


def bulk_create_reconciliations(db: Session, items: list[dict]):
    if not items:
        return []

    records = [Reconciliation(**item) for item in items]

    db.add_all(records)
    db.commit()

    return records


def get_reconciliations(db: Session, upload_id: int | None = None):
    query = db.query(Reconciliation)

    if upload_id is not None:
        query = query.filter(Reconciliation.upload_id == upload_id)

    return query.order_by(Reconciliation.created_at.desc()).all()