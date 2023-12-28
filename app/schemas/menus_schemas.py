from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class Menu(BaseModel):
    card_id: str
    product_id: str
    price: float = Field(..., description="Cet attribut supérieur à 0.")
    
    

class MenuCreate(Menu):
   pass


class MenuListing(Menu):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class MenuDetail(MenuListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class MenuUpdate(BaseModel):
    card_id: Optional[constr(max_length=256)] = None
    product_id: Optional[constr(max_length=256)] = None
    price: Optional[float] = Field(None, ge=0)
    # active: bool = True
