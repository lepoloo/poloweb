from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class CategoryEntertainmentSite(BaseModel):
    entertainment_site_id: str
    category_site_id: str
    
    

class CategoryEntertainmentSiteCreate(CategoryEntertainmentSite):
   pass


class CategoryEntertainmentSiteListing(CategoryEntertainmentSite):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class CategoryEntertainmentSiteDetail(CategoryEntertainmentSiteListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class CategoryEntertainmentSiteUpdate(BaseModel):
    entertainment_site_id: Optional[constr(max_length=256)] = None
    category_site_id: Optional[constr(max_length=256)] = None
    # active: bool = True
