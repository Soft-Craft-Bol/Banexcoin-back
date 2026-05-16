from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.wallet import Wallet

from app.schemas.wallet import WalletCreate, WalletResponse

from app.repositories.wallet_repository import (
    create_wallet,
    get_wallets,
    get_wallet_by_id
)

from app.services.crypto_service import (
    get_native_balance,
    get_erc20_balance,
    get_wallet_portfolio
)

router = APIRouter(prefix="/wallets", tags=["Wallets"])

@router.post("/", response_model=WalletResponse)
def create_wallet_endpoint(
    data: WalletCreate,
    db: Session = Depends(get_db)
):
    existing_wallet = db.query(Wallet).filter(
        Wallet.address == data.address
    ).first()

    if existing_wallet:
        raise HTTPException(
            status_code=400,
            detail="La wallet ya existe"
        )

    wallet = create_wallet(
        db,
        {
            "name": data.name,
            "network": data.network,
            "address": data.address,
            "currency": data.currency,
            "balance": 0
        }
    )

    return wallet


@router.get("/", response_model=list[WalletResponse])
def list_wallets(
    db: Session = Depends(get_db)
):
    return get_wallets(db)


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet(
    wallet_id: int,
    db: Session = Depends(get_db)
):
    wallet = get_wallet_by_id(db, wallet_id)

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet no encontrada"
        )

    return wallet


@router.get("/{address}/balance")
def wallet_balance(
    address: str,
    network: str = Query(default="ethereum")
):
    try:
        return get_native_balance(address, network)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )


@router.get("/{address}/tokens/{token}/balance")
def token_balance(
    address: str,
    token: str,
    network: str = Query(default="polygon")
):
    try:
        return get_erc20_balance(
            address,
            token,
            network
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )


@router.get("/{address}/portfolio")
def wallet_portfolio(
    address: str,
    network: str = Query(default="polygon")
):
    try:
        return get_wallet_portfolio(
            address,
            network
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

@router.get("/{wallet_id}/portfolio/db")
def wallet_portfolio_from_db(
    wallet_id: int,
    db: Session = Depends(get_db)
):
    wallet = get_wallet_by_id(db, wallet_id)

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet no encontrada"
        )

    try:
        portfolio = get_wallet_portfolio(
            wallet.address,
            wallet.network
        )

        wallet.balance = portfolio["native"]["balance"]

        db.commit()

        return {
            "wallet": {
                "id": wallet.id,
                "name": wallet.name,
                "network": wallet.network,
                "address": wallet.address,
                "currency": wallet.currency
            },
            "portfolio": portfolio
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )