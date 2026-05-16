from fastapi import APIRouter

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/")
def list_assets():
    return [{"message": "assets ok"}]