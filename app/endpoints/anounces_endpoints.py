import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import anounces_schemas
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models import models
import uuid
from datetime import datetime, timedelta
from app.database import engine, get_db
from typing import Optional
from  utils import oauth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

# /anounces/

router = APIRouter(prefix = "/anounce", tags=['Anounces Requests'])
 
# create a new anounce sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=anounces_schemas.AnounceListing)
async def create_anounce(new_anounce_c: anounces_schemas.AnounceCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Anounce).filter(models.Anounce.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_anounce= models.Anounce(id = concatenated_uuid, **new_anounce_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_anounce )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_anounce)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_anounce)

# Get all anounces requests
@router.get("/get_all_actif/", response_model=List[anounces_schemas.AnounceListing])
async def read_anounces_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    anounces_queries = db.query(models.Anounce).filter(models.Anounce.active == "True").order_by(models.Anounce.created_at).offset(skip).limit(limit).all()
    
    # pas de anounce
    if not anounces_queries:
       
        raise HTTPException(status_code=404, detail="Anounce not found")
                        
    return jsonable_encoder(anounces_queries)



# Get an anounce
# "/get_anounce_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&anouncename=valeur_anouncename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_anounce_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[anounces_schemas.AnounceListing])
async def detail_anounce_by_attribute(refnumber: Optional[str] = None, entertainment_site_id: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    anounce_query = {} # objet vide
    if refnumber is not None :
        anounce_query = db.query(models.Anounce).filter(models.Anounce.refnumber == refnumber, models.Anounce.active == "True").order_by(models.Anounce.created_at).offset(skip).limit(limit).all()
    if name is not None :
        anounce_query = db.query(models.Anounce).filter(models.Anounce.name.contains(name), models.Anounce.active == "True").offset(skip).order_by(models.Anounce.created_at).limit(limit).all()
    if entertainment_site_id is not None :
        anounce_query = db.query(models.Anounce).filter(models.Anounce.entertainment_site_id == entertainment_site_id, models.Anounce.active == "True").order_by(models.Anounce.created_at).offset(skip).limit(limit).all()
    if description is not None:
        anounce_query = db.query(models.Anounce).filter(models.Anounce.description.contains(description), models.Anounce.active == "True").order_by(models.Anounce.created_at).offset(skip).limit(limit).all()
    
    
    if not anounce_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Anounce does not exist")
    return jsonable_encoder(anounce_query)

# Get an anounce
@router.get("/get/{anounce_id}", status_code=status.HTTP_200_OK, response_model=anounces_schemas.AnounceDetail)
async def detail_anounce(anounce_id: str, db: Session = Depends(get_db)):
    anounce_query = db.query(models.Anounce).filter(models.Anounce.id == anounce_id).first()
    if not anounce_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce with id: {anounce_id} does not exist")
    
    anounce_query.nb_visite = anounce_query.nb_visite + 1
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(anounce_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    anounce_multimedias = anounce_query.anounce_multimedias
    details = [{ 'id': anounce_multimedia.id, 'refnumber': anounce_multimedia.refnumber, 'link_media': anounce_multimedia.link_media, 'anounce_id': anounce_multimedia.anounce_id, 'active': anounce_multimedia.active} for anounce_multimedia in anounce_multimedias]
    anounce_multimedias = details
    
    likes = anounce_query.likes
    details = [{ 'id': like.id, 'refnumber': like.refnumber, 'owner_id': like.owner_id, 'event_id': like.event_id, 'anounce_id': like.anounce_id, 'reel_id': like.reel_id, 'story_id': like.story_id, 'active': like.active} for like in likes]
    likes = details
    
    signals = anounce_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
    
    return jsonable_encoder(anounce_query)



# update an anounce request
@router.put("/update/{anounce_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = anounces_schemas.AnounceDetail)
async def update_anounce(anounce_id: str, anounce_update: anounces_schemas.AnounceUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    anounce_query = db.query(models.Anounce).filter(models.Anounce.id == anounce_id, models.Anounce.active == "True").first()

    if not anounce_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce with id: {anounce_id} does not exist")
    else:
        
        anounce_query.updated_by =  current_user.id
        
        if anounce_update.name:
            anounce_query.name = anounce_update.name
        if anounce_update.description:
            anounce_query.description = anounce_update.description
        if anounce_update.nb_visite:
            anounce_query.nb_visite = anounce_update.nb_visite
        if anounce_update.entertainment_site_id:
            anounce_query.entertainment_site_id = anounce_update.entertainment_site_id
        if anounce_update.duration:
            anounce_query.duration = anounce_update.duration
        if anounce_update.end_date:
            anounce_query.end_date = anounce_update.end_date
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(anounce_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(anounce_query)


# delete anounce
@router.patch("/delete/{anounce_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_anounce(anounce_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    anounce_query = db.query(models.Anounce).filter(models.Anounce.id == anounce_id, models.Anounce.active == "True").first()
    
    if not anounce_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce with id: {anounce_id} does not exist")
        
    anounce_query.active = False
    anounce_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(anounce_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "anounce deleted!"}


# Get all anounce inactive requests
@router.get("/get_all_inactive/", response_model=List[anounces_schemas.AnounceListing])
async def read_anounces_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user : str = Depends(oauth2.get_current_user)):
    
    anounces_queries = db.query(models.Anounce).filter(models.Anounce.active == "False").order_by(models.Anounce.created_at).offset(skip).limit(limit).all()
    
    # pas de anounce
    if not anounces_queries:
       
        raise HTTPException(status_code=404, detail="anounces not found")
                        
    return jsonable_encoder(anounces_queries)


# Restore permission
@router.patch("/restore/{anounce_id}", status_code = status.HTTP_200_OK,response_model = anounces_schemas.AnounceListing)
async def restore_anounce(anounce_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    anounce_query = db.query(models.Anounce).filter(models.Anounce.id == anounce_id, models.Anounce.active == "False").first()
    
    if not anounce_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce with id: {anounce_id} does not exist")
        
    anounce_query.active = True
    anounce_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(anounce_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(anounce_query)
