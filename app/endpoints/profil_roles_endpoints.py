import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import profil_roles_schemas
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

# /profil_roles/

router = APIRouter(prefix = "/profil_role", tags=['Profils roles Requests'])
 
# create a new profil_role sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=profil_roles_schemas.ProfilRoleListing)
async def create_profil_role(new_profil_role_c: profil_roles_schemas.ProfilRoleCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.profil_id == new_profil_role_c.profil_id, models.ProfilRole.role_id == new_profil_role_c.role_id).first()
    if  profil_role_query:
        raise HTTPException(status_code=403, detail="This profile has also this role!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.ProfilRole).filter(models.ProfilRole.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_profil_role= models.ProfilRole(id = concatenated_uuid, **new_profil_role_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_profil_role )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_profil_role)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_profil_role)

# Get all profil_roles requests
@router.get("/get_all_actif/", response_model=List[profil_roles_schemas.ProfilRoleListing])
async def read_profil_roles_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    profil_roles_queries = db.query(models.ProfilRole).filter(models.ProfilRole.active == "True").order_by(models.ProfilRole.created_at).offset(skip).limit(limit).all()
    
    # pas de profil_role
    # if not profil_roles_queries:
    #     raise HTTPException(status_code=404, detail="profil_role not found")
                        
    return jsonable_encoder(profil_roles_queries)

# Get an profil_role
@router.get("/get/{profil_role_id}", status_code=status.HTTP_200_OK, response_model=profil_roles_schemas.ProfilRoleDetail)
async def detail_profil_role(profil_role_id: str, db: Session = Depends(get_db)):
    profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.id == profil_role_id).first()
    if not profil_role_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_role with id: {profil_role_id} does not exist")
    return jsonable_encoder(profil_role_query)

# Get an profil_role
# "/get_profil_role_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&profil_rolename=valeur_profil_rolename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_profil_role_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[profil_roles_schemas.ProfilRoleListing])
async def detail_profil_role_by_attribute(refnumber: Optional[str] = None, profil_id: Optional[str] = None, role_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    profil_role_query = {} # objet vide
    if refnumber is not None :
        profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.refnumber == refnumber, models.ProfilRole.active == "True").order_by(models.ProfilRole.created_at).offset(skip).limit(limit).all()
    if profil_id is not None :
        profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.profil_id == profil_id, models.ProfilRole.active == "True").order_by(models.ProfilRole.created_at).offset(skip).limit(limit).all()
    if role_id is not None :
        profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.role_id == role_id, models.ProfilRole.active == "True").order_by(models.ProfilRole.created_at).offset(skip).limit(limit).all()
    
    
    if not profil_role_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_role does not exist")
    return jsonable_encoder(profil_role_query)



# update an permission request
@router.put("/update/{profil_role_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = profil_roles_schemas.ProfilRoleDetail)
async def update_profil_role(profil_role_id: str, profil_role_update: profil_roles_schemas.ProfilRoleUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.id == profil_role_id, models.ProfilRole.active == "True").first()

    if not profil_role_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_role with id: {profil_role_id} does not exist")
    else:
        
        profil_role_query.updated_by =  current_user.id
        
        if profil_role_update.profil_id:
            profil_role_query.profil_id = profil_role_update.profil_id
        if profil_role_update.role_id:
            profil_role_query.role_id = profil_role_update.role_id  
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(profil_role_query)


# delete permission
@router.patch("/delete/{profil_role_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_profil_role(profil_role_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.id == profil_role_id, models.ProfilRole.active == "True").first()
    
    if not profil_role_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_role with id: {profil_role_id} does not exist")
        
    profil_role_query.active = False
    profil_role_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "profil_role deleted!"}


# Get all profil_role inactive requests
@router.get("/get_all_inactive/", response_model=List[profil_roles_schemas.ProfilRoleListing])
async def read_profil_roles_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_roles_queries = db.query(models.ProfilRole).filter(models.ProfilRole.active == "False").order_by(models.ProfilRole.created_at).offset(skip).limit(limit).all()
    
    # pas de profil_role
    # if not profil_roles_queries:
    #     raise HTTPException(status_code=404, detail="profil_roles not found")
                        
    return jsonable_encoder(profil_roles_queries)


# Restore permission
@router.patch("/restore/{profil_role_id}", status_code = status.HTTP_200_OK,response_model = profil_roles_schemas.ProfilRoleListing)
async def restore_profil_role(profil_role_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    profil_role_query = db.query(models.ProfilRole).filter(models.ProfilRole.id == profil_role_id, models.ProfilRole.active == "False").first()
    
    if not profil_role_query:  
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"profil_role with id: {profil_role_id} does not exist")
        
    profil_role_query.active = True
    profil_role_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(profil_role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(profil_role_query)
