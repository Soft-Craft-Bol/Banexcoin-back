from fastapi import APIRouter

router = APIRouter(
    prefix="/data-sources",
    tags=["Data Sources"]
)


@router.get("/")
def list_data_sources():
    return [
        {
            "id": 1,
            "name": "Binance",
            "type": "exchange",
            "status": "active"
        },
        {
            "id": 2,
            "name": "MetaMask",
            "type": "wallet",
            "status": "active"
        },
        {
            "id": 3,
            "name": "Coinbase",
            "type": "exchange",
            "status": "inactive"
        }
    ]