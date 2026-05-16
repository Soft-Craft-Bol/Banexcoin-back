from pydantic import BaseModel


class TransactionCreate(BaseModel):
    source: str
    tx_type: str | None = None
    reference: str | None = None
    amount: float
    currency: str = "USD"
    asset_id: int


class TransactionResponse(TransactionCreate):
    id: int
    status: str

    class Config:
        from_attributes = True