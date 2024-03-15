import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import users_schemas
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models import models
from utils.users_utils import hash
import uuid
from datetime import datetime, timedelta
from app.database import engine, get_db
from typing import Optional
from  utils import oauth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

# /users/

router = APIRouter(prefix = "/user", tags=['Users Requests'])

# create a new user
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=users_schemas.UserListing)
# async def create_user(new_user_c: users_schemas.UserCreate, file: UploadFile = File(...), db: Session = Depends(get_db)):
async def create_user(new_user_c: users_schemas.UserCreate, db: Session = Depends(get_db)):
    # Vérifiez si l'utilisateur existe déjà dans la base de données
    if new_user_c.username:
        if db.query(models.User).filter(models.User.username == new_user_c.username).first():
            raise HTTPException(status_code=400, detail='Registered user with this username')
    if new_user_c.phone:
        if db.query(models.User).filter(models.User.phone == new_user_c.phone).first():
            raise HTTPException(status_code=400, detail='Registered user with this phone number')
    if new_user_c.email:
        if db.query(models.User).filter(models.User.email == new_user_c.email).first():
            raise HTTPException(status_code=400, detail='Registered user with this email')
    if new_user_c.image:
        if db.query(models.User).filter(models.User.image == new_user_c.image).first():
            raise HTTPException(status_code=400, detail='Registered user with this image')
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
       
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.User).filter(models.User.refnumber.endswith(codefin)).all())) + "/" + codefin
    hashed_password = hash(new_user_c.password)
    new_user_c.password = hashed_password
    
    author = "current_user"
    
    new_user= models.User(id = concatenated_uuid, **new_user_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_user )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_user)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_user)

