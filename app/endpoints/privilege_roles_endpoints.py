import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import privilege_roles_schemas
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


# /privileges/

router = APIRouter(prefix = "/privilege_role", tags=['Privileges Roles links Requests'])
 
# create a new permission sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=privilege_roles_schemas.PrivilegeRoleListing)
async def create_privilege_role(new_privilege_role_c: privilege_roles_schemas.PrivilegeRoleCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    privilege_role_query = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.role_id == new_privilege_role_c.role_id, models.PrivilegeRole.privilege_id == new_privilege_role_c.privilege_id).first()
    if  privilege_role_query:
        raise HTTPException(status_code=403, detail="This assocition also exists!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.PrivilegeRole).filter(models.PrivilegeRole.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_privilege_role= models.PrivilegeRole(id = concatenated_uuid, **new_privilege_role_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_privilege_role )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_privilege_role)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_privilege_role)

# Get all permissions requests
@router.get("/get_all_actif/", response_model=List[privilege_roles_schemas.PrivilegeRoleListing])
async def read_privilege_role_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    privilege_roles_queries = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.active == "True").order_by(models.PrivilegeRole.created_at).offset(skip).limit(limit).all()
    
    # pas de privilege
    if not privilege_roles_queries:
       
        raise HTTPException(status_code=404, detail="privilege not found")
                        
    return jsonable_encoder(privilege_roles_queries)


# Get an privilege role
@router.get("/get/{privilege_role_id}", status_code=status.HTTP_200_OK, response_model=privilege_roles_schemas.PrivilegeRoleDetail)
async def detail_privilege_role(privilege_role_id: str, db: Session = Depends(get_db)):
    privilege_role_query = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.id == privilege_role_id, models.PrivilegeRole.active == "True").first()
    if not privilege_role_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Privilege role with id: {privilege_role_id} does not exist")
    return jsonable_encoder(privilege_role_query)




# Get an privilege role
# "/get_privilege_role_impersonal/?role_id=value_role_id&privilege_role_id=valeur_privilege_role_id" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_privilege_role_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[privilege_roles_schemas.PrivilegeRoleListing])
async def detail_privilege_role_by_attribute(role_id: Optional[str] = None, privilege_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    privilege_role_query = {} # objet vide
    if role_id is not None :
        privilege_role_query = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.role_id == role_id, models.PrivilegeRole.active == "True").order_by(models.PrivilegeRole.created_at).offset(skip).limit(limit).all()
    if privilege_id is not None :
        privilege_role_query = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.privilege_role_id == privilege_id, models.PrivilegeRole.active == "True").order_by(models.PrivilegeRole.created_at).offset(skip).limit(limit).all()
       
    if not privilege_role_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Privilege role does not exist")
    
    return jsonable_encoder(privilege_role_query)



# update an pivilege role request
@router.put("/update/{privilege_role_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = privilege_roles_schemas.PrivilegeRoleDetail)
async def update_privilege_role(privilege_role_id: str, privilege_role_update: privilege_roles_schemas.PrivilegeRoleUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    privilege_role_query = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.id == privilege_role_id, models.PrivilegeRole.active == "True").first()

    if not privilege_role_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"privilege with id: {privilege_role_id} does not exist")
    else:
        
        privilege_role_query.updated_by =  current_user.id
        
        if privilege_role_update.role_id:
            privilege_role_query.role_id = privilege_role_update.role_id
        if privilege_role_update.privilege_id:
            privilege_role_query.privilege_id = privilege_role_update.privilege_id
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(privilege_role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(privilege_role_query)


# delete privilege role
@router.patch("/delete/{privilege_role_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_privilege_role(privilege_role_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    privilege_role_query = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.id == privilege_role_id, models.PrivilegeRole.active == "True").first()
    
    if not privilege_role_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Privilege role with id: {privilege_role_id} does not exist")
        
    privilege_role_query.active = False
    privilege_role_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(privilege_role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "This role privilege has been deleted!"}


# Get all privilege role inactive requests
@router.get("/get_all_inactive/", response_model=List[privilege_roles_schemas.PrivilegeRoleListing])
async def read_privileges_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    privilege_roles_queries = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.active == "False").order_by(models.PrivilegeRole.created_at).offset(skip).limit(limit).all()
    
    # pas de privilege role
    if not privilege_roles_queries:
       
        raise HTTPException(status_code=404, detail="privileges roles not found")
                        
    return jsonable_encoder(privilege_roles_queries)


# Restore privilege role
@router.patch("/restore/{privilege_role_id}", status_code = status.HTTP_200_OK,response_model = privilege_roles_schemas.PrivilegeRoleListing)
async def restore_privilege(privilege_role_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    privilege_role_query = db.query(models.PrivilegeRole).filter(models.PrivilegeRole.id == privilege_role_id, models.PrivilegeRole.active == "False").first()
    
    if not privilege_role_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Privilege role with id: {privilege_role_id} does not exist")
        
    privilege_role_query.active = True
    privilege_role_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(privilege_role_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(privilege_role_query)
