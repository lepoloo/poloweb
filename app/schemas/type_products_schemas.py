from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.products_schemas import ProductListing

class TypeProduct(BaseModel):
    name: str
    description: str
    
    

class TypeProductCreate(TypeProduct):
   pass


class TypeProductListing(TypeProduct):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class TypeProductDetail(TypeProductListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    products: List[ProductListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class TypeProductUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    

