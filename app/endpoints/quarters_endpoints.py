import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import quarters_schemas
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

# /quarters/

router = APIRouter(prefix = "/quarter", tags=['Quarters Requests'])
 
# create a new quarter sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=quarters_schemas.QuarterListing)
async def create_quarter(new_quarter_c: quarters_schemas.QuarterCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    quarter_query = db.query(models.Quarter).filter(models.Quarter.name == new_quarter_c.name, models.Quarter.town_id == new_quarter_c.town_id).first()
    if  quarter_query:
        raise HTTPException(status_code=403, detail="This quarter also existe!")
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Quarter).filter(models.Quarter.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_quarter= models.Quarter(id = concatenated_uuid, **new_quarter_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_quarter )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_quarter)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_quarter)

# Get all quarters requests
@router.get("/get_all_actif/", response_model=List[quarters_schemas.QuarterListing])
async def read_quarters_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    quarters_queries = db.query(models.Quarter).filter(models.Quarter.active == "True").order_by(models.Quarter.name).offset(skip).limit(limit).all()
    
                 
    return jsonable_encoder(quarters_queries)



# Get an quarter
# "/get_quarter_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&quartername=valeur_quartername" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_quarter_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[quarters_schemas.QuarterListing])
async def detail_quarter_by_attribute(refnumber: Optional[str] = None, town_id: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, price: Optional[float] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    quarter_query = {} # objet vide
    if refnumber is not None :
        quarter_query = db.query(models.Quarter).filter(models.Quarter.refnumber == refnumber, models.Quarter.active == "True").order_by(models.Quarter.name).offset(skip).limit(limit).all()
    if name is not None :
        quarter_query = db.query(models.Quarter).filter(models.Quarter.name.contains(name), models.Quarter.active == "True").order_by(models.Quarter.name).offset(skip).limit(limit).all()
    if town_id is not None :
        quarter_query = db.query(models.Quarter).filter(models.Quarter.town_id == town_id, models.Quarter.active == "True").order_by(models.Quarter.name).offset(skip).limit(limit).all()
    
    
    if not quarter_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"quarter does not exist")
    return jsonable_encoder(quarter_query)

# Get an quarter
@router.get("/get/{quarter_id}", status_code=status.HTTP_200_OK, response_model=quarters_schemas.QuarterDetail)
async def detail_quarter(quarter_id: str, db: Session = Depends(get_db)):
    quarter_query = db.query(models.Quarter).filter(models.Quarter.id == quarter_id).first()
    if not quarter_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"quarter with id: {quarter_id} does not exist")
    
    entertainment_sites = quarter_query.entertainment_sites
    details = [{ 'id': entertainment_site.id, 'refnumber': entertainment_site.refnumber, 'name': entertainment_site.name, 'description': entertainment_site.description, 'address': entertainment_site.address, 'longitude': entertainment_site.longitude, 'latitude': entertainment_site.latitude, 'quarter_id': entertainment_site.quarter_id, 'owner_id': entertainment_site.owner_id, 'nb_visite': entertainment_site.nb_visite, 'active': entertainment_site.active} for entertainment_site in entertainment_sites]
    entertainment_sites = details
    
    return jsonable_encoder(quarter_query)


# update an quarter request
@router.put("/update/{quarter_id}", status_code = status.HTTP_200_OK, response_model = quarters_schemas.QuarterDetail)
async def update_quarter(quarter_id: str, quarter_update: quarters_schemas.QuarterUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    quarter_query = db.query(models.Quarter).filter(models.Quarter.id == quarter_id).first()

    if not quarter_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"quarter with id: {quarter_id} does not exist")
    else:
        
        quarter_query.updated_by =  current_user.id
        
        if quarter_update.name:
            quarter_query.name = quarter_update.name
        if quarter_update.town_id:
            quarter_query.town_id = quarter_update.town_id
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(quarter_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    quarter_query = db.query(models.Quarter).filter(models.Quarter.id == quarter_id).first()
    entertainment_sites = quarter_query.entertainment_sites
    details = [{ 'id': entertainment_site.id, 'refnumber': entertainment_site.refnumber, 'name': entertainment_site.name, 'description': entertainment_site.description, 'address': entertainment_site.address, 'longitude': entertainment_site.longitude, 'latitude': entertainment_site.latitude, 'quarter_id': entertainment_site.quarter_id, 'owner_id': entertainment_site.owner_id, 'nb_visite': entertainment_site.nb_visite, 'active': entertainment_site.active} for entertainment_site in entertainment_sites]
    entertainment_sites = details
        
    return jsonable_encoder(quarter_query)


# delete quarter
@router.patch("/delete/{quarter_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_quarter(quarter_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    quarter_query = db.query(models.Quarter).filter(models.Quarter.id == quarter_id, models.Quarter.active == "True").first()
    
    if not quarter_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"quarter with id: {quarter_id} does not exist")
        
    quarter_query.active = False
    quarter_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(quarter_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "quarter deleted!"}


# Get all quarter inactive requests
@router.get("/get_all_inactive/", response_model=List[quarters_schemas.QuarterListing])
async def read_quarters_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    quarters_queries = db.query(models.Quarter).filter(models.Quarter.active == "False", ).order_by(models.Quarter.name).offset(skip).limit(limit).all()
                    
    return jsonable_encoder(quarters_queries)


# Restore quarter
@router.patch("/restore/{quarter_id}", status_code = status.HTTP_200_OK,response_model = quarters_schemas.QuarterListing)
async def restore_quarter(quarter_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    quarter_query = db.query(models.Quarter).filter(models.Quarter.id == quarter_id, models.Quarter.active == "False").first()
    
    if not quarter_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"quarter with id: {quarter_id} does not exist")
        
    quarter_query.active = True
    quarter_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(quarter_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(quarter_query)
