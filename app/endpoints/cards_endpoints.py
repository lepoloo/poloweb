import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import cards_schemas
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

# /Cards/

router = APIRouter(prefix = "/card", tags=['Cards Requests'])
 
# create a new Card sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=cards_schemas.CardListing)
async def create_Card(new_card_c: cards_schemas.CardCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    card_query = db.query(models.Card).filter(models.Card.name == new_card_c.name, models.Card.family_card_id == new_card_c.family_card_id, models.Card.entertainment_site_id == new_card_c.entertainment_site_id).first()
    if  card_query:
        raise HTTPException(status_code=403, detail="This card also exists For this entity !")
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Card).filter(models.Card.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_Card= models.Card(id = concatenated_uuid, **new_card_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_Card )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_Card)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_Card)

# Get all Cards requests
@router.get("/get_all_actif/", response_model=List[cards_schemas.CardListing])
async def read_Cards_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    cards_queries = db.query(models.Card).filter(models.Card.active == "True").order_by(models.Card.name).offset(skip).limit(limit).all()
    
    # pas de Card
    if not cards_queries:
       
        raise HTTPException(status_code=404, detail="Card not found")
                        
    return jsonable_encoder(cards_queries)



# Get an Card
# "/get_Card_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&Cardname=valeur_Cardname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_Card_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[cards_schemas.CardListing])
async def detail_Card_by_attribute(refnumber: Optional[str] = None, family_card_id: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, multimedia: Optional[float] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    card_query = {} # objet vide
    if refnumber is not None :
        card_query = db.query(models.Card).filter(models.Card.refnumber == refnumber, models.Card.active == "True").order_by(models.Card.name).offset(skip).limit(limit).all()
    if name is not None :
        card_query = db.query(models.Card).filter(models.Card.name.contains(name), models.Card.active == "True").order_by(models.Card.name).offset(skip).limit(limit).all()
    if family_card_id is not None :
        card_query = db.query(models.family_card_id).filter(models.Card.family_card_id == family_card_id, models.Card.active == "True").order_by(models.Card.name).offset(skip).limit(limit).all()
    if description is not None:
        card_query = db.query(models.Card).filter(models.Card.description.contains(description), models.Card.active == "True").offset(skip).order_by(models.Card.name).limit(limit).all()
    if multimedia is not None :
        card_query = db.query(models.Card).filter(models.Card.multimedia == multimedia, models.Card.active == "True").offset(skip).order_by(models.Card.name).limit(limit).all()
    
    
    if not card_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Card does not exist")
    return jsonable_encoder(card_query)

# Get an Card
@router.get("/get/{card_id}", status_code=status.HTTP_200_OK, response_model=cards_schemas.CardDetail)
async def detail_Card(card_id: str, db: Session = Depends(get_db)):
    
    card_query = db.query(models.Card).filter(models.Card.id == card_id, models.Card.active == "True").first()
    
    if not card_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Card with id: {card_id} does not exist")
    
    menus = card_query.menus
    details = [{ 'id': menu.id, 'refnumber': menu.refnumber, 'card_id': menu.card_id, 'product_id': menu.product_id, 'price': menu.price, 'active' : menu.active } for menu in menus]
    menus = details
        
    return jsonable_encoder(card_query)





# update an card request
@router.put("/update/{card_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = cards_schemas.CardDetail)
async def update_Card(card_id: str, Card_update: cards_schemas.CardUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    card_query = db.query(models.Card).filter(models.Card.id == card_id, models.Card.active == "True").first()

    if not card_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Card with id: {card_id} does not exist")
    else:
        
        card_query.updated_by =  current_user.id
        
        if Card_update.name:
            card_query.name = Card_update.name
        if Card_update.description:
            card_query.description = Card_update.description
        if Card_update.family_card_id:
            card_query.family_card_id = Card_update.family_card_id
        if Card_update.multimedia:
            card_query.multimedia = Card_update.multimedia
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(card_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(card_query)


# delete card
@router.patch("/delete/{card_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_Card(card_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    card_query = db.query(models.Card).filter(models.Card.id == card_id, models.Card.active == "True").first()
    
    if not card_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Card with id: {card_id} does not exist")
        
    card_query.active = False
    card_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(card_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "Card deleted!"}


# Get all Card inactive requests
@router.get("/get_all_inactive/", response_model=List[cards_schemas.CardListing])
async def read_Cards_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    cards_queries = db.query(models.Card).filter(models.Card.active == "False").order_by(models.Card.name).offset(skip).limit(limit).all()
    
    # pas de Card
    if not cards_queries:
       
        raise HTTPException(status_code=404, detail="Cards not found")
                        
    return jsonable_encoder(cards_queries)


# Restore card
@router.patch("/restore/{card_id}", status_code = status.HTTP_200_OK,response_model = cards_schemas.CardListing)
async def restore_Card(card_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    card_query = db.query(models.Card).filter(models.Card.id == card_id, models.Card.active == "False").first()
    
    if not card_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Card with id: {card_id} does not exist")
        
    card_query.active = True
    card_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(card_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(card_query)
