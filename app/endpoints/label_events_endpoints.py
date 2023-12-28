import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import label_events_schemas
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


# /label_events/

router = APIRouter(prefix = "/label_event", tags=['Labels events Requests'])
 
# create a new permission sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=label_events_schemas.LabelEventListing)
async def create_label_event(new_label_event_c: label_events_schemas.LabelEventCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    label_event_query = db.query(models.LabelEvent).filter(models.LabelEvent.name == new_label_event_c.name).first()
    if  label_event_query:
        raise HTTPException(status_code=403, detail="This label event also exists !")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.LabelEvent).filter(models.LabelEvent.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_label_event_= models.LabelEvent(id = concatenated_uuid, **new_label_event_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_label_event_ )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_label_event_)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_label_event_)

# Get all permissions requests
@router.get("/get_all_actif/", response_model=List[label_events_schemas.LabelEventListing])
async def read_label_event_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    label_events_queries = db.query(models.LabelEvent).filter(models.LabelEvent.active == "True").order_by(models.LabelEvent.name).offset(skip).limit(limit).all()
    
    # pas de label_event
    if not label_events_queries:
       
        raise HTTPException(status_code=404, detail="Type product not found")
                        
    return jsonable_encoder(label_events_queries)


# Get an label_event
@router.get("/get/{label_event_id}", status_code=status.HTTP_200_OK, response_model=label_events_schemas.LabelEventDetail)
async def detail_label_event(label_event_id: str, db: Session = Depends(get_db)):
    label_event_query = db.query(models.LabelEvent).filter(models.LabelEvent.id == label_event_id).first()
    if not label_event_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"label_event with id: {label_event_id} does not exist")
    
    events = label_event_query.events
    details = [{ 'id': event.id, 'refnumber': event.refnumber, 'name': event.name, 'description': event.description, 'label_event_id': event.label_event_id, 'entertainment_site_id': event.entertainment_site_id, 'start_date': event.start_date, 'end_date': event.end_date, 'start_hour': event.start_hour, 'end_hour': event.end_hour, 'nb_visite': event.nb_visite, 'active': event.active} for event in events]
    events = details
    
    return jsonable_encoder(label_event_query)




# Get an label_event
# "/get_label_event_impersonal/?name=value_name&description=valeur_description" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_label_event_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[label_events_schemas.LabelEventListing])
async def detail_label_event_by_attribute(name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    label_event_query = {} # objet vide
    if name is not None :
        label_event_query = db.query(models.LabelEvent).filter(models.LabelEvent.name.contains(name), models.LabelEvent.active == "True").order_by(models.LabelEvent.name).offset(skip).limit(limit).all()
    if description is not None :
        label_event_query = db.query(models.LabelEvent).filter(models.LabelEvent.description.contains(description), models.LabelEvent.active == "True").order_by(models.LabelEvent.name).offset(skip).limit(limit).all()
       
    
    if not label_event_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"label_event does not exist")
    return jsonable_encoder(label_event_query)



# update an permission request
@router.put("/update/{label_event_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = label_events_schemas.LabelEventDetail)
async def update_label_event(label_event_id: str, label_event_update: label_events_schemas.LabelEventUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    label_event_query = db.query(models.LabelEvent).filter(models.LabelEvent.id == label_event_id, models.LabelEvent.active == "True").first()

    if not label_event_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"label_event with id: {label_event_id} does not exist")
    else:
        
        label_event_query.updated_by =  current_user.id
        
        if label_event_update.name:
            label_event_query.name = label_event_update.name
        if label_event_update.description:
            label_event_query.description = label_event_update.description
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(label_event_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(label_event_query)


# delete permission
@router.patch("/delete/{label_event_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_label_event(label_event_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    label_event_query = db.query(models.LabelEvent).filter(models.LabelEvent.id == label_event_id, models.LabelEvent.active == "True").first()
    
    if not label_event_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"family card with id: {label_event_id} does not exist")
        
    label_event_query.active = False
    label_event_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(label_event_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "family card deleted!"}


# Get all label_event inactive requests
@router.get("/get_all_inactive/", response_model=List[label_events_schemas.LabelEventListing])
async def read_label_events_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    label_events_queries = db.query(models.LabelEvent).filter(models.LabelEvent.active == "False").order_by(models.LabelEvent.name).offset(skip).limit(limit).all()
    
    # pas de label_event
    if not label_events_queries:
       
        raise HTTPException(status_code=404, detail="label_events not found")
                        
    return jsonable_encoder(label_events_queries)


# Restore label_event
@router.patch("/restore/{label_event_id}", status_code = status.HTTP_200_OK,response_model = label_events_schemas.LabelEventListing)
async def restore_label_event(label_event_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    label_event_query = db.query(models.LabelEvent).filter(models.LabelEvent.id == label_event_id, models.LabelEvent.active == "False").first()
    
    if not label_event_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"label_event with id: {label_event_id} does not exist")
        
    label_event_query.active = True
    label_event_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(label_event_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(label_event_query)
