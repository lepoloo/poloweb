import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import products_schemas
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

# /products/

router = APIRouter(prefix = "/product", tags=['Products Requests'])
 
# create a new product sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=products_schemas.ProductListing)
async def create_product(new_product_c: products_schemas.ProductCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    product_query = db.query(models.Product).filter(models.Product.name == new_product_c.name, models.Product.type_product_id == new_product_c.type_product_id).first()
    if  product_query:
        raise HTTPException(status_code=403, detail="This association product, type product also exists !")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Product).filter(models.Product.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_product= models.Product(id = concatenated_uuid, **new_product_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_product )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_product)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_product)

# Get all products requests
@router.get("/get_all_actif/", response_model=List[products_schemas.ProductListing])
async def read_products_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    products_queries = db.query(models.Product).filter(models.Product.active == "True").order_by(models.Product.name).offset(skip).limit(limit).all()
                      
    return jsonable_encoder(products_queries)



# Get an product
# "/get_product_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&productname=valeur_productname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_product_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[products_schemas.ProductListing])
async def detail_product_by_attribute(refnumber: Optional[str] = None, type_product_id: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, price: Optional[float] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    product_query = {} # objet vide
    if refnumber is not None :
        product_query = db.query(models.Product).filter(models.Product.refnumber == refnumber, models.Product.active == "True").order_by(models.Product.name).offset(skip).limit(limit).all()
    if name is not None :
        product_query = db.query(models.Product).filter(models.Product.name.contains(name), models.Product.active == "True").order_by(models.Product.name).offset(skip).limit(limit).all()
    if type_product_id is not None :
        product_query = db.query(models.Product).filter(models.Product.type_product_id == type_product_id, models.Product.active == "True").order_by(models.Product.name).offset(skip).limit(limit).all()
    if description is not None:
        product_query = db.query(models.Product).filter(models.Product.description.contains(description), models.Product.active == "True").order_by(models.Product.name).offset(skip).limit(limit).all()
    if price is not None :
        product_query = db.query(models.Product).filter(models.Product.price == price, models.Product.active == "True").order_by(models.Product.name).offset(skip).limit(limit).all()
    
    
    return jsonable_encoder(product_query)

# Get an product
@router.get("/get/{product_id}", status_code=status.HTTP_200_OK, response_model=products_schemas.ProductDetail)
async def detail_product(product_id: str, db: Session = Depends(get_db)):
    product_query = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product with id: {product_id} does not exist")
    
    menus = product_query.menus
    details = [{ 'id': menu.id, 'refnumber': menu.refnumber, 'card_id': menu.card_id, 'product_id': menu.product_id, 'price': menu.price, 'active': menu.active} for menu in menus]
    menus = details
        
    return jsonable_encoder(product_query)



# update an permission request
@router.put("/update/{product_id}", status_code = status.HTTP_200_OK, response_model = products_schemas.ProductDetail)
async def update_product(product_id: str, product_update: products_schemas.ProductUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    product_query = db.query(models.Product).filter(models.Product.id == product_id).first()

    if not product_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product with id: {product_id} does not exist")
    else:
        
        product_query.updated_by =  current_user.id
        
        if product_update.name:
            product_query.name = product_update.name
        if product_update.description:
            product_query.description = product_update.description
        if product_update.price:
            product_query.price = product_update.price
        if product_update.image:
            product_query.image = product_update.image
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(product_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    product_query = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    menus = product_query.menus
    details = [{ 'id': menu.id, 'refnumber': menu.refnumber, 'card_id': menu.card_id, 'product_id': menu.product_id, 'price': menu.price, 'active': menu.active} for menu in menus]
    menus = details    
    
    return jsonable_encoder(product_query)


# delete product
@router.patch("/delete/{product_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    product_query = db.query(models.Product).filter(models.Product.id == product_id, models.Product.active == "True").first()
    
    if not product_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product with id: {product_id} does not exist")
        
    product_query.active = False
    product_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(product_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "product deleted!"}


# Get all product inactive requests
@router.get("/get_all_inactive/", response_model=List[products_schemas.ProductListing])
async def read_products_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    products_queries = db.query(models.Product).filter(models.Product.active == "False", ).order_by(models.Product.name).offset(skip).limit(limit).all()
                       
    return jsonable_encoder(products_queries)


# Restore permission
@router.patch("/restore/{product_id}", status_code = status.HTTP_200_OK,response_model = products_schemas.ProductListing)
async def restore_product(product_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    product_query = db.query(models.Product).filter(models.Product.id == product_id, models.Product.active == "False").first()
    
    if not product_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"product with id: {product_id} does not exist")
        
    product_query.active = True
    product_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(product_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(product_query)
