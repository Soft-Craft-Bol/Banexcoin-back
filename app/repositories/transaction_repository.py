from sqlalchemy.orm import Session
from app.models.transaction import Transaction

def create_transaction(db: Session, data: dict):
    transaction = Transaction(**data)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def get_transactions(db: Session):
    return db.query(Transaction).all()

def get_transactions_by_source(db: Session, source: str):
    return db.query(Transaction).filter(
        Transaction.source == source
    ).all()