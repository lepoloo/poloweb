import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import entertainment_sites_schemas
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models import models
from app import config_sething
import random, uuid
from utils.users_utils import send_email
from datetime import datetime, timedelta
from app.database import engine, get_db
from typing import Optional
from  utils import oauth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

models.Base.metadata.create_all(bind=engine)

# /entertainment_sites/

router = APIRouter(prefix = "/entertainment_site", tags=['Entertainment_sites Requests'])
 
# create a new entertainment_site sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=entertainment_sites_schemas.EntertainmentSiteListing)
async def create_entertainment_site(new_entertainment_site_c: entertainment_sites_schemas.EntertainmentSiteCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.name == new_entertainment_site_c.name, models.EntertainmentSite.latitude == new_entertainment_site_c.latitude, models.EntertainmentSite.longitude == new_entertainment_site_c.longitude, models.EntertainmentSite.quarter_id == new_entertainment_site_c.quarter_id).first()
    if  entertainment_site_query:
        raise HTTPException(status_code=403, detail="This entertaiment site also existe!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.EntertainmentSite).filter(models.EntertainmentSite.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_entertainment_site= models.EntertainmentSite(id = concatenated_uuid, **new_entertainment_site_c.dict(), refnumber = concatenated_num_ref,owner_id = author , created_by = author)
    try:
        db.add(new_entertainment_site )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_entertainment_site)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    # envois du mail au compte admin
        to_email = admin_mail
        subject = f"creation of a new entertainment site"
        content = f"réferance site : {concatenated_num_ref}, application_name : {config_sething.project_name},message : Entertaiment site creation request, propritaire : {current_user.name} {current_user.surname} , Username : {current_user.username}, Phone : {current_user.phone}, Email : {current_user.email},operation : Creation Entertainment site. "
        send_email(to_email, subject, content)
    return jsonable_encoder(new_entertainment_site)

# Get all entertainment_sites requests
@router.get("/get_all_actif/", response_model=List[entertainment_sites_schemas.EntertainmentSiteListing])
async def read_entertainment_sites_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    entertainment_sites_queries = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    # print(entertainment_sites_queries.__dict__)
    # pas de entertainment_site
    if not entertainment_sites_queries:
       
        raise HTTPException(status_code=404, detail="entertainment_site not found")
    
                       
    return jsonable_encoder(entertainment_sites_queries)



# Get an entertainment_site
# "/get_entertainment_site_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&entertainment_sitename=valeur_entertainment_sitename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_entertainment_site_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[entertainment_sites_schemas.EntertainmentSiteListing])
async def detail_entertainment_site_by_attribute(refnumber: Optional[str] = None, nb_visite: Optional[int] = None, name: Optional[str] = None, description: Optional[str] = None, address: Optional[str] = None, longitude: Optional[str] = None, latitude: Optional[str] = None, owner_id: Optional[str] = None, quarter_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    entertainment_site_query = {} # objet vide
    if refnumber is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.refnumber == refnumber, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if name is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.name.contains(name), models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if description is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.description.contains(description), models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if nb_visite is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.nb_visite == nb_visite, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if address is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.address == address, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if longitude is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.longitude == longitude, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if latitude is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.latitude == latitude, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if owner_id is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.owner_id == owner_id, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    if quarter_id is not None :
        entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.quarter_id == quarter_id, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    # if category_site_id is not None :
    #     entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.category_site_id == category_site_id, models.EntertainmentSite.active == "True").order_by(models.EntertainmentSite.name).offset(skip).limit(limit).all()
    
    
    if not entertainment_site_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"entertainment_site does not exist")
    return jsonable_encoder(entertainment_site_query)

