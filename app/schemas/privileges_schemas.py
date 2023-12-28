from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.profil_privileges_schemas import ProfilPrivilegeListing
from app.schemas.privilege_roles_schemas import PrivilegeRoleListing

class Privilege(BaseModel):
    name: str
    description: str
    
    

class PrivilegeCreate(Privilege):
   pass


class PrivilegeListing(Privilege):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class PrivilegeDetail(PrivilegeListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    privilege_roles: List[PrivilegeRoleListing]
    profil_privileges: List[ProfilPrivilegeListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class PrivilegeUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    description: Optional[constr(max_length=65535)] = None
    

