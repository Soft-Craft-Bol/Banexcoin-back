from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine

from app.models.user import User
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.models.upload import Upload
from app.models.reconciliation import Reconciliation

from app.api.routes import auth, users, uploads, reconciliation, wallets, reports, transactions

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(uploads.router)
app.include_router(reconciliation.router)
app.include_router(transactions.router)
app.include_router(wallets.router)
app.include_router(reports.router)

@app.get("/")
def root():
    return {
        "message": "Crypto Reconciliation API funcionando correctamente"
    }