# Get an entertainment_site
@router.get("/get/{entertainment_site_id}", status_code=status.HTTP_200_OK, response_model=entertainment_sites_schemas.EntertainmentSiteDetail)
async def detail_entertainment_site(entertainment_site_id: str, db: Session = Depends(get_db)):
    entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.id == entertainment_site_id).first()
    if not entertainment_site_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entertainment site  with id: {entertainment_site_id} does not exist")
    
    entertainment_site_query.nb_visite = entertainment_site_query.nb_visite + 1
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(entertainment_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    cards = entertainment_site_query.cards
    details = [{ 'id': card.id, 'refnumber': card.refnumber, 'name': card.name, 'description': card.description, 'family_card_id': card.family_card_id, 'entertainment_site_id': card.entertainment_site_id, 'active': card.active} for card in cards]
    cards = details
    
    reservations = entertainment_site_query.reservations
    details = [{ 'id': reservation.id, 'refnumber': reservation.refnumber, 'date': reservation.date, 'description': reservation.description, 'nb_personne': reservation.nb_personne, 'entertainment_site_id': reservation.entertainment_site_id, 'hour': reservation.hour, 'active': reservation.active} for reservation in reservations]
    reservations = details
    
    comments = entertainment_site_query.comments
    details = [{ 'id': comment.id, 'refnumber': comment.refnumber, 'note': comment.note, 'content': comment.content, 'entertainment_site_id': comment.entertainment_site_id, 'active': comment.active} for comment in comments]
    comments = details
    
    programs = entertainment_site_query.programs
    details = [{ 'id': program.id, 'refnumber': program.refnumber, 'name': program.name, 'description': program.description, 'entertainment_site_id': program.entertainment_site_id, 'active': program.active} for program in programs]
    programs = details
    
    anounces = entertainment_site_query.anounces
    details = [{ 'id': anounce.id, 'refnumber': anounce.refnumber, 'name': anounce.name, 'description': anounce.description, 'entertainment_site_id': anounce.entertainment_site_id, 'duration': anounce.duration, 'end_date': anounce.end_date,'active': anounce.active} for anounce in anounces]
    anounces = details
    
    events = entertainment_site_query.events
    details = [{ 'id': event.id, 'refnumber': event.refnumber, 'name': event.name, 'description': event.description, 'label_event_id': event.label_event_id, 'entertainment_site_id': event.entertainment_site_id, 'start_date': event.start_date, 'end_date': event.end_date, 'start_hour': event.start_hour, 'end_hour': event.end_hour, 'nb_visite': event.nb_visite, 'active': event.active} for event in events]
    events = details
    
    profils = entertainment_site_query.profils
    details = [{ 'id': profil.id, 'refnumber': profil.refnumber, 'fucntion': profil.fucntion, 'description': profil.description, 'owner_id': profil.owner_id, 'entertainment_site_id': profil.entertainment_site_id, 'active': profil.active} for profil in profils]
    profils = details
    
    entertainment_site_multimedias = entertainment_site_query.entertainment_site_multimedias
    details = [{ 'id': entertainment_site_multimedia.id, 'refnumber': entertainment_site_multimedia.refnumber, 'link_media': entertainment_site_multimedia.link_media, 'entertainment_site_id': entertainment_site_multimedia.entertainment_site_id, 'active': entertainment_site_multimedia.active} for entertainment_site_multimedia in entertainment_site_multimedias]
    entertainment_site_multimedias = details
    
    favorites = entertainment_site_query.favorites
    details = [{ 'id': favorite.id, 'refnumber': favorite.refnumber, 'owner_id': favorite.owner_id, 'entertainment_site_id': favorite.entertainment_site_id, 'active': favorite.active} for favorite in favorites]
    favorites = details
    
    category_entertainment_sites = entertainment_site_query.category_entertainment_sites
    details = [{ 'id': category_entertainment_site.id, 'refnumber': category_entertainment_site.refnumber, 'category_site_id': category_entertainment_site.category_site_id, 'entertainment_site_id': category_entertainment_site.entertainment_site_id, 'active': category_entertainment_site.active} for category_entertainment_site in category_entertainment_sites]
    category_entertainment_sites = details
    
    notes = entertainment_site_query.notes
    details = [{ 'id': note.id, 'refnumber': note.refnumber, 'note': note.note, 'owner_id': note.owner_id, 'entertainment_site_id': note.entertainment_site_id, 'active': note.active} for note in notes]
    notes = details
    
    signals = entertainment_site_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
        
    return jsonable_encoder(entertainment_site_query)





# update an entertainment_site request
@router.put("/update/{entertainment_site_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = entertainment_sites_schemas.EntertainmentSiteDetail)
async def update_entertainment_site(entertainment_site_id: str, entertainment_site_update: entertainment_sites_schemas.EntertainmentSiteUpdate, db: Session = Depends(get_db),current_user : str = Depends(oauth2.get_current_user)):
        
    entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.id == entertainment_site_id, models.EntertainmentSite.active == "True").first()

    if not entertainment_site_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entertainment site  with id: {entertainment_site_id} does not exist")
    else:
        
        entertainment_site_query.updated_by =  current_user.id
        
        if entertainment_site_update.name:
            entertainment_site_query.name = entertainment_site_update.name
        if entertainment_site_update.description:
            entertainment_site_query.description = entertainment_site_update.description
        if entertainment_site_update.nb_visite:
            entertainment_site_query.nb_visite = entertainment_site_update.nb_visite
        if entertainment_site_update.address:
            entertainment_site_query.address = entertainment_site_update.address
        if entertainment_site_update.longitude:
            entertainment_site_query.longitude = entertainment_site_update.longitude
        if entertainment_site_update.latitude:
            entertainment_site_query.latitude = entertainment_site_update.latitude
        if entertainment_site_update.owner_id:
            entertainment_site_query.owner_id = entertainment_site_update.owner_id
        if entertainment_site_update.quarter_id:
            entertainment_site_query.quarter_id = entertainment_site_update.quarter_id
        # if entertainment_site_update.category_site_id:
        #     entertainment_site_query.category_site_id = entertainment_site_update.category_site_id
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(entertainment_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(entertainment_site_query)


# delete entertainment_site
@router.patch("/delete/{entertainment_site_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_entertainment_site(entertainment_site_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.id == entertainment_site_id, models.EntertainmentSite.active == "True").first()
    
    if not entertainment_site_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entertainment site  with id: {entertainment_site_id} does not exist")
        
    entertainment_site_query.active = False
    entertainment_site_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(entertainment_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "entertainment_site deleted!"}


# Get all entertainment_site inactive requests
@router.get("/get_all_inactive/", response_model=List[entertainment_sites_schemas.EntertainmentSiteListing])
async def read_entertainment_sites_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    entertainment_sites_queries = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.active == "False").order_by(models.EntertainmentSite.created_at).offset(skip).limit(limit).all()
    
    # pas de entertainment_site
    if not entertainment_sites_queries:
       
        raise HTTPException(status_code=404, detail="entertainment_sites not found")
                        
    return jsonable_encoder(entertainment_sites_queries)


# Restore entertainment_site
@router.patch("/restore/{entertainment_site_id}", status_code = status.HTTP_200_OK,response_model = entertainment_sites_schemas.EntertainmentSiteListing)
async def restore_entertainment_site(entertainment_site_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    entertainment_site_query = db.query(models.EntertainmentSite).filter(models.EntertainmentSite.id == entertainment_site_id, models.EntertainmentSite.active == "False").first()
    
    if not entertainment_site_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entertainment site  with id: {entertainment_site_id} does not exist")
        
    entertainment_site_query.active = True
    entertainment_site_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(entertainment_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(entertainment_site_query)
