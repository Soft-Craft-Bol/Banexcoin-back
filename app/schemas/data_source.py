from pydantic import BaseModel


class DataSourceCreate(BaseModel):
    name: str
    type: str


class DataSourceResponse(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        from_attributes = True