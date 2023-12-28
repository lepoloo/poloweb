import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import menus_schemas
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

# /menus/

router = APIRouter(prefix = "/menu", tags=['Menus Requests'])
 
# create a new menu sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=menus_schemas.MenuListing)
async def create_menu(new_menu_c: menus_schemas.MenuCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    menu_query = db.query(models.Menu).filter(models.Menu.card_id == new_menu_c.card_id, models.Menu.product_id == new_menu_c.product_id).first()
    if  menu_query:
        raise HTTPException(status_code=403, detail="This menu also exists For this card !")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Menu).filter(models.Menu.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_menu= models.Menu(id = concatenated_uuid, **new_menu_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_menu )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_menu)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_menu)

# Get all menus requests
@router.get("/get_all_actif/", response_model=List[menus_schemas.MenuListing])
async def read_menus_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    menus_queries = db.query(models.Menu).filter(models.Menu.active == "True").order_by(models.Menu.card_id).offset(skip).limit(limit).all()
    
    # pas de menu
    if not menus_queries:
       
        raise HTTPException(status_code=404, detail="menu not found")
                        
    return jsonable_encoder(menus_queries)

# Get an menu
@router.get("/get/{menu_id}", status_code=status.HTTP_200_OK, response_model=menus_schemas.MenuDetail)
async def detail_menu(menu_id: str, db: Session = Depends(get_db)):
    menu_query = db.query(models.Menu).filter(models.Menu.id == menu_id, models.Menu.active == "True").first()
    if not menu_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu with id: {menu_id} does not exist")
    return jsonable_encoder(menu_query)

# Get an menu
# "/get_menu_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&menuname=valeur_menuname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_menu_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[menus_schemas.MenuListing])
async def detail_menu_by_attribute(refnumber: Optional[str] = None, product_id: Optional[str] = None, card_id: Optional[str] = None, price: Optional[float] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    menu_query = {} # objet vide
    if refnumber is not None :
        menu_query = db.query(models.Menu).filter(models.Menu.refnumber == refnumber).order_by(models.Menu.card_id).offset(skip).limit(limit).all()
    if card_id is not None :
        menu_query = db.query(models.Menu).filter(models.Menu.card_id == card_id).order_by(models.Menu.card_id).offset(skip).limit(limit).all()
    if product_id is not None :
        menu_query = db.query(models.Menu).filter(models.Menu.product_id == product_id).order_by(models.Menu.card_id).offset(skip).limit(limit).all()
    if price is not None :
        menu_query = db.query(models.Menu).filter(models.Menu.price == price).order_by(models.Menu.card_id).offset(skip).limit(limit).all()
    
    
    if not menu_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"menu does not exist")
    return jsonable_encoder(menu_query)



# update an menu request
@router.put("/update/{menu_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = menus_schemas.MenuDetail)
async def update_menu(menu_id: str, menu_update: menus_schemas.MenuUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    menu_query = db.query(models.Menu).filter(models.Menu.id == menu_id, models.Menu.active == "True").first()

    if not menu_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu with id: {menu_id} does not exist")
    else:
        
        menu_query.updated_by =  current_user.id
        
        if menu_update.product_id:
            menu_query.product_id = menu_update.product_id
        if menu_update.card_id:
            menu_query.card_id = menu_update.card_id
        if menu_update.price:
            menu_query.price = menu_update.price
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(menu_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(menu_query)


# delete menu
@router.patch("/delete/{menu_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_menu(menu_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    menu_query = db.query(models.Menu).filter(models.Menu.id == menu_id, models.Menu.active == "True").first()
    
    if not menu_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu with id: {menu_id} does not exist")
        
    menu_query.active = False
    menu_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(menu_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "menu deleted!"}


# Get all menu inactive requests
@router.get("/get_all_inactive/", response_model=List[menus_schemas.MenuListing])
async def read_menus_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    menus_queries = db.query(models.Menu).filter(models.Menu.active == "False").order_by(models.Menu.card_id).offset(skip).limit(limit).all()
    
    # pas de menu
    if not menus_queries:
        raise HTTPException(status_code=404, detail="menus not found")
                        
    return jsonable_encoder(menus_queries)


# Restore menu
@router.patch("/restore/{menu_id}", status_code = status.HTTP_200_OK,response_model = menus_schemas.MenuListing)
async def restore_menu(menu_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    menu_query = db.query(models.Menu).filter(models.Menu.id == menu_id, models.Menu.active == "False").first()
    
    if not menu_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu with id: {menu_id} does not exist")
        
    menu_query.active = True
    menu_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(menu_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(menu_query)
