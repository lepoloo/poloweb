import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import schedule_times_schemas
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

# /schedule_times/

router = APIRouter(prefix = "/schedule_time", tags=['Schedules Times Requests'])
 
# create a new schedule_time sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=schedule_times_schemas.ScheduleTimeListing)
async def create_schedule_time(new_schedule_time_c: schedule_times_schemas.ScheduleTimeCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.daily_day == new_schedule_time_c.daily_day, models.ScheduleTime.program_id == new_schedule_time_c.program_id).first()
    
    if  schedule_time_query:
        raise HTTPException(status_code=403, detail="This Schedule time also exists!")
    
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.ScheduleTime).filter(models.ScheduleTime.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_schedule_time_= models.ScheduleTime(id = concatenated_uuid, **new_schedule_time_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_schedule_time_ )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_schedule_time_)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_schedule_time_)

# Get all schedule_time requests
@router.get("/get_all_actif/", response_model=List[schedule_times_schemas.ScheduleTimeListing])
async def read_schedule_time_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    schedule_times_queries = db.query(models.ScheduleTime).filter(models.ScheduleTime.active == "True").order_by(models.ScheduleTime.program_id).offset(skip).limit(limit).all()
    
    # pas de schedule_time
    if not schedule_times_queries:
       
        raise HTTPException(status_code=404, detail="schedule_time not found")
                        
    return jsonable_encoder(schedule_times_queries)


# Get an schedule_time
@router.get("/get/{schedule_time_id}", status_code=status.HTTP_200_OK, response_model=schedule_times_schemas.ScheduleTimeDetail)
async def detail_schedule_time(schedule_time_id: str, db: Session = Depends(get_db)):
    schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.id == schedule_time_id).first()
    if not schedule_time_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"schedule_time with id: {schedule_time_id} does not exist")
    return jsonable_encoder(schedule_time_query)




# Get an schedule_time
# "/get_schedule_time_impersonal/?name=value_name&description=valeur_description" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_schedule_time_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[schedule_times_schemas.ScheduleTimeListing])
async def detail_schedule_time_by_attribute(daily_day: Optional[str] = None, open_hour: Optional[str] = None, close_hour: Optional[str] = None, program_id: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    schedule_time_query = {} # objet vide
    if daily_day is not None :
        schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.daily_day.contains(daily_day), daily_day, models.ScheduleTime.active == "True").order_by(models.ScheduleTime.program_id).offset(skip).limit(limit).all()
    if open_hour is not None :
        schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.open_hour == open_hour, models.ScheduleTime.active == "True").order_by(models.ScheduleTime.program_id).offset(skip).limit(limit).all()
    if close_hour is not None :
        schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.close_hour == close_hour, models.ScheduleTime.active == "True").order_by(models.ScheduleTime.program_id).offset(skip).limit(limit).all()
    if program_id is not None :
        schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.program_id == program_id, models.ScheduleTime.active == "True").order_by(models.ScheduleTime.program_id).offset(skip).limit(limit).all()
       
    
    if not schedule_time_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"schedule_time does not exist")
    return jsonable_encoder(schedule_time_query)



# update an permission request
@router.put("/update/{schedule_time_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = schedule_times_schemas.ScheduleTimeDetail)
async def update_schedule_time(schedule_time_id: str, schedule_time_update: schedule_times_schemas.ScheduleTimeUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.id == schedule_time_id, models.ScheduleTime.active == "True").first()

    if not schedule_time_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"schedule_time with id: {schedule_time_id} does not exist")
    else:
        
        schedule_time_query.updated_by =  current_user.id
        
        if schedule_time_update.daily_day:
            schedule_time_query.daily_day = schedule_time_update.daily_day
        if schedule_time_update.open_hour:
            schedule_time_query.open_hour = schedule_time_update.open_hour
        if schedule_time_update.close_hour:
            schedule_time_query.close_hour = schedule_time_update.close_hour
        if schedule_time_update.program_id:
            schedule_time_query.program_id = schedule_time_update.program_id
        
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(schedule_time_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(schedule_time_query)


# delete permission
@router.patch("/delete/{schedule_time_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_schedule_time(schedule_time_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.id == schedule_time_id, models.ScheduleTime.active == "True").first()
    
    if not schedule_time_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"schedule_time with id: {schedule_time_id} does not exist")
        
    schedule_time_query.active = False
    schedule_time_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(schedule_time_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "schedule_time deleted!"}


# Get all schedule_time inactive requests
@router.get("/get_all_inactive/", response_model=List[schedule_times_schemas.ScheduleTimeListing])
async def read_schedule_times_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    schedule_times_queries = db.query(models.ScheduleTime).filter(models.ScheduleTime.active == "False", ).order_by(models.ScheduleTime.program_id).offset(skip).limit(limit).all()
    
    # pas de schedule_time
    if not schedule_times_queries:
       
        raise HTTPException(status_code=404, detail="schedule_times not found")
                        
    return jsonable_encoder(schedule_times_queries)


# Restore schedule_time
@router.patch("/restore/{schedule_time_id}", status_code = status.HTTP_200_OK,response_model = schedule_times_schemas.ScheduleTimeListing)
async def restore_schedule_time(schedule_time_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    schedule_time_query = db.query(models.ScheduleTime).filter(models.ScheduleTime.id == schedule_time_id, models.ScheduleTime.active == "False").first()
    
    if not schedule_time_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"schedule_time with id: {schedule_time_id} does not exist")
        
    schedule_time_query.active = True
    schedule_time_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(schedule_time_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(schedule_time_query)
