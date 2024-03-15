import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import family_cards_schemas
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

# /family_cards/

router = APIRouter(prefix = "/family_card", tags=['Family_cards Requests'])
 
# create a new permission sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=family_cards_schemas.FamilyCardListing)
async def create_family_card(new_family_card_c: family_cards_schemas.FamilyCardCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.name == new_family_card_c.name).first()
    if  family_card_query:
        raise HTTPException(status_code=403, detail="This family card also exists !")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.FamilyCard).filter(models.FamilyCard.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_family_card_= models.FamilyCard(id = concatenated_uuid, **new_family_card_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_family_card_ )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_family_card_)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_family_card_)

# Get all family_card requests
@router.get("/get_all_actif/", response_model=List[family_cards_schemas.FamilyCardListing])
async def read_family_card_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    family_cards_queries = db.query(models.FamilyCard).filter(models.FamilyCard.active == "True").order_by(models.FamilyCard.name).offset(skip).limit(limit).all()
                       
    return jsonable_encoder(family_cards_queries)


# Get an family_card
@router.get("/get/{family_card_id}", status_code=status.HTTP_200_OK, response_model=family_cards_schemas.FamilyCardDetail)
async def detail_family_card(family_card_id: str, db: Session = Depends(get_db)):
    family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.id == family_card_id).first()
    if not family_card_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"family_card with id: {family_card_id} does not exist")
    
    cards = family_card_query.cards
    for card in cards:
        details = [{ 'id': card.id, 'refnumber': card.refnumber, 'name': card.name, 'family_card_id': card.family_card_id, 'entertainment_site_id': card.entertainment_site_id, 'description': card.description, 'active': card.active} for card in cards]
        cards = details
        
    return jsonable_encoder(family_card_query)


# Get an family_card
# "/get_family_card_impersonal/?name=value_name&description=valeur_description" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_family_card_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[family_cards_schemas.FamilyCardListing])
async def detail_family_card_by_attribute(name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    family_card_query = {} # objet vide
    if name is not None :
        family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.name.contains(name), models.FamilyCard.active == "True").order_by(models.FamilyCard.name).offset(skip).limit(limit).all()
    if description is not None :
        family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.description.contains(description), models.FamilyCard.active == "True").order_by(models.FamilyCard.name).offset(skip).limit(limit).all()
       
    return jsonable_encoder(family_card_query)



# update an family card request
@router.put("/update/{family_card_id}", status_code = status.HTTP_200_OK, response_model = family_cards_schemas.FamilyCardDetail)
async def update_family_card(family_card_id: str, family_card_update: family_cards_schemas.FamilyCardUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.id == family_card_id).first()

    if not family_card_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"family_card with id: {family_card_id} does not exist")
    else:
        
        family_card_query.updated_by =  current_user.id
        
        if family_card_update.name:
            family_card_query.name = family_card_update.name
        if family_card_update.description:
            family_card_query.description = family_card_update.description
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(family_card_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.id == family_card_id).first()
    cards = family_card_query.cards
    for card in cards:
        details = [{ 'id': card.id, 'refnumber': card.refnumber, 'name': card.name, 'family_card_id': card.family_card_id, 'entertainment_site_id': card.entertainment_site_id, 'description': card.description, 'active': card.active} for card in cards]
        cards = details    
    
    return jsonable_encoder(family_card_query)


# delete permission
@router.patch("/delete/{family_card_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_family_card(family_card_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.id == family_card_id, models.FamilyCard.active == "True").first()
    
    if not family_card_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"family card with id: {family_card_id} does not exist")
        
    family_card_query.active = False
    family_card_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(family_card_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "family card deleted!"}


# Get all family_card inactive requests
@router.get("/get_all_inactive/", response_model=List[family_cards_schemas.FamilyCardListing])
async def read_family_cards_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    family_cards_queries = db.query(models.FamilyCard).filter(models.FamilyCard.active == "False").order_by(models.FamilyCard.name).offset(skip).limit(limit).all()
                      
    return jsonable_encoder(family_cards_queries)


# Restore family_card
@router.patch("/restore/{family_card_id}", status_code = status.HTTP_200_OK,response_model = family_cards_schemas.FamilyCardListing)
async def restore_family_card(family_card_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    family_card_query = db.query(models.FamilyCard).filter(models.FamilyCard.id == family_card_id, models.FamilyCard.active == "False").first()
    
    if not family_card_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"family_card with id: {family_card_id} does not exist")
        
    family_card_query.active = True
    family_card_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(family_card_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(family_card_query)
