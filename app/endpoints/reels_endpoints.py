import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import reels_schemas
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

# /reels/

router = APIRouter(prefix = "/reel", tags=['Reels Requests'])
 
# create a new reel sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=reels_schemas.ReelListing)
async def create_reel(new_reel_c: reels_schemas.ReelCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Reel).filter(models.Reel.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    owner_id = current_user.id
    
    new_reel= models.Reel(id = concatenated_uuid, **new_reel_c.dict(), refnumber = concatenated_num_ref, owner_id = owner_id, created_by = author)
    
    try:
        db.add(new_reel )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_reel)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_reel)

# Get all reels requests
@router.get("/get_all_actif/", response_model=List[reels_schemas.ReelListing])
async def read_reels_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    reels_queries = db.query(models.Reel).filter(models.Reel.active == "True", models.Reel.created_at < (datetime.now() - timedelta(hours=24))).all()
    # Mettre à jour les enregistrements et changer l'attribut actif à False
    for reels_querie in reels_queries:
        reels_querie.active = False
        try:
            db.commit() # pour faire l'enregistrement
            # db.refresh()# pour renvoyer le résultat
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
        
        await delete_media(reels_querie.link_media, "reel_medias")
    
    reels_queries = db.query(models.Reel).filter(models.Reel.active == "True").order_by(models.Reel.created_at).offset(skip).limit(limit).all()
    
    # pas de reel
    # if not reels_queries:
    #     raise HTTPException(status_code=404, detail="reel not found")
                        
    return jsonable_encoder(reels_queries)



# Get an reel
# "/get_reel_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&reelname=valeur_reelname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_reel_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[reels_schemas.ReelListing])
async def detail_reel_by_attribute(refnumber: Optional[str] = None, owner_id: Optional[str] = None, link_media: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    reel_query = {} # objet vide
    if refnumber is not None :
        reel_query = db.query(models.Reel).filter(models.Reel.refnumber == refnumber, models.Reel.active == "True").order_by(models.Reel.created_at).offset(skip).limit(limit).all()
    if link_media is not None :
        reel_query = db.query(models.Reel).filter(models.Reel.link_media.contains(link_media), models.Reel.active == "True").offset(skip).order_by(models.Reel.created_at).limit(limit).all()
    if owner_id is not None :
        reel_query = db.query(models.Reel).filter(models.Reel.owner_id == owner_id, models.Reel.active == "True").order_by(models.Reel.created_at).offset(skip).limit(limit).all()
    if description is not None:
        reel_query = db.query(models.Reel).filter(models.Reel.description.contains(description), models.Reel.active == "True").order_by(models.Reel.created_at).offset(skip).limit(limit).all()
    
    
    if not reel_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reel does not exist")
    return jsonable_encoder(reel_query)

# Get an reel
@router.get("/get/{reel_id}", status_code=status.HTTP_200_OK, response_model=reels_schemas.ReelDetail)
async def detail_reel(reel_id: str, db: Session = Depends(get_db)):
    reel_query = db.query(models.Reel).filter(models.Reel.id == reel_id).first()
    if not reel_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reel with id: {reel_id} does not exist")
    
    reel_query.nb_vue = reel_query.nb_vue + 1
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(reel_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    
    likes = reel_query.likes
    details = [{ 'id': like.id, 'refnumber': like.refnumber, 'owner_id': like.owner_id, 'event_id': like.event_id, 'anounce_id': like.anounce_id, 'reel_id': like.reel_id, 'story_id': like.story_id, 'active': like.active} for like in likes]
    likes = details
    
    signals = reel_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
    
    return jsonable_encoder(reel_query)





# update an reel request
@router.put("/update/{reel_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = reels_schemas.ReelDetail)
async def update_reel(reel_id: str, reel_update: reels_schemas.ReelUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    reel_query = db.query(models.Reel).filter(models.Reel.id == reel_id, models.Reel.active == "True").first()

    if not reel_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reel with id: {reel_id} does not exist")
    else:
        
        reel_query.updated_by =  current_user.id
        
        if reel_update.link_media:
            reel_query.link_media = reel_update.link_media
        if reel_update.description:
            reel_query.description = reel_update.description
        if reel_update.nb_visite:
            reel_query.nb_visite = reel_update.nb_visite
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(reel_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(reel_query)


# delete reel
@router.patch("/delete/{reel_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_reel(reel_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    reel_query = db.query(models.Reel).filter(models.Reel.id == reel_id, models.Reel.active == "True").first()
    
    if not reel_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reel with id: {reel_id} does not exist")
        
    reel_query.active = False
    reel_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(reel_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "reel deleted!"}


# Get all reel inactive requests
@router.get("/get_all_inactive/", response_model=List[reels_schemas.ReelListing])
async def read_reels_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user : str = Depends(oauth2.get_current_user)):
    
    reels_queries = db.query(models.Reel).filter(models.Reel.active == "False").order_by(models.Reel.created_at).offset(skip).limit(limit).all()
    
    # pas de reel
    # if not reels_queries:
    #     raise HTTPException(status_code=404, detail="reels not found")
                        
    return jsonable_encoder(reels_queries)


# Restore permission
@router.patch("/restore/{reel_id}", status_code = status.HTTP_200_OK,response_model = reels_schemas.ReelListing)
async def restore_reel(reel_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    reel_query = db.query(models.Reel).filter(models.Reel.id == reel_id, models.Reel.active == "False").first()
    
    if not reel_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reel with id: {reel_id} does not exist")
        
    reel_query.active = True
    reel_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(reel_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(reel_query)
