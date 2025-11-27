# app/schemas/inventory_status.py

from pydantic import BaseModel


class InventoryStatusBase(BaseModel):
    name: str


class InventoryStatusCreate(InventoryStatusBase):
    pass



class InventoryStatusUpdate(InventoryStatusBase):
    pass



class InventoryStatus(InventoryStatusBase):
    id: int

    class Config:
        from_attributes = True
