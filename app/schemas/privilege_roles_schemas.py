from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

class PrivilegeRole(BaseModel):
    role_id: str
    privilege_id: str
    
    

class PrivilegeRoleCreate(PrivilegeRole):
   pass


class PrivilegeRoleListing(PrivilegeRole):
    id: str
    refnumber: str
    active: bool
    
    class Config:
        from_attributes = True 

class PrivilegeRoleDetail(PrivilegeRoleListing):
    
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class PrivilegeRoleUpdate(BaseModel):
    role_id: Optional[constr(max_length=256)] = None
    privilege_id: Optional[constr(max_length=256)] = None
    

