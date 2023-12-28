from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class Favorite(BaseModel):
    owner_id: str
    entertainment_site_id: str
    
    

class FavoriteCreate(Favorite):
   pass


class FavoriteListing(Favorite):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class FavoriteDetail(FavoriteListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class FavoriteUpdate(BaseModel):
    owner_id: Optional[constr(max_length=256)] = None
    entertainment_site_id: Optional[constr(max_length=256)] = None
    

