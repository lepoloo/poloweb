
import os
from fastapi import APIRouter, HTTPException, Depends, Response, status,File, UploadFile, Request
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, get_db
from app.schemas import users_schemas
from app.models import models as models
from  utils import oauth2
from utils.users_utils import hash
import uuid
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from app.database import engine, get_db
from app.models import models
from typing import List

router = APIRouter(tags=['Authentication'])


@router.post('/login', response_model=users_schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(
        models.User.username == user_credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    if not oauth2.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    

    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


# create a new anounce sheet
@router.get("/get_user_by_token/", status_code = status.HTTP_200_OK, response_model=users_schemas.UserDetail)
async def get_user_by_token( db: Session = Depends(get_db), current_user : str = Depends(oauth2.get_current_user)):
    
    user_id = current_user.id
    
    user_query = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {user_id} does not exist")
    
    profils = user_query.profils
    details = [{ 'id': profil.id, 'refnumber': profil.refnumber, 'fucntion': profil.fucntion, 'description': profil.description, 'owner_id': profil.owner_id, 'entertainment_site_id': profil.entertainment_site_id, 'active': profil.active} for profil in profils]
    profils = details
    
    entertainment_sites = user_query.entertainment_sites
    details = [{ 'id': entertainment_site.id, 'refnumber': entertainment_site.refnumber, 'name': entertainment_site.name, 'address': entertainment_site.address, 'description': entertainment_site.description, 'longitude': entertainment_site.longitude, 'latitude': entertainment_site.latitude, 'quarter_id': entertainment_site.quarter_id, 'owner_id': entertainment_site.owner_id, 'nb_visite': entertainment_site.nb_visite, 'active': entertainment_site.active} for entertainment_site in entertainment_sites]
    entertainment_sites = details
    
    favorites = user_query.favorites
    details = [{ 'id': favorite.id, 'refnumber': favorite.refnumber, 'owner_id': favorite.owner_id, 'entertainment_site_id': favorite.entertainment_site_id, 'active': favorite.active} for favorite in favorites]
    favorites = details
    
    likes = user_query.likes
    details = [{ 'id': like.id, 'refnumber': like.refnumber, 'owner_id': like.owner_id, 'event_id': like.event_id, 'anounce_id': like.anounce_id, 'reel_id': like.reel_id, 'story_id': like.story_id, 'active': like.active} for like in likes]
    likes = details
    
    reels = user_query.reels
    details = [{ 'id': reel.id, 'refnumber': reel.refnumber, 'link_media': reel.link_media, 'owner_id': reel.owner_id, 'description': reel.description, 'nb_vue': reel.nb_vue, 'active': reel.active} for reel in reels]
    reels = details
    
    signals = user_query.signals
    details = [{ 'id': signal.id, 'refnumber': signal.refnumber, 'owner_id': signal.owner_id, 'event_id': signal.event_id, 'anounce_id': signal.anounce_id, 'story_id': signal.story_id, 'story_id': signal.story_id, 'entertainment_site_id': signal.entertainment_site_id, 'active': signal.active} for signal in signals]
    signals = details
    
    stories = user_query.stories
    details = [{ 'id': storie.id, 'refnumber': storie.refnumber, 'link_media': storie.link_media, 'owner_id': storie.owner_id, 'description': storie.description, 'nb_vue': storie.nb_vue, 'active': storie.active} for storie in stories]
    stories = details
    
    notes = user_query.notes
    details = [{ 'id': note.id, 'refnumber': note.refnumber, 'owner_id': note.owner_id, 'entertainment_site_id': note.entertainment_site_id, 'note': note.note, 'active': note.active} for note in notes]
    notes = details
    
    return jsonable_encoder(current_user)


# @router.get("/user/{profil_id}/privileges", response_model=List[dict])
@router.get("/user_privileges/{profil_id}")
def get_privileges_for_user_profil(
    profil_id: str,
    db: Session = Depends(get_db),
    # current_user: str Depends(oauth2.get_current_user)
    current_user: models.User = Depends(oauth2.get_current_user),  # Utilisation du modèle User
):
    # Utilisation de .first() au lieu de .all() pour obtenir un seul résultat
    profil = db.query(models.Profil).filter(
        models.Profil.id == profil_id, models.Profil.active == True
    ).first()
    
    if not profil:
        raise HTTPException(status_code=404, detail="Profil non trouvé")

    # Obtenez les privilèges directement liés au profil
    profile_privileges = [p.privilege.name for p in profil.profil_privileges]

    # Obtenez les privilèges liés aux rôles du profil
    for profil_role in profil.profil_roles:
        role_privileges = [rp.privilege.name for rp in profil_role.role.privilege_roles]
        profile_privileges.extend(role_privileges)

    # Supprimer les doublons
    unique_privileges = list(set(profile_privileges))

    return {"profil_id": profil.id, "privileges": unique_privileges}
    
    
# Endpoint de déconnexion
# @router.post("/logout")
# async def logout(request: Request, current_user : str = Depends(oauth2.get_current_user)):
    
#     headers = dict(request.headers)  # Convertir les headers en dict pour pouvoir les modifier
#     print(headers)
    
#     if "Authorization" in headers:
#         del headers["Authorization"]  # Supprimer la clé "Authorization" du dict des headers
        
#     token = request.headers.get("Authorization")  # Vérifier que le token a été supprimé
#     print(token)
    
#     if token is not None:
#         return {"error": "Invalid token"}
    

#     return {"message": "User successfully logged out"}

# Endpoint de déconnexion
@router.post("/logout")
async def logout( token : str = Depends(oauth2.get_current_user)):
    oauth2.invalid_tokens.add(token)
    return {"message": "Logout successful"}

