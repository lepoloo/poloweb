import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import favorites_schemas
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

# Fonction pour permuter la valeur d'un booléen
def toggle_boolean(value):
    return not value

# /favorites/

router = APIRouter(prefix = "/favorite", tags=['Favorites Requests'])
 
# create favorite or disfavorite
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=favorites_schemas.FavoriteListing)
async def create_favorite(new_favorite_c: favorites_schemas.FavoriteCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    favorites_queries = db.query(models.Favorite).filter(models.Favorite.owner_id == new_favorite_c.owner_id,models.Favorite.owner_id == new_favorite_c.owner_id ).all()
    if not favorites_queries:
        formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
        concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
        NUM_REF = 10001
        codefin = datetime.now().strftime("%m/%Y")
        concatenated_num_ref = str(
                NUM_REF + len(db.query(models.Favorite).filter(models.Favorite.refnumber.endswith(codefin)).all())) + "/" + codefin
        
        author = current_user.id
        
        favorites_queries= models.Favorite(id = concatenated_uuid, **new_favorite_c.dict(), refnumber = concatenated_num_ref, created_by = author)
        
        try:
            db.add(favorites_queries )# pour ajouter une tuple
            db.commit() # pour faire l'enregistrement
            db.refresh(favorites_queries)# pour renvoyer le résultat
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
        
    else:
        
        favorites_queries.active = toggle_boolean(favorites_queries.active)
    
    return jsonable_encoder(favorites_queries)

# Get all favorites requests
@router.get("/get_all_actif/", response_model=List[favorites_schemas.FavoriteListing])
async def read_favorites_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    favorites_queries = db.query(models.Favorite).filter(models.Favorite.active == "True").order_by(models.Favorite.created_at).offset(skip).limit(limit).all()
                       
    return jsonable_encoder(favorites_queries)



# Get an favorite
# "/get_favorite_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&favoritename=valeur_favoritename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_favorite_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[favorites_schemas.FavoriteListing])
async def detail_favorite_by_attribute(refnumber: Optional[str] = None, entertainment_site_id: Optional[str] = None, owner_id: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    favorite_query = {} # objet vide
    if refnumber is not None :
        favorite_query = db.query(models.Favorite).filter(models.Favorite.refnumber == refnumber, models.Favorite.active == "True").order_by(models.Favorite.created_at).offset(skip).limit(limit).all()
    if owner_id is not None :
        favorite_query = db.query(models.Favorite).filter(models.Favorite.owner_id == owner_id, models.Favorite.active == "True").order_by(models.Favorite.created_at).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        favorite_query = db.query(models.Favorite).filter(models.Favorite.entertainment_site_id == entertainment_site_id, models.Favorite.active == "True").order_by(models.Favorite.created_at).offset(skip).limit(limit).all()
    
    return jsonable_encoder(favorite_query)

# Get an favorite
@router.get("/get/{favorite_id}", status_code=status.HTTP_200_OK, response_model=favorites_schemas.FavoriteDetail)
async def detail_favorite(favorite_id: str, db: Session = Depends(get_db)):
    favorite_query = db.query(models.Favorite).filter(models.Favorite.id == favorite_id).first()
    if not favorite_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"favorite with id: {favorite_id} does not exist")
    return jsonable_encoder(favorite_query)






