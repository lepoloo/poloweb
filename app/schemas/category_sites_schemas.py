from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.category_entertainment_sites_schemas import CategoryEntertainmentSiteListing

class CategorySite(BaseModel):
    name: str
    description: str
    
    

class CategorySiteCreate(CategorySite):
   image: str


class CategorySiteListing(CategorySite):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class CategorySiteDetail(CategorySiteListing):
    image: str
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    category_entertainment_sites: List[CategoryEntertainmentSiteListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class CategorySiteUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    

