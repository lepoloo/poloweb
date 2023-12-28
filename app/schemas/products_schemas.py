from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.menus_schemas import MenuListing

class Product(BaseModel):
    name: str
    type_product_id: str
    description: str = Field(..., max_length=65535)
    price: float = Field(..., description="Cet attribut supérieur à 0.")
    
    

class ProductCreate(Product):
   image: str


class ProductListing(Product):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class ProductDetail(ProductListing):
    
    image: str
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    menus: List[MenuListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class ProductUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    price: Optional[float] = Field(None, ge=0)
    image: Optional[constr(max_length=256)] = None
    # active: bool = True
