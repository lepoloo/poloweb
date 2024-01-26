import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.schemas import reservations_schemas
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

# /reservations/

router = APIRouter(prefix = "/reservation", tags=['Reservations Requests'])
 
# create a new reservation sheet
@router.post("/create/", status_code = status.HTTP_201_CREATED, response_model=reservations_schemas.ReservationListing)
async def create_reservation(new_reservation_c: reservations_schemas.ReservationCreate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    author = current_user.id
    date_veref = new_reservation_c.date.strftime("%Y-%m-%d")
    reservation_query = db.query(models.Reservation).filter(models.Reservation.created_by == author, models.Reservation.description.contains(new_reservation_c.description), models.Reservation.date.startswith(date_veref), models.Reservation.entertainment_site_id == new_reservation_c.entertainment_site_id).first()
    if  reservation_query:
        raise HTTPException(status_code=403, detail="This Reservation site also exists!")
    
    formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Formatage de la date au format souhaité (par exemple, YYYY-MM-DD HH:MM:SS)
    concatenated_uuid = str(uuid.uuid4())+ ":" + formated_date
    NUM_REF = 10001
    codefin = datetime.now().strftime("%m/%Y")
    concatenated_num_ref = str(
            NUM_REF + len(db.query(models.Reservation).filter(models.Reservation.refnumber.endswith(codefin)).all())) + "/" + codefin
    
    
    new_reservation= models.Reservation(id = concatenated_uuid, **new_reservation_c.dict(), refnumber = concatenated_num_ref, created_by = author)
    
    try:
        db.add(new_reservation )# pour ajouter une tuple
        db.commit() # pour faire l'enregistrement
        db.refresh(new_reservation)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    return jsonable_encoder(new_reservation)

# Get all reservations requests
@router.get("/get_all_actif/", response_model=List[reservations_schemas.ReservationListing])
async def read_reservations_actif(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    reservations_queries = db.query(models.Reservation).filter(models.Reservation.active == "True").order_by(models.Reservation.created_at).offset(skip).limit(limit).all()
    
    # pas de reservation
    # if not reservations_queries:
    #     raise HTTPException(status_code=404, detail="reservation not found")
                        
    return jsonable_encoder(reservations_queries)



# Get an reservation
# "/get_reservation_impersonal/?refnumber=value_refnumber&phone=valeur_phone&email=valeur_email&reservationhour=valeur_reservationhour" : Retourne `{"param1": "value1", "param2": 42, "param3": null}`.
@router.get("/get_reservation_by_attribute/", status_code=status.HTTP_200_OK, response_model=List[reservations_schemas.ReservationListing])
async def detail_reservation_by_attribute(refnumber: Optional[str] = None, entertainment_site_id: Optional[str] = None, hour: Optional[str] = None, description: Optional[str] = None, nb_personne: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    reservation_query = {} # objet vide
    if refnumber is not None :
        reservation_query = db.query(models.Reservation).filter(models.Reservation.refnumber == refnumber, models.Reservation.active == "True").order_by(models.Reservation.created_at).offset(skip).limit(limit).all()
    if hour is not None :
        reservation_query = db.query(models.Reservation).filter(models.Reservation.hour == hour, models.Reservation.active == "True").order_by(models.Reservation.created_at).offset(skip).limit(limit).all()
    if entertainment_site_id is not None :
        reservation_query = db.query(models.Reservation).filter(models.Reservation.entertainment_site_id == entertainment_site_id, models.Reservation.active == "True").offset(skip).limit(limit).all()
    if description is not None:
        reservation_query = db.query(models.Reservation).filter(models.Reservation.description.contains(description), models.Reservation.active == "True").order_by(models.Reservation.created_at).offset(skip).limit(limit).all()
    if nb_personne is not None :
        reservation_query = db.query(models.Reservation).filter(models.Reservation.nb_personne == nb_personne, models.Reservation.active == "True").order_by(models.Reservation.created_at).offset(skip).limit(limit).all()
    
    
    if not reservation_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reservation does not exist")
    return jsonable_encoder(reservation_query)

# Get an reservation
@router.get("/get/{reservation_id}", status_code=status.HTTP_200_OK, response_model=reservations_schemas.ReservationDetail)
async def detail_reservation(reservation_id: str, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    reservation_query = db.query(models.Reservation).filter(models.Reservation.id == reservation_id, models.Reservation.active == "True").first()
    if not reservation_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reservation with id: {reservation_id} does not exist")
    return jsonable_encoder(reservation_query)





# update an reservation request
@router.put("/update/{reservation_id}", status_code = status.HTTP_205_RESET_CONTENT, response_model = reservations_schemas.ReservationDetail)
async def update_reservation(reservation_id: str, reservation_update: reservations_schemas.ReservationUpdate, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
        
    reservation_query = db.query(models.Reservation).filter(models.Reservation.id == reservation_id, models.Reservation.active == "True").first()

    if not reservation_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reservation with id: {reservation_id} does not exist")
    
    if  reservation_query.created_by != current_user.id or current_user.is_staff!= "True" :
        raise HTTPException(status_code=403, detail="You don't have the authorization to do this opération!")
        
    reservation_query.updated_by =  current_user.id
    
    if reservation_update.entertainment_site_id:
        reservation_query.entertainment_site_id = reservation_update.entertainment_site_id
    if reservation_update.hour:
        reservation_query.hour = reservation_update.hour
    if reservation_update.description:
        reservation_query.description = reservation_update.description
    if reservation_update.nb_personne:
        reservation_query.nb_personne = reservation_update.nb_personne
        
    
    try:
        db.commit() # pour faire l'enregistrement
        db.refresh(reservation_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process , pleace try later sorry!")
        
    return jsonable_encoder(reservation_query)


# delete reservation
@router.patch("/delete/{reservation_id}", status_code = status.HTTP_204_NO_CONTENT)
async def delete_reservation(reservation_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    reservation_query = db.query(models.Reservation).filter(models.Reservation.id == reservation_id, models.Reservation.active == "True").first()
    
    if not reservation_query:    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reservation with id: {reservation_id} does not exist")
        
    reservation_query.active = False
    reservation_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(reservation_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return {"message": "reservation deleted!"}


# Get all reservation inactive requests
@router.get("/get_all_inactive/", response_model=List[reservations_schemas.ReservationListing])
async def read_reservations_inactive(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    reservations_queries = db.query(models.Reservation).filter(models.Reservation.active == "False", ).order_by(models.Reservation.created_at).offset(skip).limit(limit).all()
    
    # pas de reservation
    # if not reservations_queries:
    #     raise HTTPException(status_code=404, detail="reservations not found")
                        
    return jsonable_encoder(reservations_queries)


# Restore reservation
@router.patch("/restore/{reservation_id}", status_code = status.HTTP_200_OK,response_model = reservations_schemas.ReservationListing)
async def restore_reservation(reservation_id: str,  db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    reservation_query = db.query(models.Reservation).filter(models.Reservation.id == reservation_id, models.Reservation.active == "False").first()
    
    if not reservation_query:
            
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"reservation with id: {reservation_id} does not exist")
        
    reservation_query.active = True
    reservation_query.updated_by =  current_user.id
    
    try:  
        db.commit() # pour faire l'enregistrement
        db.refresh(reservation_query)# pour renvoyer le résultat
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=403, detail="Somthing is wrong in the process, pleace try later sorry!")
    
    
    return jsonable_encoder(reservation_query)
