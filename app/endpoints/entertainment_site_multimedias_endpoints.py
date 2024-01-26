import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import entertainment_site_multimedias_schemas
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

# /entertainment_site_multimedias/

router = APIRouter(prefix = "/entertainment_site_multimedia", tags=['Entertainment site multimedias Requests'])
 
# create a new entertainment_site_multimedia sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaListing)
async def create_entertainment_site_multimedia(new_entertainment_site_multimedia_c: entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_entertainment_site_multimedia= models.EntertainmentSiteMultimedia(id = concatenated_uuid, **new_entertainment_site_multimedia_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_entertainment_site_multimedia )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_entertainment_site_multimedia)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_entertainment_site_multimedia)

# Get all entertainment_site_multimedias requests
@router.get("/get_all_actif/", response_model=List[entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaListing])
async def read_entertainment_site_multimedias_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    entertainment_site_multimedias_queries = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.active == "True").order_by(models.EntertainmentSiteMultimedia.created_at).offset(skip).limit(limit).all()
    
    # pas de entertainment_site_multimedia
    # if not entertainment_site_multimedias_queries:
    #     raise HTTPException(status_code=404, detail="entertainment_site_multimedia not found")
                        
    return jsonable_encoder(entertainment_site_multimedias_queries)

# Get an entertainment_site_multimedia
@router.get("/get/{entertainment_site_multimedia_id}", status_code=status.HTTP_200_OK, response_model=entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaDetail)
async def detail_entertainment_site_multimedia(entertainment_site_multimedia_id: str, db: Session = Depends(get_db)):
    entertainment_site_multimedia_query = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.id == entertainment_site_multimedia_id).first()
    if not entertainment_site_multimedia_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"entertainment_site_multimedia with id: {entertainment_site_multimedia_id} does not exist")
    return jsonable_encoder(entertainment_site_multimedia_query)

# Get an entertainment_site_multimedia
# "/get_entertainment_site_multimedia_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&entertainment_site_multimedianame=valeur_entertainment_site_multimedianame" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_entertainment_site_multimedia_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaListing])
async def detail_entertainment_site_multimedia_by_attribute(refnumber: Optional[str] = None, link_media: Optional[str] = None, entertainment_site_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    entertainment_site_multimedia_query = {} # objet vide
    if refnumber is not None :
        entertainment_site_multimedia_query = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.refnumber == refnumber, models.EntertainmentSiteMultimedia.active == "True").order_by(models.EntertainmentSiteMultimedia.created_at).offset(skip).limit(limit).all()
    if link_media is not None :
        entertainment_site_multimedia_query = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.link_media.contains(link_media), models.EntertainmentSiteMultimedia.active == "True").order_by(models.EntertainmentSiteMultimedia.created_at).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        entertainment_site_multimedia_query = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.entertainment_site_id == entertainment_site_id, models.EntertainmentSiteMultimedia.active == "True").order_by(models.EntertainmentSiteMultimedia.created_at).offset(skip).limit(limit).all()
    
    
    if not entertainment_site_multimedia_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"entertainment_site_multimedia does not exist")
    return jsonable_encoder(entertainment_site_multimedia_query)



# update an entertainment_site_multimedia request
@router.put("/update/{entertainment_site_multimedia_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaDetail)
async def update_entertainment_site_multimedia(entertainment_site_multimedia_id: str, entertainment_site_multimedia_update: entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    entertainment_site_multimedia_query = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.id == entertainment_site_multimedia_id, models.EntertainmentSiteMultimedia.active == "True").first()

    if not entertainment_site_multimedia_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"entertainment_site_multimedia with id: {entertainment_site_multimedia_id} does not exist")
    else:
        
        entertainment_site_multimedia_query.updated_by =  current_user.id
        
        if entertainment_site_multimedia_update.link_media:
            entertainment_site_multimedia_query.link_media = entertainment_site_multimedia_update.link_media
        if entertainment_site_multimedia_update.entertainment_site_id:
            entertainment_site_multimedia_query.entertainment_site_id = entertainment_site_multimedia_update.entertainment_site_id
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(entertainment_site_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(entertainment_site_multimedia_query)


# delete entertainment_site_multimedia
@router.patch("/delete/{entertainment_site_multimedia_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_entertainment_site_multimedia(entertainment_site_multimedia_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    entertainment_site_multimedia_query = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.id == entertainment_site_multimedia_id, models.EntertainmentSiteMultimedia.active == "True").first()
    
    if not entertainment_site_multimedia_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"entertainment_site_multimedia with id: {entertainment_site_multimedia_id} does not exist")
        
    entertainment_site_multimedia_query.active = False
    entertainment_site_multimedia_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(entertainment_site_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "entertainment_site_multimedia deleted!"}


# Get all entertainment_site_multimedia inactive requests
@router.get("/get_all_inactive/", response_model=List[entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaListing])
async def read_entertainment_site_multimedias_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    entertainment_site_multimedias_queries = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.active == "False").order_by(models.EntertainmentSiteMultimedia.created_at).offset(skip).limit(limit).all()
    
    # pas de entertainment_site_multimedia
    # if not entertainment_site_multimedias_queries:
    #     raise HTTPException(status_code=404, detail="entertainment_site_multimedias not found")
                        
    return jsonable_encoder(entertainment_site_multimedias_queries)


# Restore entertainment_site_multimedia
@router.patch("/restore/{entertainment_site_multimedia_id}", status_code = status.HTTP_200_OK,response_model = entertainment_site_multimedias_schemas.EntertainmentSiteMultimediaListing)
async def restore_entertainment_site_multimedia(entertainment_site_multimedia_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    entertainment_site_multimedia_query = db.query(models.EntertainmentSiteMultimedia).filter(models.EntertainmentSiteMultimedia.id == entertainment_site_multimedia_id, models.EntertainmentSiteMultimedia.active == "False").first()
    
    if not entertainment_site_multimedia_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"entertainment_site_multimedia with id: {entertainment_site_multimedia_id} does not exist")
        
    entertainment_site_multimedia_query.active = True
    entertainment_site_multimedia_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(entertainment_site_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(entertainment_site_multimedia_query)
