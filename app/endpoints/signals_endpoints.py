import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import signals_schemas
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models import models
import uuid
from datetime import datetime, timedelta
from app.database import engine, get_db
from typing import Optional
from  utils import oauth2

models.Base.metadata.create_all(bind=engine)

# Fonction pour permuter la valeur d'un booléen
def toggle_boolean(value):
    return not value

# /signals/

router = APIRouter(prefix = "/signal", tags=['Signals Requests'])
 
# create signal or dissignal
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=signals_schemas.SignalListing)
async def create_signal(new_signal_c: signals_schemas.SignalCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    if new_signal_c.event_id :
        signals_queries = db.query(models.Signal).filter(models.Signal.owner_id == new_signal_c.owner_id,models.Signal.event_id == new_signal_c.event_id ).first()
    if new_signal_c.anounce_id :
        signals_queries = db.query(models.Signal).filter(models.Signal.owner_id == new_signal_c.owner_id,models.Signal.anounce_id == new_signal_c.anounce_id ).first()
    if new_signal_c.reel_id :
        signals_queries = db.query(models.Signal).filter(models.Signal.owner_id == new_signal_c.owner_id,models.Signal.reel_id == new_signal_c.reel_id ).first()
    if new_signal_c.story_id :
        signals_queries = db.query(models.Signal).filter(models.Signal.owner_id == new_signal_c.owner_id,models.Signal.story_id == new_signal_c.story_id ).first()
    if new_signal_c.entertainment_site_id :
        signals_queries = db.query(models.Signal).filter(models.Signal.owner_id == new_signal_c.owner_id,models.Signal.entertainment_site_id == new_signal_c.entertainment_site_id ).first()
    
    if not signals_queries:
        formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
        concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
        NUM_REF = 10001
        codefin = datetime.now().strftime("%m/%Y")
        concatenated_num_ref = str(
                NUM_REF + len(db.query(models.Signal).filter(models.Signal.refnumber.endswith(codefin)).all())) + "/" + codefin
        
        author = current_user.id
        
        signals_queries= models.Signal(id = concatenated_uuid, **new_signal_c.dict(), refnumber = concatenated_num_ref, created_by = author)
        
        try:
            db.add(signals_queries )# pour ajouter une tuple
            db.commit() # pour faire l'enregistrement
            db.refresh(signals_queries)# pour renvoyer le résultat
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
        
    else:
        
        signals_queries.active = toggle_boolean(signals_queries.active)
        try:
            db.add(signals_queries )# pour ajouter une tuple
            db.commit() # pour faire l'enregistrement
            db.refresh(signals_queries)# pour renvoyer le résultat
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=403, detail="Somthing is wrong in the process, we can't validated your signal!")
    
    return jsonable_encoder(signals_queries)

# Get all signals requests
@router.get("/get_all_actif/", response_model=List[signals_schemas.SignalListing])
async def read_signals_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    signals_queries = db.query(models.Signal).filter(models.Signal.active == "True").order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    
    # pas de signal
    # if not signals_queries:
    #     raise HTTPException(status_code=404, detail="signal not found")
                        
    return jsonable_encoder(signals_queries)



# Get an signal
# "/get_signal_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&signalname=valeur_signalname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_signal_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[signals_schemas.SignalListing])
async def detail_signal_by_attribute(refnumber: Optional[str] = None, event_id: Optional[str] = None, owner_id: Optional[str] = None, anounce_id: Optional[str] = None, reel_id: Optional[str] = None, story_id: Optional[str] = None, entertainment_site_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    signal_query = {} # objet vide
    if refnumber is not None :
        signal_query = db.query(models.Signal).filter(models.Signal.refnumber == refnumber).order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    if owner_id is not None :
        signal_query = db.query(models.Signal).filter(models.Signal.owner_id == owner_id).order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    if event_id is not None :
        signal_query = db.query(models.Signal).filter(models.Signal.event_id == event_id).order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    if anounce_id is not None :
        signal_query = db.query(models.Signal).filter(models.Signal.anounce_id == anounce_id).order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    if reel_id is not None :
        signal_query = db.query(models.Signal).filter(models.Signal.reel_id == reel_id).order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    if story_id is not None :
        signal_query = db.query(models.Signal).filter(models.Signal.story_id == story_id).order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        signal_query = db.query(models.Signal).filter(models.Signal.entertainment_site_id == entertainment_site_id).order_by(models.Signal.create_at).offset(skip).limit(limit).all()
    
    
    if not signal_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"signal does not exist")
    
    return jsonable_encoder(signal_query)

# Get an signal
@router.get("/get/{signal_id}", status_code=status.HTTP_200_OK, response_model=signals_schemas.SignalDetail)
async def detail_signal(signal_id: str, db: Session = Depends(get_db)):
    signal_query = db.query(models.Signal).filter(models.Signal.id == signal_id).first()
    if not signal_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"signal with id: {signal_id} does not exist")
    return jsonable_encoder(signal_query)






