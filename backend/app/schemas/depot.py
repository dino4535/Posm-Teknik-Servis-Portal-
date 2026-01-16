from pydantic import BaseModel


class DepotResponse(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True
