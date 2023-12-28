import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import event_multimedias_schemas
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

# /event_multimedias/

router = APIRouter(prefix = "/event_multimedia", tags=['Event multimedias Requests'])
 
# create a new event_multimedia sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=event_multimedias_schemas.EventMultimediaListing)
async def create_event_multimedia(new_event_multimedia_c: event_multimedias_schemas.EventMultimediaCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.event_id == new_event_multimedia_c.event_id, models.EventMultimedia.link_media == new_event_multimedia_c.link_media).first()
    if  event_multimedia_query:
        raise HTTPException(status_code=403, detail="This event also the same image !")
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.EventMultimedia).filter(models.EventMultimedia.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_event_multimedia= models.EventMultimedia(id = concatenated_uuid, **new_event_multimedia_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_event_multimedia )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_event_multimedia)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_event_multimedia)

# Get all event_multimedias requests
@router.get("/get_all_actif/", response_model=List[event_multimedias_schemas.EventMultimediaListing])
async def read_event_multimedias_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    event_multimedias_queries = db.query(models.EventMultimedia).filter(models.EventMultimedia.active == "True").order_by(models.EventMultimedia.created_at).offset(skip).limit(limit).all()
    
    # pas de event_multimedia
    if not event_multimedias_queries:
       
        raise HTTPException(status_code=404, detail="event_multimedia not found")
                        
    return jsonable_encoder(event_multimedias_queries)

# Get an event_multimedia
@router.get("/get/{event_multimedia_id}", status_code=status.HTTP_200_OK, response_model=event_multimedias_schemas.EventMultimediaDetail)
async def detail_event_multimedia(event_multimedia_id: str, db: Session = Depends(get_db)):
    event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.id == event_multimedia_id, models.EventMultimedia.active == "True").first()
    if not event_multimedia_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event_multimedia with id: {event_multimedia_id} does not exist")
    return jsonable_encoder(event_multimedia_query)

# Get an event_multimedia
# "/get_event_multimedia_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&event_multimedianame=valeur_event_multimedianame" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_event_multimedia_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[event_multimedias_schemas.EventMultimediaListing])
async def detail_event_multimedia_by_attribute(refnumber: Optional[str] = None, link_media: Optional[str] = None, event_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    event_multimedia_query = {} # objet vide
    if refnumber is not None :
        event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.refnumber == refnumber, models.EventMultimedia.active == "True").order_by(models.EventMultimedia.created_at).offset(skip).limit(limit).all()
    if link_media is not None :
        event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.link_media.contains(link_media), models.EventMultimedia.active == "True").order_by(models.EventMultimedia.created_at).offset(skip).limit(limit).all()
    if event_id is not None :
        event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.event_id == event_id, models.EventMultimedia.active == "True").order_by(models.EventMultimedia.created_at).offset(skip).limit(limit).all()
    
    
    if not event_multimedia_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event_multimedia does not exist")
    return jsonable_encoder(event_multimedia_query)



# update an event_multimedia request
@router.put("/update/{event_multimedia_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = event_multimedias_schemas.EventMultimediaDetail)
async def update_event_multimedia(event_multimedia_id: str, event_multimedia_update: event_multimedias_schemas.EventMultimediaUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.id == event_multimedia_id, models.EventMultimedia.active == "True").first()

    if not event_multimedia_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event_multimedia with id: {event_multimedia_id} does not exist")
    else:
        
        event_multimedia_query.updated_by =  current_user.id
        
        if event_multimedia_update.link_media:
            event_multimedia_query.link_media = event_multimedia_update.link_media
        if event_multimedia_update.event_id:
            event_multimedia_query.event_id = event_multimedia_update.event_id
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(event_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(event_multimedia_query)


# delete event_multimedia
@router.patch("/delete/{event_multimedia_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_event_multimedia(event_multimedia_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.id == event_multimedia_id, models.EventMultimedia.active == "True").first()
    
    if not event_multimedia_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event_multimedia with id: {event_multimedia_id} does not exist")
        
    event_multimedia_query.active = False
    event_multimedia_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(event_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "event_multimedia deleted!"}


# Get all event_multimedia inactive requests
@router.get("/get_all_inactive/", response_model=List[event_multimedias_schemas.EventMultimediaListing])
async def read_event_multimedias_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    event_multimedias_queries = db.query(models.EventMultimedia).filter(models.EventMultimedia.active == "False", ).offset(skip).limit(limit).all()
    
    # pas de event_multimedia
    if not event_multimedias_queries:
        raise HTTPException(status_code=404, detail="event_multimedias not found")
                        
    return jsonable_encoder(event_multimedias_queries)


# Restore event_multimedia
@router.patch("/restore/{event_multimedia_id}", status_code = status.HTTP_200_OK,response_model = event_multimedias_schemas.EventMultimediaListing)
async def restore_event_multimedia(event_multimedia_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    event_multimedia_query = db.query(models.EventMultimedia).filter(models.EventMultimedia.id == event_multimedia_id, models.EventMultimedia.active == "False").first()
    
    if not event_multimedia_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event_multimedia with id: {event_multimedia_id} does not exist")
        
    event_multimedia_query.active = True
    event_multimedia_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(event_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(event_multimedia_query)
