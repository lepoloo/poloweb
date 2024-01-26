import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import privileges_schemas
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

router = APIRouter(prefix = "/privilege", tags=['Privileges Requests'])
 
# create a new permission sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=privileges_schemas.PrivilegeListing)
async def create_privilege(new_privilege_c: privileges_schemas.PrivilegeCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    privilege_query = db.query(models.Privilege).filter(models.Privilege.name == new_privilege_c.name).first()
    if  privilege_query:
        raise HTTPException(status_code=403, detail="This privilege also exists!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Privilege).filter(models.Privilege.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_privilege_= models.Privilege(id = concatenated_uuid, **new_privilege_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_privilege_ )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_privilege_)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_privilege_)

# Get all permissions requests
@router.get("/get_all_actif/", response_model=List[privileges_schemas.PrivilegeListing])
async def read_privilege_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    privileges_queries = db.query(models.Privilege).filter(models.Privilege.active == "True").order_by(models.Privilege.name).offset(skip).limit(limit).all()
    
    # pas de privilege
    # if not privileges_queries:
    #     raise HTTPException(status_code=404, detail="privilege not found")
                        
    return jsonable_encoder(privileges_queries)


# Get an privilege
@router.get("/get/{privilege_id}", status_code=status.HTTP_200_OK, response_model=privileges_schemas.PrivilegeDetail)
async def detail_privilege(privilege_id: str, db: Session = Depends(get_db)):
    privilege_query = db.query(models.Privilege).filter(models.Privilege.id == privilege_id).first()
    if not privilege_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"privilege with id: {privilege_id} does not exist")
    
    privilege_roles = privilege_query.privilege_roles
    details = [{ 'id': privilege_role.id, 'refnumber': privilege_role.refnumber, 'privilege_id': privilege_role.privilege_id, 'privilege_id': privilege_role.privilege_id, 'active': privilege_role.active} for privilege_role in privilege_roles]
    privilege_roles = details
    
    profil_privileges = privilege_query.profil_privileges
    details = [{ 'id': profil_privilege.id, 'refnumber': profil_privilege.refnumber, 'profil_id': profil_privilege.profil_id, 'privilege_id': profil_privilege.privilege_id, 'active': profil_privilege.active} for profil_privilege in profil_privileges]
    profil_privileges = details
    
    return jsonable_encoder(privilege_query)




# Get an privilege by attribute
# "/get_privilege_impersonal/?name=value_name&description=valeur_description" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_privilege_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[privileges_schemas.PrivilegeListing])
async def detail_privilege_by_attribute(name: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    privilege_query = {} # objet vide
    if name is not None :
        privilege_query = db.query(models.Privilege).filter(models.Privilege.name.contains(name)).order_by(models.Privilege.name).offset(skip).limit(limit).all()
    if description is not None :
        privilege_query = db.query(models.Privilege).filter(models.Privilege.description.contains(description)).order_by(models.Privilege.name).offset(skip).limit(limit).all()
       
    
    if not privilege_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"privilege does not exist")
    return jsonable_encoder(privilege_query)



# update an permission request
@router.put("/update/{privilege_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = privileges_schemas.PrivilegeDetail)
async def update_privilege(privilege_id: str, privilege_update: privileges_schemas.PrivilegeUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    privilege_query = db.query(models.Privilege).filter(models.Privilege.id == privilege_id, models.Privilege.active == "True").first()

    if not privilege_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"privilege with id: {privilege_id} does not exist")
    else:
        
        privilege_query.updated_by =  current_user.id
        
        if privilege_update.name:
            privilege_query.name = privilege_update.name
        if privilege_update.description:
            privilege_query.description = privilege_update.description
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(privilege_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(privilege_query)


# delete privileges
@router.patch("/delete/{privilege_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_privilege(privilege_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    privilege_query = db.query(models.Privilege).filter(models.Privilege.id == privilege_id, models.Privilege.active == "True").first()
    
    if not privilege_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"privilege with id: {privilege_id} does not exist")
        
    privilege_query.active = False
    privilege_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(privilege_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "privilege deleted!"}


# Get all privilege inactive requests
@router.get("/get_all_inactive/", response_model=List[privileges_schemas.PrivilegeListing])
async def read_privileges_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    privileges_queries = db.query(models.Privilege).filter(models.Privilege.active == "False").order_by(models.Privilege.name).offset(skip).limit(limit).all()
    
    # pas de privilege
    # if not privileges_queries:
    #     raise HTTPException(status_code=404, detail="privileges not found")
                        
    return jsonable_encoder(privileges_queries)


# Restore privilege
@router.patch("/restore/{privilege_id}", status_code = status.HTTP_200_OK,response_model = privileges_schemas.PrivilegeListing)
async def restore_privilege(privilege_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    privilege_query = db.query(models.Privilege).filter(models.Privilege.id == privilege_id, models.Privilege.active == "False").first()
    
    if not privilege_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"privilege with id: {privilege_id} does not exist")
        
    privilege_query.active = True
    privilege_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(privilege_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(privilege_query)
