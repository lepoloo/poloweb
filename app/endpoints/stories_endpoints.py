import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import stories_schemas
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models import models
from app.endpoints.medias_endpoints import delete_media
import uuid
from datetime import datetime, timedelta
from app.database import engine, get_db
from typing import Optional
from  utils import oauth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

# /stories/

router = APIRouter(prefix = "/storie", tags=['stories Requests'])
 
# create a new storie sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=stories_schemas.StoryListing)
async def create_storie(new_storie_c: stories_schemas.StoryCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Story).filter(models.Story.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    owner_id = current_user.id
    
    new_storie= models.Story(id = concatenated_uuid, **new_storie_c.dict(), refnumber = concatenated_num_ref, owner_id = owner_id, created_by = author)
    
    try:
        db.add(new_storie )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_storie)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_storie)

# Get all stories requests
@router.get("/get_all_actif/", response_model=List[stories_schemas.StoryListing])
async def read_stories_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    stories_queries = db.query(models.Story).filter(models.Story.active == "True", models.Story.created_at < (datetime.now() - timedelta(hours=24))).all()
    # Mettre à jour les enregistrements et changer l'attribut actif à False
    for stories_querie in stories_queries:
        stories_querie.active = False
        try:
            db.commit() # pour faire l'enregistrement
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
        await delete_media(stories_querie.link_media, "reel_medias")
    
    stories_queries = db.query(models.Story).filter(models.Story.active == "True").order_by(models.Story.created_at).offset(skip).limit(limit).all()
    
    # pas de storie
    # if not stories_queries:
    #     raise HTTPException(status_code=404, detail="storie not found")
    
    return jsonable_encoder(stories_queries)



# Get an storie
# "/get_storie_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&storiename=valeur_storiename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_storie_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[stories_schemas.StoryListing])
async def detail_storie_by_attribute(refnumber: Optional[str] = None, owner_id: Optional[str] = None, link_media: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    storie_query = {} # objet vide
    if refnumber is not None :
        storie_query = db.query(models.Story).filter(models.Story.refnumber == refnumber, models.Story.active == "True").order_by(models.Story.created_at).offset(skip).limit(limit).all()
    if link_media is not None :
        storie_query = db.query(models.Story).filter(models.Story.link_media.contains(link_media), models.Story.active == "True").offset(skip).order_by(models.Story.created_at).limit(limit).all()
    if owner_id is not None :
        storie_query = db.query(models.Story).filter(models.Story.owner_id == owner_id, models.Story.active == "True").order_by(models.Story.created_at).offset(skip).limit(limit).all()
    if description is not None:
        storie_query = db.query(models.Story).filter(models.Story.description.contains(description), models.Story.active == "True").order_by(models.Story.created_at).offset(skip).limit(limit).all()
    
    
    if not storie_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"storie does not exist")
    return jsonable_encoder(storie_query)

# Get an storie
@router.get("/get/{storie_id}", status_code=status.HTTP_200_OK, response_model=stories_schemas.StoryDetail)
async def detail_storie(storie_id: str, db: Session = Depends(get_db)):
    storie_query = db.query(models.Story).filter(models.Story.id == storie_id).first()
    if not storie_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"storie with id: {storie_id} does not exist")
    
    storie_query.nb_vue = storie_query.nb_vue + 1
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(storie_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    
    likes = storie_query.likes
    details = [{ 'id': like.id, 'refnumber': like.refnumber, 'owner_id': like.owner_id, 'event_id': like.event_id, 'anounce_id': like.anounce_id, 'reel_id': like.reel_id, 'story_id': like.story_id, 'active': like.active} for like in likes]
    likes = details
    
    signals = storie_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
    
    return jsonable_encoder(storie_query)





# update an storie request
@router.put("/update/{storie_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = stories_schemas.StoryDetail)
async def update_storie(storie_id: str, storie_update: stories_schemas.StoryUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    storie_query = db.query(models.Story).filter(models.Story.id == storie_id, models.Story.active == "True").first()

    if not storie_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"storie with id: {storie_id} does not exist")
    else:
        
        storie_query.updated_by =  current_user.id
        
        if storie_update.link_media:
            storie_query.link_media = storie_update.link_media
        if storie_update.description:
            storie_query.description = storie_update.description
        if storie_update.nb_visite:
            storie_query.nb_visite = storie_update.nb_visite
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(storie_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(storie_query)


# delete storie
@router.patch("/delete/{storie_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_storie(storie_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    storie_query = db.query(models.Story).filter(models.Story.id == storie_id, models.Story.active == "True").first()
    
    if not storie_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"storie with id: {storie_id} does not exist")
        
    storie_query.active = False
    storie_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(storie_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "storie deleted!"}


# Get all storie inactive requests
@router.get("/get_all_inactive/", response_model=List[stories_schemas.StoryListing])
async def read_stories_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user : str = Depends(oauth2.get_current_user)):
    
    stories_queries = db.query(models.Story).filter(models.Story.active == "False").order_by(models.Story.created_at).offset(skip).limit(limit).all()
    
    # pas de storie
    # if not stories_queries:
    #     raise HTTPException(status_code=404, detail="stories not found")
                        
    return jsonable_encoder(stories_queries)


# Restore permission
@router.patch("/restore/{storie_id}", status_code = status.HTTP_200_OK,response_model = stories_schemas.StoryListing)
async def restore_storie(storie_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    storie_query = db.query(models.Story).filter(models.Story.id == storie_id, models.Story.active == "False").first()
    
    if not storie_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"storie with id: {storie_id} does not exist")
        
    storie_query.active = True
    storie_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(storie_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(storie_query)
