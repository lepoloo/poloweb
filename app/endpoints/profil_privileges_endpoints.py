import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import profil_privileges_schemas
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

# /profil_privileges/

router = APIRouter(prefix = "/profil_privilege", tags=['Profil privilege Requests'])
 
# create a new profil_privilege sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=profil_privileges_schemas.ProfilPrivilegeListing)
async def create_profil_privilege(new_profil_privilege_c: profil_privileges_schemas.ProfilPrivilegeCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.profil_id == new_profil_privilege_c.profil_id, models.ProfilPrivilege.privilege_id == new_profil_privilege_c.privilege_id).first()
    if  profil_privilege_query:
        raise HTTPException(status_code=403, detail="This profile has also this privilege!")
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_profil_privilege= models.ProfilPrivilege(id = concatenated_uuid, **new_profil_privilege_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_profil_privilege )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_profil_privilege)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_profil_privilege)

# Get all profil_privileges requests
@router.get("/get_all_actif/", response_model=List[profil_privileges_schemas.ProfilPrivilegeListing])
async def read_profil_privileges_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    profil_privileges_queries = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.active == "True").order_by(models.ProfilPrivilege.created_at).offset(skip).limit(limit).all()
    
    # pas de profil_privilege
    if not profil_privileges_queries:
       
        raise HTTPException(status_code=404, detail="profil_privilege not found")
                        
    return jsonable_encoder(profil_privileges_queries)

# Get an profil_privilege
@router.get("/get/{profil_privilege_id}", status_code=status.HTTP_200_OK, response_model=profil_privileges_schemas.ProfilPrivilegeDetail)
async def detail_profil_privilege(profil_privilege_id: str, db: Session = Depends(get_db)):
    profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.id == profil_privilege_id).first()
    if not profil_privilege_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_privilege with id: {profil_privilege_id} does not exist")
    return jsonable_encoder(profil_privilege_query)

# Get an profil_privilege
# "/get_profil_privilege_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&profil_privilegename=valeur_profil_privilegename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_profil_privilege_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[profil_privileges_schemas.ProfilPrivilegeListing])
async def detail_profil_privilege_by_attribute(refnumber: Optional[str] = None, profil_id: Optional[str] = None, privilege_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    profil_privilege_query = {} # objet vide
    if refnumber is not None :
        profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.refnumber == refnumber, models.ProfilPrivilege.active == "True").order_by(models.ProfilPrivilege.created_at).offset(skip).limit(limit).all()
    if profil_id is not None :
        profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.profil_id == profil_id, models.ProfilPrivilege.active == "True").order_by(models.ProfilPrivilege.created_at).offset(skip).limit(limit).all()
    if privilege_id is not None :
        profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.privilege_id == privilege_id, models.ProfilPrivilege.active == "True").order_by(models.ProfilPrivilege.created_at).offset(skip).limit(limit).all()
    
    
    if not profil_privilege_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_privilege does not exist")
    return jsonable_encoder(profil_privilege_query)



# update an profil_privilege  request
@router.put("/update/{profil_privilege_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = profil_privileges_schemas.ProfilPrivilegeDetail)
async def update_profil_privilege(profil_privilege_id: str, profil_privilege_update: profil_privileges_schemas.ProfilPrivilegeUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.id == profil_privilege_id, models.ProfilPrivilege.active == "True").first()

    if not profil_privilege_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_privilege with id: {profil_privilege_id} does not exist")
    else:
        
        profil_privilege_query.updated_by =  current_user.id
        
        if profil_privilege_update.profil_id:
            profil_privilege_query.profil_id = profil_privilege_update.profil_id
        if profil_privilege_update.privilege_id:
            profil_privilege_query.privilege_id = profil_privilege_update.privilege_id  
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_privilege_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(profil_privilege_query)


# delete profil_privilege 
@router.patch("/delete/{profil_privilege_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_profil_privilege(profil_privilege_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.id == profil_privilege_id, models.ProfilPrivilege.active == "True").first()
    
    if not profil_privilege_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_privilege with id: {profil_privilege_id} does not exist")
        
    profil_privilege_query.active = False
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_privilege_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "profil_privilege deleted!"}


# Get all profil_privilege inactive requests
@router.get("/get_all_inactive/", response_model=List[profil_privileges_schemas.ProfilPrivilegeListing])
async def read_profil_privileges_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_privileges_queries = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.active == "False").order_by(models.ProfilPrivilege.created_at).offset(skip).limit(limit).all()
    
    # pas de profil_privilege
    if not profil_privileges_queries:
        raise HTTPException(status_code=404, detail="profil_privileges not found")
                        
    return jsonable_encoder(profil_privileges_queries)


# Restore profil_privilege 
@router.patch("/restore/{profil_privilege_id}", status_code = status.HTTP_200_OK,response_model = profil_privileges_schemas.ProfilPrivilegeListing)
async def restore_profil_privilege(profil_privilege_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_privilege_query = db.query(models.ProfilPrivilege).filter(models.ProfilPrivilege.id == profil_privilege_id, models.ProfilPrivilege.active == "False").first()
    
    if not profil_privilege_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_privilege with id: {profil_privilege_id} does not exist")
        
    profil_privilege_query.active = True
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_privilege_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(profil_privilege_query)
