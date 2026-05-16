from pydantic import BaseModel

class WalletCreate(BaseModel):
    name: str
    network: str
    address: str
    currency: str = "USDT"

class WalletResponse(BaseModel):
    id: int
    name: str
    network: str
    address: str
    balance: float
    currency: str

    class Config:
        from_attributes = True