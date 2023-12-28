import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import comments_schemas
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

# /comments/

router = APIRouter(prefix = "/comment", tags=['Comments Requests'])
 
# create a new comment sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=comments_schemas.CommentListing)
async def create_comment(new_comment_c: comments_schemas.CommentCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Comment).filter(models.Comment.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    author = current_user.id
    
    new_comment= models.Comment(id = concatenated_uuid, **new_comment_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_comment )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_comment)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_comment)

# Get all comments requests
@router.get("/get_all_actif/", response_model=List[comments_schemas.CommentListing])
async def read_comments_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    
    comments_queries = db.query(models.Comment).filter(models.Comment.active == "True").order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    
    # pas de comment
    if not comments_queries:
       
        raise HTTPException(status_code=404, detail="comment not found")
                        
    return jsonable_encoder(comments_queries)



# Get an comment
# "/get_comment_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&commentnote=valeur_commentnote" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_comment_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[comments_schemas.CommentListing])
async def detail_comment_by_attribute(refnumber: Optional[str] = None, entertainment_site_id: Optional[str] = None, note: Optional[str] = None, content: Optional[str] = None, nb_personne: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    comment_query = {} # objet vide
    if refnumber is not None :
        comment_query = db.query(models.Comment).filter(models.Comment.refnumber == refnumber, models.Comment.active == "True").order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    if note is not None :
        comment_query = db.query(models.Comment).filter(models.Comment.note == note, models.Comment.active == "True").order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        comment_query = db.query(models.Comment).filter(models.Comment.entertainment_site_id == entertainment_site_id, models.Comment.active == "True").order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    if content is not None:
        comment_query = db.query(models.Comment).filter(models.Comment.content.contains(content), models.Comment.active == "True").order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    
    
    
    if not comment_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"comment does not exist")
    return jsonable_encoder(comment_query)

# Get an comment
@router.get("/get/{comment_id}", status_code=status.HTTP_200_OK, response_model=comments_schemas.CommentDetail)
async def detail_comment(comment_id: str, db: Session = Depends(get_db)):
    comment_query = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"comment with id: {comment_id} does not exist")
    return jsonable_encoder(comment_query)





# update an comment request
@router.put("/update/{comment_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = comments_schemas.CommentDetail)
async def update_comment(comment_id: str, comment_update: comments_schemas.CommentUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    comment_query = db.query(models.Comment).filter(models.Comment.id == comment_id, models.Comment.active == "True").first()

    if not comment_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"comment with id: {comment_id} does not exist")
    else:
        
        comment_query.updated_by =  current_user.id
        
        if comment_update.entertainment_site_id:
            comment_query.entertainment_site_id = comment_update.entertainment_site_id
        if comment_update.note:
            comment_query.note = comment_update.note
        if comment_update.content:
            comment_query.content = comment_update.content
 
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(comment_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(comment_query)


# delete comment
@router.patch("/delete/{comment_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    comment_query = db.query(models.Comment).filter(models.Comment.id == comment_id, models.Comment.active == "True").first()
    
    if not comment_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"comment with id: {comment_id} does not exist")
        
    comment_query.active = False
    comment_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(comment_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "comment deleted!"}


# Get all comment inactive requests
@router.get("/get_all_inactive/", response_model=List[comments_schemas.CommentListing])
async def read_comments_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user : str = Depends(oauth2.get_current_user)):
    
    comments_queries = db.query(models.Comment).filter(models.Comment.active == "False", ).order_by(models.Comment.created_at).offset(skip).limit(limit).all()
    
    # pas de comment
    if not comments_queries:
       
        raise HTTPException(status_code=404, detail="comments not found")
                        
    return jsonable_encoder(comments_queries)


# Restore comment
@router.patch("/restore/{comment_id}", status_code = status.HTTP_200_OK,response_model = comments_schemas.CommentListing)
async def restore_comment(comment_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    comment_query = db.query(models.Comment).filter(models.Comment.id == comment_id, models.Comment.active == "False").first()
    
    if not comment_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"comment with id: {comment_id} does not exist")
        
    comment_query.active = True
    comment_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(comment_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(comment_query)
