import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import type_products_schemas
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

# /type_products/

router = APIRouter(prefix = "/type_product", tags=['Type products Requests'])
 
# create a new type product sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=type_products_schemas.TypeProductListing)
async def create_type_product(new_type_product_c: type_products_schemas.TypeProductCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.name == new_type_product_c.name).first()
    if  type_product_query:
        raise HTTPException(status_code=403, detail="This type product also exists !")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.TypeProduct).filter(models.TypeProduct.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_type_product_= models.TypeProduct(id = concatenated_uuid, **new_type_product_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_type_product_ )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_type_product_)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_type_product_)

# Get all type products requests
@router.get("/get_all_actif/", response_model=List[type_products_schemas.TypeProductListing])
async def read_type_product_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    type_products_queries = db.query(models.TypeProduct).filter(models.TypeProduct.active == "True").order_by(models.TypeProduct.name).offset(skip).limit(limit).all()
                        
    return jsonable_encoder(type_products_queries)


# Get an type_product
@router.get("/get/{type_product_id}", status_code=status.HTTP_200_OK, response_model=type_products_schemas.TypeProductDetail)
async def detail_type_product(type_product_id: str, db: Session = Depends(get_db)):
    type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.id == type_product_id).first()
    if not type_product_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"type_product with id: {type_product_id} does not exist")
    
    products = type_product_query.products
    details = [{ 'id': product.id, 'refnumber': product.refnumber, 'name': product.name, 'type_product_id': product.type_product_id, 'description': product.description, 'price': product.price, 'active': product.active} for product in products]
    products = details
    
    return jsonable_encoder(type_product_query)


# Get an type_product
# "/get_type_product_impersonal/?name=value_name&description=valeur_description" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_type_product_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[type_products_schemas.TypeProductListing])
async def detail_type_product_by_attribute(name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    type_product_query = {} # objet vide
    if name is not None :
        type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.name.contains(name), models.TypeProduct.active == "True").order_by(models.TypeProduct.name).offset(skip).limit(limit).all()
    if description is not None :
        type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.description.contains(description), models.TypeProduct.active == "True").order_by(models.TypeProduct.name).offset(skip).limit(limit).all()
       
    return jsonable_encoder(type_product_query)



# update an type product request
@router.put("/update/{type_product_id}", status_code = status.HTTP_200_OK, response_model = type_products_schemas.TypeProductDetail)
async def update_type_product(type_product_id: str, type_product_update: type_products_schemas.TypeProductUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.id == type_product_id, models.TypeProduct.active == "True").first()

    if not type_product_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"type_product with id: {type_product_id} does not exist")
    else:
        
        type_product_query.updated_by =  current_user.id
        
        if type_product_update.name:
            type_product_query.name = type_product_update.name
        if type_product_update.description:
            type_product_query.description = type_product_update.description
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(type_product_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.id == type_product_id).first()
    
    products = type_product_query.products
    details = [{ 'id': product.id, 'refnumber': product.refnumber, 'name': product.name, 'type_product_id': product.type_product_id, 'description': product.description, 'price': product.price, 'active': product.active} for product in products]
    products = details
        
    return jsonable_encoder(type_product_query)


# delete type product
@router.patch("/delete/{type_product_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_type_product(type_product_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.id == type_product_id, models.TypeProduct.active == "True").first()
    
    if not type_product_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"family card with id: {type_product_id} does not exist")
        
    type_product_query.active = False
    type_product_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(type_product_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "family card deleted!"}


# Get all type_product inactive requests
@router.get("/get_all_inactive/", response_model=List[type_products_schemas.TypeProductListing])
async def read_type_products_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    type_products_queries = db.query(models.TypeProduct).filter(models.TypeProduct.active == "False", ).order_by(models.TypeProduct.name).offset(skip).limit(limit).all()
                     
    return jsonable_encoder(type_products_queries)


# Restore type_product
@router.patch("/restore/{type_product_id}", status_code = status.HTTP_200_OK,response_model = type_products_schemas.TypeProductListing)
async def restore_type_product(type_product_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    type_product_query = db.query(models.TypeProduct).filter(models.TypeProduct.id == type_product_id, models.TypeProduct.active == "False").first()
    
    if not type_product_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"type_product with id: {type_product_id} does not exist")
        
    type_product_query.active = True
    type_product_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(type_product_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(type_product_query)