# Get all users requests
@router.get("/get_all_actif/", response_model=List[users_schemas.UserListing])
async def read_users_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    users_queries = db.query(models.User).filter(models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
                        
    return jsonable_encoder(users_queries)


# Get an user
# "/get_user_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&username=valeur_username" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_user_by_attribut/", status_code=status.HTTP_200_OK, response_model=List[users_schemas.UserListing])
async def detail_user_by_attribut(refnumber: Optional[str] = None, phone: Optional[str] = None, name: Optional[str] = None, surname: Optional[str] = None, email: Optional[str] = None, username: Optional[str] = None,is_owner: Optional[bool] = None ,is_staff: Optional[bool] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    user_query = {} # objet vide
    if refnumber is not None :
        user_query = db.query(models.User).filter(models.User.refnumber == refnumber, models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    if name is not None :
        user_query = db.query(models.User).filter(models.User.name.contains(name), models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    if surname is not None :
        user_query = db.query(models.User).filter(models.User.surname.contains(surname), models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    if phone is not None :
        user_query = db.query(models.User).filter(models.User.phone.contains(phone), models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    if email is not None:
        user_query = db.query(models.User).filter(models.User.email.contains(email), models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    if username is not None :
        user_query = db.query(models.User).filter(models.User.username.contains(username), models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    if is_staff is not None :
        user_query = db.query(models.User).filter(models.User.is_staff == is_staff, models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    if is_owner is not None :
        user_query = db.query(models.User).filter(models.User.is_owner == is_owner, models.User.active == "True").order_by(models.User.name).offset(skip).limit(limit).all()
    
    return jsonable_encoder(user_query)

# Get an user
@router.get("/get/{user_id}", status_code=status.HTTP_200_OK, response_model=users_schemas.UserDetail)
async def detail_user(user_id: str, db: Session = Depends(get_db)):
    user_query = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} does not exist")
    
    profils = user_query.profils
    details = [{ 'id': profil.id, 'refnumber': profil.refnumber, 'fucntion': profil.fucntion, 'description': profil.description, 'owner_id': profil.owner_id, 'entertainment_site_id': profil.entertainment_site_id, 'active': profil.active} for profil in profils]
    profils = details
    
    entertainment_sites = user_query.entertainment_sites
    details = [{ 'id': entertainment_site.id, 'refnumber': entertainment_site.refnumber, 'name': entertainment_site.name, 'address': entertainment_site.address, 'description': entertainment_site.description, 'longitude': entertainment_site.longitude, 'latitude': entertainment_site.latitude, 'quarter_id': entertainment_site.quarter_id, 'owner_id': entertainment_site.owner_id, 'nb_visite': entertainment_site.nb_visite, 'active': entertainment_site.active} for entertainment_site in entertainment_sites]
    entertainment_sites = details
    
    favorites = user_query.favorites
    details = [{ 'id': favorite.id, 'refnumber': favorite.refnumber, 'owner_id': favorite.owner_id, 'entertainment_site_id': favorite.entertainment_site_id, 'active': favorite.active} for favorite in favorites]
    favorites = details
    
    likes = user_query.likes
    details = [{ 'id': like.id, 'refnumber': like.refnumber, 'owner_id': like.owner_id, 'event_id': like.event_id, 'anounce_id': like.anounce_id, 'reel_id': like.reel_id, 'story_id': like.story_id, 'active': like.active} for like in likes]
    likes = details
    
    reels = user_query.reels
    details = [{ 'id': reel.id, 'refnumber': reel.refnumber, 'link_media': reel.link_media, 'owner_id': reel.owner_id, 'description': reel.description, 'nb_vue': reel.nb_vue, 'active': reel.active} for reel in reels]
    reels = details
    
    signals = user_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
    
    stories = user_query.stories
    details = [{ 'id': storie.id, 'refnumber': storie.refnumber, 'link_media': storie.link_media, 'owner_id': storie.owner_id, 'description': storie.description, 'nb_vue': storie.nb_vue, 'active': storie.active} for storie in stories]
    stories = details
    
    notes = user_query.notes
    details = [{ 'id': note.id, 'refnumber': note.refnumber, 'owner_id': note.owner_id, 'entertainment_site_id': note.entertainment_site_id, 'note': note.note, 'active': note.active} for note in notes]
    notes = details
    
    return jsonable_encoder(user_query)





# update an user request
@router.put("/update/{user_id}", status_code = status.HTTP_200_OK, response_model = users_schemas.UserDetail)
async def update_user(user_id: str, user_update: users_schemas.UserUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    user_query = db.query(models.User).filter(models.User.id == user_id).first()

    if not user_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} does not exist")
    else:
        
        user_query.updated_by =  current_user.id
        
        if user_update.name:
            user_query.name = user_update.name
        if user_update.surname:
            user_query.surname = user_update.surname
        if user_update.phone:
            user_query.phone = user_update.phone
        if user_update.birthday:
            user_query.birthday = user_update.birthday
        if user_update.gender:
            user_query.gender = user_update.gender
        if user_update.email:
            user_query.email = user_update.email
        if user_update.image:
            user_query.image = user_update.image
        if user_update.username:
            user_query.username = user_update.username
        if user_update.password:
            hashed_password = hash(user_update.password)
            user_update.password = hashed_password
            user_query.password = user_update.password
        if user_update.is_staff:
            user_query.is_staff = user_update.is_staff
        if user_update.is_owner:
            user_query.is_owner = user_update.is_owner
        if user_update.is_annoncer:
            user_query.is_annoncer = user_update.is_annoncer
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(user_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    user_query = db.query(models.User).filter(models.User.id == user_id).first()
    profils = user_query.profils
    details = [{ 'id': profil.id, 'refnumber': profil.refnumber, 'fucntion': profil.fucntion, 'description': profil.description, 'owner_id': profil.owner_id, 'entertainment_site_id': profil.entertainment_site_id, 'active': profil.active} for profil in profils]
    profils = details
    
    entertainment_sites = user_query.entertainment_sites
    details = [{ 'id': entertainment_site.id, 'refnumber': entertainment_site.refnumber, 'name': entertainment_site.name, 'address': entertainment_site.address, 'description': entertainment_site.description, 'longitude': entertainment_site.longitude, 'latitude': entertainment_site.latitude, 'quarter_id': entertainment_site.quarter_id, 'owner_id': entertainment_site.owner_id, 'nb_visite': entertainment_site.nb_visite, 'active': entertainment_site.active} for entertainment_site in entertainment_sites]
    entertainment_sites = details
    
    favorites = user_query.favorites
    details = [{ 'id': favorite.id, 'refnumber': favorite.refnumber, 'owner_id': favorite.owner_id, 'entertainment_site_id': favorite.entertainment_site_id, 'active': favorite.active} for favorite in favorites]
    favorites = details
    
    likes = user_query.likes
    details = [{ 'id': like.id, 'refnumber': like.refnumber, 'owner_id': like.owner_id, 'event_id': like.event_id, 'anounce_id': like.anounce_id, 'reel_id': like.reel_id, 'story_id': like.story_id, 'active': like.active} for like in likes]
    likes = details
    
    reels = user_query.reels
    details = [{ 'id': reel.id, 'refnumber': reel.refnumber, 'link_media': reel.link_media, 'owner_id': reel.owner_id, 'description': reel.description, 'nb_vue': reel.nb_vue, 'active': reel.active} for reel in reels]
    reels = details
    
    signals = user_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
    
    stories = user_query.stories
    details = [{ 'id': storie.id, 'refnumber': storie.refnumber, 'link_media': storie.link_media, 'owner_id': storie.owner_id, 'description': storie.description, 'nb_vue': storie.nb_vue, 'active': storie.active} for storie in stories]
    stories = details
    
    notes = user_query.notes
    details = [{ 'id': note.id, 'refnumber': note.refnumber, 'owner_id': note.owner_id, 'entertainment_site_id': note.entertainment_site_id, 'note': note.note, 'active': note.active} for note in notes]
    notes = details
        
    return jsonable_encoder(user_query)


# delete permission
@router.patch("/delete/{user_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str,  db: Session = Depends(get_db),current_user : str = Depends(oauth2.get_current_user)):
    
    user_query = db.query(models.User).filter(models.User.id == user_id, models.User.active == "True").first()
    
    if not user_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} does not exist")
        
    user_query.active = False
    user_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(user_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "User deleted!"}


# Get all user inactive requests
@router.get("/get_all_inactive/", response_model=List[users_schemas.UserListing])
async def read_users_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    users_queries = db.query(models.User).filter(models.User.active == "False").order_by(models.User.name).offset(skip).limit(limit).all()
                        
    return jsonable_encoder(users_queries)


# Restore user
@router.patch("/restore/{user_id}", status_code = status.HTTP_200_OK,response_model = users_schemas.UserListing)
async def restore_user(user_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    user_query = db.query(models.User).filter(models.User.id == user_id, models.User.active == "False").first()
    
    if not user_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} does not exist")
        
    user_query.active = True
    user_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(user_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(user_query)
