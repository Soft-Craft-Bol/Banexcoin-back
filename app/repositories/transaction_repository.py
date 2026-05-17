from sqlalchemy.orm import Session
from app.models.transaction import Transaction


def bulk_create_transactions(db: Session, transactions: list[dict]):
    if not transactions:
        return []

    db_transactions = [Transaction(**item) for item in transactions]

    db.add_all(db_transactions)
    db.commit()

    return db_transactions


def delete_transactions_by_upload(db: Session, upload_id: int):
    db.query(Transaction).filter(Transaction.upload_id == upload_id).delete()
    db.commit()