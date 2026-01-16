from pydantic import BaseModel


class TerritoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
