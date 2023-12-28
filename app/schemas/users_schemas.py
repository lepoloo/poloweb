from pydantic import BaseModel, EmailStr, PositiveInt, validator, root_validator, constr,Field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List
from app.schemas.profils_schemas import ProfilListing
from app.schemas.likes_schemas import LikeListing
from app.schemas.signals_schemas import SignalListing
from app.schemas.reels_schemas import ReelListing
from app.schemas.stories_schemas import StoryListing
from app.schemas.notes_schemas import NoteListing
from app.schemas.favorites_schemas import FavoriteListing
from app.schemas.entertainment_sites_schemas import EntertainmentSiteListing
from app.models.models import GenderType

class User(BaseModel):
    name: str
    surname: str
    phone: str
    email: EmailStr
    birthday: date
    gender: GenderType
    username: str
    

class UserCreate(User):
   image: str
   password: str
   is_staff: bool = False
   is_owner: bool = False
   is_annoncer: bool = False
   


class UserListing(User):
    id: str
    refnumber: str
    active: bool
   
    class Config:
        from_attributes = True 

class UserDetail(UserListing):
    
    image: str
    is_staff: bool
    is_owner: bool
    is_annoncer: bool
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[constr(max_length=256)] = None
    profils: List[ProfilListing]
    entertainment_sites: List[EntertainmentSiteListing]
    notes: List[NoteListing]
    favorites: List[FavoriteListing]
    reels: List[ReelListing]
    likes: List[LikeListing]
    stories: List[StoryListing]
    signals: List[SignalListing]
    
    class Config:
        from_attributes = True 
        # orm_mode = True 
        

class UserUpdate(BaseModel):
    name: Optional[constr(max_length=256)] = None
    surname: Optional[constr(max_length=256)] = None
    phone: Optional[constr(max_length=256)] = None
    birthday: Optional[date] = None
    gender: Optional[GenderType] = None
    email: Optional[EmailStr] = None
    image: Optional[constr(max_length=256)] = None
    username: Optional[constr(max_length=256)] = None
    password: Optional[constr(max_length=256)] = None
    is_staff: Optional[bool] = False
    is_owner: Optional[bool] = False
    is_annoncer: Optional[bool] = False
    # active: bool = True


class UserLogin(BaseModel):
#    email: EmailStr
   username: str
   password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[str] = None
