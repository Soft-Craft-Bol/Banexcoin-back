from pydantic import BaseModel

class ReconciliationCreate(BaseModel):
    wallet_id: int
    token: str = "usdt"

class ReconciliationResponse(BaseModel):
    id: int
    wallet_id: int | None
    source_a: str
    source_b: str
    total_a: float
    total_b: float
    difference: float
    status: str
    details: str | None

    class Config:
        from_attributes = True