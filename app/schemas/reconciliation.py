from datetime import date
from pydantic import BaseModel, Field
from typing import Literal


class ReconciliationCreate(BaseModel):
    wallet_id: int
    token: str = "usdt"


# ===== EPICA 5 =====

class ReconciliationPeriodCreate(BaseModel):
    start_date: date
    end_date: date

    period_type: Literal["DAILY", "MONTHLY"] = "DAILY"

    data_source_id: int
    asset_id: int


class InitialBalanceUpdate(BaseModel):
    initial_balance: float = Field(..., ge=0)


class ReportedFinalBalanceUpdate(BaseModel):
    reported_final_balance: float = Field(..., ge=0)


# ===== RESPONSE =====

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

    # ===== EPICA 5 =====

    start_date: date | None = None
    end_date: date | None = None

    period_type: str | None = None

    data_source_id: int | None = None
    asset_id: int | None = None

    initial_balance: float | None = None

    reported_final_balance: float | None = None

    expected_balance: float | None = None

    class Config:
        from_attributes = True