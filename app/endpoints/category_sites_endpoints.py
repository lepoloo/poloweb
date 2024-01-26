import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import category_sites_schemas
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

# /category_sites/

router = APIRouter(prefix = "/category_site", tags=['Category Sites Requests'])
 
# create a new permission sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=category_sites_schemas.CategorySiteListing)
async def create_category_site(new_category_site_c: category_sites_schemas.CategorySiteCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    category_site_query = db.query(models.CategorySite).filter(models.CategorySite.name == new_category_site_c.name).first()
    if  category_site_query:
        raise HTTPException(status_code=403, detail="This category site also exists!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.CategorySite).filter(models.CategorySite.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_category_site_= models.CategorySite(id = concatenated_uuid, **new_category_site_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_category_site_ )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_category_site_)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_category_site_)

# Get all category_sites requests
@router.get("/get_all_actif/", response_model=List[category_sites_schemas.CategorySiteListing])
async def read_category_site_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    category_sites_queries = db.query(models.CategorySite).filter(models.CategorySite.active == "True").order_by(models.CategorySite.name).offset(skip).limit(limit).all()
    
    # pas de category_site
    # if not category_sites_queries:
    #     raise HTTPException(status_code=404, detail="category_site not found")
                        
    return jsonable_encoder(category_sites_queries)


# Get an category_site
@router.get("/get/{category_site_id}", status_code=status.HTTP_200_OK, response_model=category_sites_schemas.CategorySiteDetail)
async def detail_category_site(category_site_id: str, db: Session = Depends(get_db)):
    category_site_query = db.query(models.CategorySite).filter(models.CategorySite.id == category_site_id).first()
    if not category_site_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_site with id: {category_site_id} does not exist")
    
    category_entertainment_sites = category_site_query.category_entertainment_sites
    details = [{ 'id': category_entertainment_site.id, 'refnumber': category_entertainment_site.refnumber, 'entertainment_site_id': category_entertainment_site.entertainment_site_id, 'category_site_id': category_entertainment_site.category_site_id, 'active': category_entertainment_site.active} for category_entertainment_site in category_entertainment_sites]
    category_entertainment_sites = details
    
    return jsonable_encoder(category_site_query)




# Get an category_site
# "/get_category_site_impersonal/?name=value_name&description=valeur_description" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_category_site_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[category_sites_schemas.CategorySiteListing])
async def detail_category_site_by_attribute(name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    category_site_query = {} # objet vide
    if name is not None :
        category_site_query = db.query(models.CategorySite).filter(models.CategorySite.name.contains(name), models.CategorySite.active == "True").order_by(models.CategorySite.name).offset(skip).limit(limit).all()
    if description is not None :
        category_site_query = db.query(models.CategorySite).filter(models.CategorySite.description.contains(description), models.CategorySite.active == "True").order_by(models.CategorySite.name).offset(skip).limit(limit).all()
       
    
    if not category_site_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_site does not exist")
    return jsonable_encoder(category_site_query)



# update an permission request
@router.put("/update/{category_site_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = category_sites_schemas.CategorySiteDetail)
async def update_category_site(category_site_id: str, category_site_update: category_sites_schemas.CategorySiteUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    category_site_query = db.query(models.CategorySite).filter(models.CategorySite.id == category_site_id, models.CategorySite.active == "True").first()

    if not category_site_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_site with id: {category_site_id} does not exist")
    else:
        
        category_site_query.updated_by =  current_user.id
        
        if category_site_update.name:
            category_site_query.name = category_site_update.name
        if category_site_update.description:
            category_site_query.description = category_site_update.description
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(category_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(category_site_query)


# delete permission
@router.patch("/delete/{category_site_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_category_site(category_site_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    category_site_query = db.query(models.CategorySite).filter(models.CategorySite.id == category_site_id, models.CategorySite.active == "True").first()
    
    if not category_site_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_site with id: {category_site_id} does not exist")
        
    category_site_query.active = False
    category_site_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(category_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "category_site deleted!"}


# Get all category_site inactive requests
@router.get("/get_all_inactive/", response_model=List[category_sites_schemas.CategorySiteListing])
async def read_category_sites_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    category_sites_queries = db.query(models.CategorySite).filter(models.CategorySite.active == "False").order_by(models.CategorySite.name).offset(skip).limit(limit).all()
    
    # pas de category_site
    # if not category_sites_queries:
    #     raise HTTPException(status_code=404, detail="category_sites not found")
                        
    return jsonable_encoder(category_sites_queries)


# Restore category_site
@router.patch("/restore/{category_site_id}", status_code = status.HTTP_200_OK,response_model = category_sites_schemas.CategorySiteListing)
async def restore_category_site(category_site_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    category_site_query = db.query(models.CategorySite).filter(models.CategorySite.id == category_site_id, models.CategorySite.active == "False").first()
    
    if not category_site_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"category_site with id: {category_site_id} does not exist")
        
    category_site_query.active = True
    category_site_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(category_site_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(category_site_query)
