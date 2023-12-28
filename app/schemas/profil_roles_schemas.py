from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class ProfilRole(BaseModel):
    profil_id: str
    role_id: str
    
    

class ProfilRoleCreate(ProfilRole):
   pass


class ProfilRoleListing(ProfilRole):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class ProfilRoleDetail(ProfilRoleListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class ProfilRoleUpdate(BaseModel):
    profil_id: Optional[constr(max_length=256)] = None
    role_id: Optional[constr(max_length=256)] = None
    # active: bool = True
