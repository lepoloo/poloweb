import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import roles_schemas
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

# /roles/

router = APIRouter(prefix = "/role", tags=['Roles Requests'])
 
# create a new permission sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=roles_schemas.RoleListing)
async def create_role(new_role_c: roles_schemas.RoleCreate, db: Session = Depends(get_db),current_user : str = Depends(oauth2.get_current_user)):
    role_query = db.query(models.Role).filter(models.Role.name == new_role_c.name).first()
    if  role_query:
        raise HTTPException(status_code=403, detail="This role also exists!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Role).filter(models.Role.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_role_= models.Role(id = concatenated_uuid, **new_role_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_role_ )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_role_)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_role_)

# Get all permissions requests
@router.get("/get_all_actif/", response_model=List[roles_schemas.RoleListing])
async def read_role_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    roles_queries = db.query(models.Role).filter(models.Role.active == "True").order_by(models.Role.name).offset(skip).limit(limit).all()
                     
    return jsonable_encoder(roles_queries)


# Get an role
@router.get("/get/{role_id}", status_code=status.HTTP_200_OK, response_model=roles_schemas.RoleDetail)
async def detail_role(role_id: str, db: Session = Depends(get_db)):
    role_query = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} does not exist")
    
    profil_roles = role_query.profil_roles
    details = [{ 'id': profil_role.id, 'refnumber': profil_role.refnumber, 'profil_id': profil_role.profil_id, 'role_id': profil_role.role_id, 'active': profil_role.active} for profil_role in profil_roles]
    profil_roles = details
    
    privilege_roles = role_query.privilege_roles
    details = [{ 'id': privilege_role.id, 'refnumber': privilege_role.refnumber, 'privilege_id': privilege_role.privilege_id, 'privilege_id': privilege_role.privilege_id, 'active': privilege_role.active} for privilege_role in privilege_roles]
    privilege_roles = details
    
    return jsonable_encoder(role_query)


# Get an role
# "/get_role_impersonal/?name=value_name&description=valeur_description" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_role_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[roles_schemas.RoleListing])
async def detail_role_by_attribute(name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    role_query = {} # objet vide
    if name is not None :
        role_query = db.query(models.Role).filter(models.Role.name.contains(name), models.Role.active == "True").order_by(models.Role.name).offset(skip).limit(limit).all()
    if description is not None :
        role_query = db.query(models.Role).filter(models.Role.description.contains(description), models.Role.active == "True").order_by(models.Role.name).offset(skip).limit(limit).all()
       
    
    return jsonable_encoder(role_query)



# update an permission request
@router.put("/update/{role_id}", status_code = status.HTTP_200_OK, response_model = roles_schemas.RoleDetail)
async def update_role(role_id: str, role_update: roles_schemas.RoleUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    role_query = db.query(models.Role).filter(models.Role.id == role_id).first()

    if not role_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} does not exist")
    else:
        
        role_query.updated_by =  current_user.id
        
        if role_update.name:
            role_query.name = role_update.name
        if role_update.description:
            role_query.description = role_update.description
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
    
    role_query = db.query(models.Role).filter(models.Role.id == role_id).first()
    profil_roles = role_query.profil_roles
    details = [{ 'id': profil_role.id, 'refnumber': profil_role.refnumber, 'profil_id': profil_role.profil_id, 'role_id': profil_role.role_id, 'active': profil_role.active} for profil_role in profil_roles]
    profil_roles = details
    
    privilege_roles = role_query.privilege_roles
    details = [{ 'id': privilege_role.id, 'refnumber': privilege_role.refnumber, 'privilege_id': privilege_role.privilege_id, 'privilege_id': privilege_role.privilege_id, 'active': privilege_role.active} for privilege_role in privilege_roles]
    privilege_roles = details    
    
    return jsonable_encoder(role_query)


# delete permission
@router.patch("/delete/{role_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    role_query = db.query(models.Role).filter(models.Role.id == role_id, models.Role.active == "True").first()
    
    if not role_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} does not exist")
        
    role_query.active = False
    role_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "role deleted!"}


# Get all role inactive requests
@router.get("/get_all_inactive/", response_model=List[roles_schemas.RoleListing])
async def read_roles_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    roles_queries = db.query(models.Role).filter(models.Role.active == "False").order_by(models.Role.name).offset(skip).limit(limit).all()
                      
    return jsonable_encoder(roles_queries)


# Restore role
@router.patch("/restore/{role_id}", status_code = status.HTTP_200_OK,response_model = roles_schemas.RoleListing)
async def restore_role(role_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    role_query = db.query(models.Role).filter(models.Role.id == role_id, models.Role.active == "False").first()
    
    if not role_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Role with id: {role_id} does not exist")
        
    role_query.active = True
    role_query.updated_by =  current_user.id    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(role_query)
