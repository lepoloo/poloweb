from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.profil_roles_schemas import ProfilRoleListing
from app.schemas.profil_privileges_schemas import ProfilPrivilegeListing

class Profil(BaseModel):
    fucntion: str
    description: str = Field(..., max_length=65535)
    owner_id: str
    entertainment_site_id: str
    
    
    

class ProfilCreate(Profil):
   pass


class ProfilListing(Profil):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class ProfilDetail(ProfilListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    profil_roles: List[ProfilRoleListing]
    profil_privileges: List[ProfilPrivilegeListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class ProfilUpdate(BaseModel):
    fucntion: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    owner_id: Optional[constr(max_length=256)] = None
    entertainment_sites_id: Optional[constr(max_length=256)] = None
    
    # active: bool = True
   