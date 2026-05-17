from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ReconciliationResponse(BaseModel):
    id: int
    upload_id: int

    operation_transaction_id: int | None
    bank_transaction_id: int | None

    reconciliation_type: str
    reference: str | None

    operation_amount: Decimal | None
    bank_amount: Decimal | None
    difference: Decimal | None

    status: str
    message: str | None

    created_at: datetime

    class Config:
        from_attributes = True