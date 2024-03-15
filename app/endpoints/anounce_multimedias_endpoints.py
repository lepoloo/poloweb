import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import anounce_multimedias_schemas
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

# /anounce_multimedias/

router = APIRouter(prefix = "/anounce_multimedia", tags=['Anounce Multimedias Requests'])
 
# create a new anounce_multimedia sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=anounce_multimedias_schemas.AnounceMultimediaListing)
async def create_anounce_multimedia(new_anounce_multimedia_c: anounce_multimedias_schemas.AnounceMultimediaCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_anounce_multimedia= models.AnounceMultimedia(id = concatenated_uuid, **new_anounce_multimedia_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_anounce_multimedia )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_anounce_multimedia)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_anounce_multimedia)

# Get all anounce_multimedias requests
@router.get("/get_all_actif/", response_model=List[anounce_multimedias_schemas.AnounceMultimediaListing])
async def read_anounce_multimedias_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    anounce_multimedias_queries = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.active == "True").order_by(models.AnounceMultimedia.link_media).offset(skip).limit(limit).all()
    
    # pas de anounce_multimedia
    # if not anounce_multimedias_queries:

    #     raise HTTPException(status_code=404, detail="anounce_multimedia not found")
                        
    return jsonable_encoder(anounce_multimedias_queries)


# Get an anounce_multimedia
@router.get("/get/{anounce_multimedia_id}", status_code=status.HTTP_200_OK, response_model=anounce_multimedias_schemas.AnounceMultimediaDetail)
async def detail_anounce_multimedia(anounce_multimedia_id: str, db: Session = Depends(get_db)):
    anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.id == anounce_multimedia_id).first()
    if not anounce_multimedia_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce_multimedia with id: {anounce_multimedia_id} does not exist")
    return jsonable_encoder(anounce_multimedia_query)

# Get an anounce_multimedia
# "/get_anounce_multimedia_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&anounce_multimedianame=valeur_anounce_multimedianame" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_anounce_multimedia_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[anounce_multimedias_schemas.AnounceMultimediaListing])
async def detail_anounce_multimedia_by_attribute(refnumber: Optional[str] = None, link_media: Optional[str] = None, anounce_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    anounce_multimedia_query = {} # objet vide
    if refnumber is not None :
        anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.refnumber == refnumber, models.AnounceMultimedia.active == "True").order_by(models.AnounceMultimedia.link_media).offset(skip).limit(limit).all()
    if link_media is not None :
        # anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.link_media == link_media).order_by(models.AnounceMultimedia.link_media).offset(skip).limit(limit).all()
        anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.link_media.contains(link_media), models.AnounceMultimedia.active == "True").order_by(models.AnounceMultimedia.link_media).offset(skip).limit(limit).all()
        
    if anounce_id is not None :
        anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.anounce_id == anounce_id, models.AnounceMultimedia.active == "True").order_by(models.AnounceMultimedia.link_media).offset(skip).limit(limit).all()
    
    
    return jsonable_encoder(anounce_multimedia_query)



# update an anounce_multimedia request
@router.put("/update/{anounce_multimedia_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = anounce_multimedias_schemas.AnounceMultimediaDetail)
async def update_anounce_multimedia(anounce_multimedia_id: str, anounce_multimedia_update: anounce_multimedias_schemas.AnounceMultimediaUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.id == anounce_multimedia_id, models.AnounceMultimedia.active == "True").first()

    if not anounce_multimedia_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce_multimedia with id: {anounce_multimedia_id} does not exist")
    else:
        
        anounce_multimedia_query.updated_by =  current_user.id
        
        if anounce_multimedia_update.link_media:
            anounce_multimedia_query.link_media = anounce_multimedia_update.link_media
        if anounce_multimedia_update.anounce_id:
            anounce_multimedia_query.anounce_id = anounce_multimedia_update.anounce_id
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(anounce_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(anounce_multimedia_query)


# delete anounce_multimedia
@router.patch("/delete/{anounce_multimedia_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_anounce_multimedia(anounce_multimedia_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.id == anounce_multimedia_id, models.AnounceMultimedia.active == "True").first()
    
    if not anounce_multimedia_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce_multimedia with id: {anounce_multimedia_id} does not exist")
        
    anounce_multimedia_query.active = False
    anounce_multimedia_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(anounce_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "anounce_multimedia deleted!"}


# Get all anounce_multimedia inactive requests
@router.get("/get_all_inactive/", response_model=List[anounce_multimedias_schemas.AnounceMultimediaListing])
async def read_anounce_multimedias_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    anounce_multimedias_queries = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.active == "False", ).order_by(models.AnounceMultimedia.link_media).offset(skip).limit(limit).all()
    
    # pas de anounce_multimedia
    # if not anounce_multimedias_queries:
    #     raise HTTPException(status_code=404, detail="anounce_multimedias not found")
                        
    return jsonable_encoder(anounce_multimedias_queries)


# Restore anounce_multimedia
@router.patch("/restore/{anounce_multimedia_id}", status_code = status.HTTP_200_OK,response_model = anounce_multimedias_schemas.AnounceMultimediaListing)
async def restore_anounce_multimedia(anounce_multimedia_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    anounce_multimedia_query = db.query(models.AnounceMultimedia).filter(models.AnounceMultimedia.id == anounce_multimedia_id, models.AnounceMultimedia.active == "False").first()
    
    if not anounce_multimedia_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"anounce_multimedia with id: {anounce_multimedia_id} does not exist")
        
    anounce_multimedia_query.active = True
    anounce_multimedia_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(anounce_multimedia_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(anounce_multimedia_query)
