import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import notes_schemas
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

# /notes/

router = APIRouter(prefix = "/note", tags=['notes Requests'])
 
# create note or disnote
@router.post("/create/", status_code = status.HTTP_201_CREATED)
async def create_note(new_note_c: notes_schemas.NoteCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    notes_queries = db.query(models.Note).filter(models.Note.entertainment_site_id == new_note_c.entertainment_site_id,models.Note.owner_id == new_note_c.owner_id ).first()
    # print(notes_queries.__dict__)
    # print(new_note_c)
    # input("entrer un nombre")
    if notes_queries:
        notes_queries.note = new_note_c.note
        try:
            db.add(notes_queries )# pour ajouter une tuple
            db.commit() # pour faire l'enregistrement
            db.refresh(notes_queries)# pour renvoyer le résultat
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
        
    else:
        formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
        concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
        NUM_REF = 10001
        codefin = datetime.now().strftime("%m/%Y")
        concatenated_num_ref = str(
                NUM_REF + len(db.query(models.Note).filter(models.Note.refnumber.endswith(codefin)).all())) + "/" + codefin
        
        author = current_user.id
        
        notes_queries= models.Note(id = concatenated_uuid, **new_note_c.dict(), refnumber = concatenated_num_ref, created_by = author)
        
        try:
            db.add(notes_queries )# pour ajouter une tuple
            db.commit() # pour faire l'enregistrement
            db.refresh(notes_queries)# pour renvoyer le résultat
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
           
    
    return {"message": "Note save."}

# Get all notes requests
@router.get("/get_all_actif/", response_model=List[notes_schemas.NoteListing])
async def read_notes_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    notes_queries = db.query(models.Note).filter(models.Note.active == "True").order_by(models.Note.entertainment_site_id).offset(skip).limit(limit).all()
    
    # pas de note
    if not notes_queries:
       
        raise HTTPException(status_code=404, detail="note not found")
                        
    return jsonable_encoder(notes_queries)



# Get an note
# "/get_note_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&notename=valeur_notename" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_note_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[notes_schemas.NoteListing])
async def detail_note_by_attribute(refnumber: Optional[str] = None, entertainment_site_id: Optional[str] = None, owner_id: Optional[str] = None, description: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    note_query = {} # objet vide
    if refnumber is not None :
        note_query = db.query(models.Note).filter(models.Note.refnumber == refnumber).order_by(models.Note.entertainment_site_id).offset(skip).limit(limit).all()
    if owner_id is not None :
        note_query = db.query(models.Note).filter(models.Note.owner_id == owner_id).order_by(models.Note.entertainment_site_id).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        note_query = db.query(models.Note).filter(models.Note.entertainment_site_id == entertainment_site_id).order_by(models.Note.entertainment_site_id).offset(skip).limit(limit).all()
    
    
    if not note_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"note does not exist")
    return jsonable_encoder(note_query)

# Get an note
@router.get("/get/{note_id}", status_code=status.HTTP_200_OK, response_model=notes_schemas.NoteDetail)
async def detail_note(note_id: str, db: Session = Depends(get_db)):
    note_query = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"note with id: {note_id} does not exist")
    return jsonable_encoder(note_query)






