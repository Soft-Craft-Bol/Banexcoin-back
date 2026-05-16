from sqlalchemy.orm import Session
from app.models.reconciliation import Reconciliation

def save_reconciliation(db: Session, data: dict):
    reconciliation = Reconciliation(**data)
    db.add(reconciliation)
    db.commit()
    db.refresh(reconciliation)
    return reconciliation

def get_reconciliations(db: Session):
    return db.query(Reconciliation).order_by(
        Reconciliation.id.desc()
    ).all()

def get_reconciliation_by_id(db: Session, reconciliation_id: int):
    return db.query(Reconciliation).filter(
        Reconciliation.id == reconciliation_id
    ).first()