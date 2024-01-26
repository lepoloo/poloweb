import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import profils_schemas
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

# /profils/

router = APIRouter(prefix = "/profil", tags=['Profils Requests'])
 
# create a new profil sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=profils_schemas.ProfilListing)
async def create_profil(new_profil_c: profils_schemas.ProfilCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    profil_query = db.query(models.Profil).filter(models.Profil.owner_id == new_profil_c.owner_id, models.Profil.entertainment_site_id == new_profil_c.entertainment_site_id).first()
    if  profil_query:
        raise HTTPException(status_code=403, detail="This profil also exists!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Profil).filter(models.Profil.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_profil= models.Profil(id = concatenated_uuid, **new_profil_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_profil )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_profil)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_profil)

# Get all profils requests
@router.get("/get_all_actif/", response_model=List[profils_schemas.ProfilListing])
async def read_profils_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    profils_queries = db.query(models.Profil).filter(models.Profil.active == "True").order_by(models.Profil.fucntion).offset(skip).limit(limit).all()
    
    # pas de profil
    # if not profils_queries:
    #     raise HTTPException(status_code=404, detail="profil not found")
                        
    return jsonable_encoder(profils_queries)

# Get an profil
@router.get("/get/{profil_id}", status_code=status.HTTP_200_OK, response_model=profils_schemas.ProfilDetail)
async def detail_profil(profil_id: str, db: Session = Depends(get_db)):
    profil_query = db.query(models.Profil).filter(models.Profil.id == profil_id).first()
    if not profil_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil with id: {profil_id} does not exist")
    
    profil_roles = profil_query.profil_roles
    details = [{ 'id': profil_role.id, 'refnumber': profil_role.refnumber, 'profil_id': profil_role.profil_id, 'role_id': profil_role.role_id, 'active': profil_role.active} for profil_role in profil_roles]
    profil_roles = details
    
    profil_privileges = profil_query.profil_privileges
    details = [{ 'id': profil_privilege.id, 'refnumber': profil_privilege.refnumber, 'profil_id': profil_privilege.profil_id, 'privilege_id': profil_privilege.privilege_id, 'active': profil_privilege.active} for profil_privilege in profil_privileges]
    profil_privileges = details
    
    return jsonable_encoder(profil_query)

# Get an profil
# "/get_profil_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&profilname=valeur_profilname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_profil_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[profils_schemas.ProfilListing])
async def detail_profil_by_attribute(refnumber: Optional[str] = None, fucntion: Optional[str] = None, description: Optional[str] = None, owner_id: Optional[str] = None, entertainment_site_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    profil_query = {} # objet vide
    if refnumber is not None :
        profil_query = db.query(models.Profil).filter(models.Profil.refnumber == refnumber, models.Profil.active == "True").order_by(models.Profil.fucntion).offset(skip).limit(limit).all()
    if fucntion is not None :
        profil_query = db.query(models.Profil).filter(models.Profil.fucntion.contains(fucntion), models.Profil.active == "True").order_by(models.Profil.fucntion).offset(skip).limit(limit).all()
    if description is not None :
        profil_query = db.query(models.Profil).filter(models.Profil.description.contains(description), models.Profil.active == "True").order_by(models.Profil.fucntion).offset(skip).limit(limit).all()
    if owner_id is not None :
        profil_query = db.query(models.Profil).filter(models.Profil.owner_id == owner_id, models.Profil.active == "True").offset(skip).order_by(models.Profil.fucntion).limit(limit).all()
    if entertainment_site_id is not None :
        profil_query = db.query(models.Profil).filter(models.Profil.entertainment_site_id == entertainment_site_id, models.Profil.active == "True").order_by(models.Profil.fucntion).offset(skip).limit(limit).all()
    
    
    if not profil_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil does not exist")
    return jsonable_encoder(profil_query)



# update an profil request
@router.put("/update/{profil_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = profils_schemas.ProfilDetail)
async def update_profil(profil_id: str, profil_update: profils_schemas.ProfilUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    profil_query = db.query(models.Profil).filter(models.Profil.id == profil_id, models.Profil.active == "True").first()

    if not profil_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil with id: {profil_id} does not exist")
    else:
        
        profil_query.updated_by =  current_user.id
        
        if profil_update.fucntion:
            profil_query.fucntion = profil_update.fucntion
        if profil_update.description:
            profil_query.description = profil_update.description
        if profil_update.owner_id:
            profil_query.owner_id = profil_update.owner_id
        if profil_update.entertainment_sites_id:
            profil_query.entertainment_sites_id = profil_update.entertainment_sites_id
        
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(profil_query)


# delete profil
@router.patch("/delete/{profil_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_profil(profil_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_query = db.query(models.Profil).filter(models.Profil.id == profil_id, models.Profil.active == "True").first()
    
    if not profil_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil with id: {profil_id} does not exist")
        
    profil_query.active = False
    profil_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "profil deleted!"}


# Get all profil inactive requests
@router.get("/get_all_inactive/", response_model=List[profils_schemas.ProfilListing])
async def read_profils_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profils_queries = db.query(models.Profil).filter(models.Profil.active == "False").order_by(models.Profil.fucntion).offset(skip).limit(limit).all()
    
    # pas de profil
    # if not profils_queries:
    #     raise HTTPException(status_code=404, detail="profils not found")
                        
    return jsonable_encoder(profils_queries)


# Restore profil
@router.patch("/restore/{profil_id}", status_code = status.HTTP_200_OK,response_model = profils_schemas.ProfilListing)
async def restore_profil(profil_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_query = db.query(models.Profil).filter(models.Profil.id == profil_id, models.Profil.active == "False").first()
    
    if not profil_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil with id: {profil_id} does not exist")
        
    profil_query.active = True
    profil_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(profil_query)
