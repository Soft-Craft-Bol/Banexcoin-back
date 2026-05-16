from fastapi import APIRouter
from app.services.report_service import generate_summary

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/summary")
def summary():
    return generate_summary(total_transactions=20, differences=3)
