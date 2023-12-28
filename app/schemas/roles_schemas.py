from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.profil_roles_schemas import ProfilRoleListing
from app.schemas.privilege_roles_schemas import PrivilegeRoleListing

class Role(BaseModel):
    name: str
    description: str
    
    

class RoleCreate(Role):
   pass


class RoleListing(Role):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class RoleDetail(RoleListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    profil_roles: List[ProfilRoleListing]
    privilege_roles: List[PrivilegeRoleListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class RoleUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    

