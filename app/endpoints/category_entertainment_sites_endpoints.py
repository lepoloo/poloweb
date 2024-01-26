import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import category_entertainment_sites_schemas
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

# /category_entertainment_sites/

router = APIRouter(prefix = "/category_entertainment_site", tags=['Category Entertainment Sites Association Requests'])
 
# create a new category_entertainment_site sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=category_entertainment_sites_schemas.CategoryEntertainmentSiteListing)
async def create_category_entertainment_site(new_category_entertainment_site_c: category_entertainment_sites_schemas.CategoryEntertainmentSiteCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.entertainment_site_id == new_category_entertainment_site_c.entertainment_site_id, models.CategoryEntertainmentSite.category_site_id == new_category_entertainment_site_c.category_site_id).first()
    
    if  category_entertainment_site_query:
        raise HTTPException(status_code=403, detail="This association also exists!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_category_entertainment_site= models.CategoryEntertainmentSite(id = concatenated_uuid, **new_category_entertainment_site_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_category_entertainment_site )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_category_entertainment_site)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
        
    
    return jsonable_encoder(new_category_entertainment_site)

# Get all category_entertainment_sites requests
@router.get("/get_all_actif/", response_model=List[category_entertainment_sites_schemas.CategoryEntertainmentSiteListing])
async def read_category_entertainment_sites_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    category_entertainment_sites_queries = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.active == "True").order_by(models.CategoryEntertainmentSite.entertainment_site_id).offset(skip).limit(limit).all()
    
    # pas de category_entertainment_site
    # if not category_entertainment_sites_queries:
    #     raise HTTPException(status_code=404, detail="category_entertainment_site not found")
                        
    return jsonable_encoder(category_entertainment_sites_queries)

# Get an category_entertainment_site
@router.get("/get/{category_entertainment_site_id}", status_code=status.HTTP_200_OK, response_model=category_entertainment_sites_schemas.CategoryEntertainmentSiteDetail)
async def detail_category_entertainment_site(category_entertainment_site_id: str, db: Session = Depends(get_db)):
    category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.id == category_entertainment_site_id).first()
    if not category_entertainment_site_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_entertainment_site with id: {category_entertainment_site_id} does not exist")
    
    
    return jsonable_encoder(category_entertainment_site_query)

# Get an category_entertainment_site
# "/get_category_entertainment_site_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&category_entertainment_sitename=valeur_category_entertainment_sitename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_category_entertainment_site_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[category_entertainment_sites_schemas.CategoryEntertainmentSiteListing])
async def detail_category_entertainment_site_by_attribute(refnumber: Optional[str] = None, category_site_id: Optional[str] = None, entertainment_site_id: Optional[str] = None, price: Optional[float] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    category_entertainment_site_query = {} # objet vide
    if refnumber is not None :
        category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.refnumber == refnumber).order_by(models.CategoryEntertainmentSite.entertainment_site_id).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.entertainment_site_id == entertainment_site_id).order_by(models.CategoryEntertainmentSite.entertainment_site_id).offset(skip).limit(limit).all()
    if category_site_id is not None :
        category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.category_site_id == category_site_id).order_by(models.CategoryEntertainmentSite.entertainment_site_id).offset(skip).limit(limit).all()
    
    
    if not category_entertainment_site_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_entertainment_site does not exist")
    return jsonable_encoder(category_entertainment_site_query)



# update an category_entertainment_site request
@router.put("/update/{category_entertainment_site_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = category_entertainment_sites_schemas.CategoryEntertainmentSiteDetail)
async def update_category_entertainment_site(category_entertainment_site_id: str, category_entertainment_site_update: category_entertainment_sites_schemas.CategoryEntertainmentSiteUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.id == category_entertainment_site_id, models.CategoryEntertainmentSite.active == "True").first()

    if not category_entertainment_site_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_entertainment_site with id: {category_entertainment_site_id} does not exist")
    else:
        
        category_entertainment_site_query.updated_by =  current_user.id
        
        if category_entertainment_site_update.category_site_id:
            category_entertainment_site_query.category_site_id = category_entertainment_site_update.category_site_id
        if category_entertainment_site_update.entertainment_site_id:
            category_entertainment_site_query.entertainment_site_id = category_entertainment_site_update.entertainment_site_id
        if category_entertainment_site_update.price:
            category_entertainment_site_query.price = category_entertainment_site_update.price
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(category_entertainment_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(category_entertainment_site_query)


# delete category_entertainment_site
@router.patch("/delete/{category_entertainment_site_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_category_entertainment_site(category_entertainment_site_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.id == category_entertainment_site_id, models.CategoryEntertainmentSite.active == "True").first()
    
    if not category_entertainment_site_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_entertainment_site with id: {category_entertainment_site_id} does not exist")
        
    category_entertainment_site_query.active = False
    category_entertainment_site_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(category_entertainment_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "category_entertainment_site deleted!"}


# Get all category_entertainment_site inactive requests
@router.get("/get_all_inactive/", response_model=List[category_entertainment_sites_schemas.CategoryEntertainmentSiteListing])
async def read_category_entertainment_sites_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    category_entertainment_sites_queries = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.active == "False").order_by(models.CategoryEntertainmentSite.entertainment_site_id).offset(skip).limit(limit).all()
    
    # pas de category_entertainment_site
    # if not category_entertainment_sites_queries:
    #     raise HTTPException(status_code=404, detail="category_entertainment_sites not found")
                        
    return jsonable_encoder(category_entertainment_sites_queries)


# Restore category_entertainment_site
@router.patch("/restore/{category_entertainment_site_id}", status_code = status.HTTP_200_OK,response_model = category_entertainment_sites_schemas.CategoryEntertainmentSiteListing)
async def restore_category_entertainment_site(category_entertainment_site_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    category_entertainment_site_query = db.query(models.CategoryEntertainmentSite).filter(models.CategoryEntertainmentSite.id == category_entertainment_site_id, models.CategoryEntertainmentSite.active == "False").first()
    
    if not category_entertainment_site_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_entertainment_site with id: {category_entertainment_site_id} does not exist")
        
    category_entertainment_site_query.active = True
    category_entertainment_site_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(category_entertainment_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(category_entertainment_site_query)
