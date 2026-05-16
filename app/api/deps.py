from fastapi import Depends
from app.core.database import get_db

def get_database(db = Depends(get_db)):
    return db
