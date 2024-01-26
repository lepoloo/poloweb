import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import programs_schemas
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from app.models import models
import uuid
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import engine, get_db
from typing import Optional
from  utils import oauth2
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from app.schemas.schedule_times_schemas import ScheduleTimeListing

models.Base.metadata.create_all(bind=engine)

# /programs/

router = APIRouter(prefix = "/program", tags=['Programs Requests'])
 
# create a new program sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=programs_schemas.ProgramListing)
async def create_program(new_program_c: programs_schemas.ProgramCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    program_query = db.query(models.Program).filter(models.Program.name == new_program_c.name, models.Program.entertainment_site_id == new_program_c.entertainment_site_id).first()
    if  program_query:
        raise HTTPException(status_code=403, detail="This Programm also exists for this entertaiment site!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Program).filter(models.Program.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_program= models.Program(id = concatenated_uuid, **new_program_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_program )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_program)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_program)

# Get all programs requests
@router.get("/get_all_actif/", response_model=List[programs_schemas.ProgramListing])
async def read_programs_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    programs_queries = db.query(models.Program).filter(models.Program.active == "True").order_by(models.Program.name).offset(skip).limit(limit).all()
    
    # pas de program
    # if not programs_queries:
    #     raise HTTPException(status_code=404, detail="program not found")
                        
    return jsonable_encoder(programs_queries)



# Get an program
# "/get_program_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&programname=valeur_programname" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_program_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[programs_schemas.ProgramListing])
async def detail_program_by_attribute(refnumber: Optional[str] = None, entertainment_site_id: Optional[str] = None, name: Optional[str] = None, description: Optional[str] = None, price: Optional[float] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    program_query = {} # objet vide
    if refnumber is not None :
        program_query = db.query(models.Program).filter(models.Program.refnumber == refnumber, models.Program.active == "True").order_by(models.Program.name).offset(skip).limit(limit).all()
    if name is not None :
        program_query = db.query(models.Program).filter(models.Program.name.contains(name), models.Program.active == "True").order_by(models.Program.name).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        program_query = db.query(models.Program).filter(models.Program.entertainment_site_id == entertainment_site_id, models.Program.active == "True").order_by(models.Program.name).offset(skip).limit(limit).all()
    if description is not None:
        program_query = db.query(models.Program).filter(models.Program.description.contains(description), models.Program.active == "True").order_by(models.Program.name).offset(skip).limit(limit).all()
    
    
    if not program_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"program does not exist")
    return jsonable_encoder(program_query)

# Get an program
@router.get("/get/{program_id}", status_code=status.HTTP_200_OK, response_model=programs_schemas.ProgramDetail)
async def detail_program(program_id: str, db: Session = Depends(get_db)):
    program_query = db.query(models.Program).filter(models.Program.id == program_id, models.Program.active == "True").first()
    
    if not program_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"program with id: {program_id} does not exist")
    
    schedule_times = program_query.schedule_times
    details = [{ 'id': schedule_time.id, 'refnumber': schedule_time.refnumber, 'daily_day': schedule_time.daily_day, 'program_id': schedule_time.program_id, 'open_hour': schedule_time.open_hour, 'close_hour': schedule_time.close_hour, 'active': schedule_time.active} for schedule_time in schedule_times]
    schedule_times = details
    
    return jsonable_encoder(program_query)





# update an program request
@router.put("/update/{program_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = programs_schemas.ProgramDetail)
async def update_program(program_id: str, program_update: programs_schemas.ProgramUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    program_query = db.query(models.Program).filter(models.Program.id == program_id, models.Program.active == "True").first()

    if not program_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"program with id: {program_id} does not exist")
    else:
        
        program_query.updated_by =  current_user.id
        
        if program_update.name:
            program_query.name = program_update.name
        if program_update.description:
            program_query.description = program_update.description
        if program_update.entertainment_site_id:
            program_query.entertainment_site_id = program_update.entertainment_site_id
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(program_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(program_query)


# delete program
@router.patch("/delete/{program_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_program(program_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    program_query = db.query(models.Program).filter(models.Program.id == program_id, models.Program.active == "True").first()
    
    if not program_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"program with id: {program_id} does not exist")
        
    program_query.active = False
    program_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(program_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "program deleted!"}


# Get all program inactive requests
@router.get("/get_all_inactive/", response_model=List[programs_schemas.ProgramListing])
async def read_programs_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    programs_queries = db.query(models.Program).filter(models.Program.active == "False", ).order_by(models.Program.name).offset(skip).limit(limit).all()
    
    # pas de program
    # if not programs_queries:
    #     raise HTTPException(status_code=404, detail="programs not found")
                        
    return jsonable_encoder(programs_queries)


# Restore program
@router.patch("/restore/{program_id}", status_code = status.HTTP_200_OK,response_model = programs_schemas.ProgramListing)
async def restore_program(program_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    program_query = db.query(models.Program).filter(models.Program.id == program_id, models.Program.active == "False").first()
    
    if not program_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"program with id: {program_id} does not exist")
        
    program_query.active = True
    program_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(program_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(program_query)
