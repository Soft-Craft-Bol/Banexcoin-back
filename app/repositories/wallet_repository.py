from sqlalchemy.orm import Session
from app.models.wallet import Wallet

def create_wallet(db: Session, data: dict):
    wallet = Wallet(**data)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

def get_wallets(db: Session):
    return db.query(Wallet).all()

def get_wallet_by_id(db: Session, wallet_id: int):
    return db.query(Wallet).filter(Wallet.id == wallet_id).first()