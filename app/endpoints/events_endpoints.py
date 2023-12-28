import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import events_schemas
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models import models
import uuid
from datetime import datetime, timedelta
from app.database import engine, get_db
from typing import Optional
from  utils import oauth2
from apscheduler.schedulers.background import BackgroundScheduler

models.Base.metadata.create_all(bind=engine)

# /events/

router = APIRouter(prefix = "/event", tags=['Events Requests'])
 
# create a new event sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=events_schemas.EventListing)
async def create_event(new_event_c: events_schemas.EventCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    event_query = db.query(models.Event).filter(models.Event.label_event_id == new_event_c.label_event_id, models.Event.entertainment_site_id == new_event_c.entertainment_site_id, models.Event.name == new_event_c.name).first()
    if  event_query:
        raise HTTPException(status_code=403, detail="This event also exists !")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Event).filter(models.Event.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_event= models.Event(id = concatenated_uuid, **new_event_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_event )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_event)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_event)

# Get all events requests
@router.get("/get_all_actif/", response_model=List[events_schemas.EventListing])
async def read_events_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    events_queries = db.query(models.Event).filter(models.Event.active == "True").order_by(models.Event.name).offset(skip).limit(limit).all()
    
    # pas de event
    if not events_queries:
       
        raise HTTPException(status_code=404, detail="event not found")
                        
    return jsonable_encoder(events_queries)

# Get an event
@router.get("/get/{event_id}", status_code=status.HTTP_200_OK, response_model=events_schemas.EventDetail)
async def detail_event(event_id: str, db: Session = Depends(get_db)):
    event_query = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event with id: {event_id} does not exist")
    
    event_query.nb_visite = event_query.nb_visite + 1
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(event_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    
    event_multimedias = event_query.event_multimedias
    details = [{ 'id': event_multimedia.id, 'refnumber': event_multimedia.refnumber, 'link_media': event_multimedia.link_media, 'event_id': event_multimedia.event_id, 'active': event_multimedia.active} for event_multimedia in event_multimedias]
    event_multimedias = details
    
    likes = event_query.likes
    details = [{ 'id': like.id, 'refnumber': like.refnumber, 'owner_id': like.owner_id, 'event_id': like.event_id, 'anounce_id': like.anounce_id, 'reel_id': like.reel_id, 'story_id': like.story_id, 'active': like.active} for like in likes]
    likes = details
    
    signals = event_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
        
    return jsonable_encoder(event_query)

# Get an event
# "/get_event_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&eventname=valeur_eventname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_event_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[events_schemas.EventListing])
async def detail_event_by_attribute(refnumber: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, start_date: Optional[datetime] = None,end_date: Optional[datetime] = None,start_hour: Optional[str] = None,end_hour: Optional[str] = None,entertainment_site_id: Optional[str] = None, label_event_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    event_query = {} # objet vide
    if refnumber is not None :
        event_query = db.query(models.Event).filter(models.Event.refnumber == refnumber).order_by(models.Event.name).offset(skip).limit(limit).all()
    if name is not None :
        event_query = db.query(models.Event).filter(models.Event.name.contains(name)).order_by(models.Event.name).offset(skip).limit(limit).all()
    if description is not None :
        event_query = db.query(models.Event).filter(models.Event.description.contains(description)).order_by(models.Event.name).offset(skip).limit(limit).all()
    if start_date is not None :
        event_query = db.query(models.Event).filter(models.Event.start_date == start_date).order_by(models.Event.name).offset(skip).limit(limit).all()
    if end_date is not None :
        event_query = db.query(models.Event).filter(models.Event.end_date == end_date).order_by(models.Event.name).offset(skip).limit(limit).all()
    if start_hour is not None :
        event_query = db.query(models.Event).filter(models.Event.start_hour == start_hour).order_by(models.Event.name).offset(skip).limit(limit).all()
    if end_hour is not None :
        event_query = db.query(models.Event).filter(models.Event.end_hour == end_hour).order_by(models.Event.name).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        event_query = db.query(models.Event).filter(models.Event.entertainment_site_id == entertainment_site_id).order_by(models.Event.name).offset(skip).limit(limit).all()
    if label_event_id is not None :
        event_query = db.query(models.Event).filter(models.Event.label_event_id == label_event_id).order_by(models.Event.name).offset(skip).limit(limit).all()
    
    
    if not event_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event does not exist")
    return jsonable_encoder(event_query)



# update an permission request
@router.put("/update/{event_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = events_schemas.EventDetail)
async def update_event(event_id: str, event_update: events_schemas.EventUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    event_query = db.query(models.Event).filter(models.Event.id == event_id, models.Event.active == "True").first()

    if not event_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event with id: {event_id} does not exist")
    else:
        
        event_query.updated_by =  current_user.id
        
        if event_update.name:
            event_query.name = event_update.name
        if event_update.description:
            event_query.description = event_update.description
        if event_update.label_event_id:
            event_query.label_event_id = event_update.label_event_id
        if event_update.entertainment_site_id:
            event_query.entertainment_site_id = event_update.entertainment_site_id
        if event_update.nb_visite:
            event_query.nb_visite = event_update.nb_visite
        if event_update.start_date:
            event_query.start_date = event_update.start_date
        if event_update.end_date:
            event_query.end_date = event_update.end_date
        if event_update.start_hour:
            event_query.start_hour = event_update.start_hour
        if event_update.end_hour:
            event_query.end_hour = event_update.end_hour
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(event_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(event_query)


# delete permission
@router.patch("/delete/{event_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    event_query = db.query(models.Event).filter(models.Event.id == event_id, models.Event.active == "True").first()
    
    if not event_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event with id: {event_id} does not exist")
        
    event_query.active = False
    event_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(event_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "event deleted!"}


# Get all event inactive requests
@router.get("/get_all_inactive/", response_model=List[events_schemas.EventListing])
async def read_events_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    events_queries = db.query(models.Event).filter(models.Event.active == "False").order_by(models.Event.name).offset(skip).limit(limit).all()
    
    # pas de event
    if not events_queries:
        raise HTTPException(status_code=404, detail="events not found")
                        
    return jsonable_encoder(events_queries)


# Restore permission
@router.patch("/restore/{event_id}", status_code = status.HTTP_200_OK,response_model = events_schemas.EventListing)
async def restore_event(event_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    event_query = db.query(models.Event).filter(models.Event.id == event_id, models.Event.active == "False").first()
    
    if not event_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"event with id: {event_id} does not exist")
        
    event_query.active = True
    event_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(event_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(event_query)


# Déactivation des tâches expirées
# def update_attribute(db: Session = Depends(get_db)):
    
#     # Exemple de mise à jour d'une valeur dans la table
#     formated_date = datetime.now()
#     events_queries = db.query(models.Event).filter(models.Event.active == "True").all()
#     for events_querie in events_queries :
#         if events_querie.end_date < formated_date:
#             events_querie.active = "False"
#             db.commit()
#             db.refresh(events_querie)
    
#     db.close()

# # Configuration de l'ordonnanceur
# scheduler = BackgroundScheduler()
# scheduler.add_job(update_attribute, 'interval', hours=1)
# scheduler.start()

# # Tâche pour arrêter l'ordonnanceur lorsque l'application FastAPI se ferme
# def close_scheduler():
#     scheduler.shutdown()

# router.add_event_handler("shutdown", close_scheduler)
