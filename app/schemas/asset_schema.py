from typing import Literal
from pydantic import BaseModel


class AssetCreate(BaseModel):
    symbol: str
    name: str
    type: Literal["FIAT", "CRYPTO"]


class AssetResponse(BaseModel):
    id: int
    symbol: str
    name: str
    type: str

    class Config:
        from_attributes = True