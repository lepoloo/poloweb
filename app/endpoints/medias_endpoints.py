import os
from fastapi import APIRouter, HTTPException, Depends, status, Request, File, UploadFile,Form
from app.models import models
from app import config_sething
from app.database import engine, get_db
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from datetime import datetime
from PIL import Image
# from multipart.multipart import parse_options_header

models.Base.metadata.create_all(bind=engine)

# /users/
PARENT_MEDIA_NAME = config_sething.parent_media_name
MEDIA_PATHS = {
    "user_medias": "user_medias",# pour la photo de profile du user
    "product_medias": "product_medias",# photo des produit
    "card_medias": "card_medias",
    "event_medias": "event_medias",
    "anounce_medias": "anounce_medias",
    "product_medias": "product_medias",
    "entertainment_site_medias": "entertainment_site_medias",
    "reel_medias": "reel_medias",
    
}
router = APIRouter(prefix = "/medias", tags=['Medias Requests'])
# create image 
@router.post("/uploadfile/")
async def create_media(file: UploadFile = File(...), media_use: str = None):
    if media_use not in MEDIA_PATHS:
        raise HTTPException(status_code=404, detail=f"We don't have this media files!")
    
    if not os.path.exists(PARENT_MEDIA_NAME):
        os.makedirs(PARENT_MEDIA_NAME)

    # Vérifier si le répertoire enfant existe
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    if not os.path.exists(child_path):
        os.makedirs(child_path)
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    
    try:
        image = Image.open(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to open image: {str(e)}")

    # Modifier le nom du fichier en ajoutant la date actuelle comme préfixe
    file.filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + "_" + file.filename

    try:
        if media_use in MEDIA_PATHS:
            image.save(f"{PARENT_MEDIA_NAME}/{MEDIA_PATHS[media_use]}/{file.filename}")
            return {"filename save": file.filename}
        else:
            raise HTTPException(status_code=403, detail="This file cannot be saved, sorry!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

# get animage
@router.get("/image/{media_use}/{image_name}")
async def get_media(image_name: str, media_use: str):

    if media_use not in MEDIA_PATHS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"We don't have this media files!")

    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    image_path = os.path.join(child_path, image_name)
    return FileResponse(image_path)



@router.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...), media_use : str = None):
    
    if media_use not in MEDIA_PATHS:
        raise HTTPException(status_code=404, detail=f"We don't have this media files!")
    
    if not os.path.exists(PARENT_MEDIA_NAME):
        os.makedirs(PARENT_MEDIA_NAME)

    # Vérifier si le répertoire enfant existe
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    if not os.path.exists(child_path):
        os.makedirs(child_path)
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    # formated_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    media_name = []
    for file in files:
        try:
            image = Image.open(file.file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to open image: {str(e)}")

        file.filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + "_" + file.filename

        try:
            if media_use in MEDIA_PATHS:
                image.save(f"{PARENT_MEDIA_NAME}/{MEDIA_PATHS[media_use]}/{file.filename}")
                media_name.append(file.filename)
            else:
                raise HTTPException(status_code=403, detail="This file cannot be saved, sorry!")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")
    return {"media information": media_name}



# renvois une liste d'image
# @router.get("/images/{image_names:List[str]}/{media_use:str}")
# @router.get("/images/{image_names:List[str]},{media_use:str}")
# async def get_media_files(image_names: List[str], media_use: str):
#     if media_use not in MEDIA_PATHS:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"We don't have this media files!")
    
#     child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    
#     responses = {}
#     for image_name in image_names:
#         image_path = os.path.join(child_path, image_name)
#         responses.append(FileResponse(image_path))
         
#     return FileResponse(responses) 

@router.get("/images/{image_names:List[str]},{media_use:str}")
async def get_media_files(image_names: List[str], media_use: str):
    if media_use not in MEDIA_PATHS:
        raise HTTPException(status_code=404, detail=f"We don't have this media files!")
    
    if not os.path.exists(PARENT_MEDIA_NAME):
        os.makedirs(PARENT_MEDIA_NAME)

    # Vérifier si le répertoire enfant existe
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    if not os.path.exists(child_path):
        os.makedirs(child_path)
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)

    responses = []
    for image_name in image_names:
        image_path = os.path.join(child_path, image_name)
        responses.append(FileResponse(image_path))

    return responses
  
    
#     return responses
@router.post("/upload_video/")
async def upload_video(file: UploadFile = File(...), media_use: str = None):
    
    if media_use not in MEDIA_PATHS:
        raise HTTPException(status_code=403, detail="This file cannot be saved, sorry!")

    if not os.path.exists(PARENT_MEDIA_NAME):
        os.makedirs(PARENT_MEDIA_NAME)

    # Vérifier si le répertoire enfant existe
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    if not os.path.exists(child_path):
        os.makedirs(child_path)

    file.filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") + "_" + file.filename
    
    file_path = os.path.join(child_path, file.filename)
    with open(file_path, "wb") as video_file:
        video_file.write(file.file.read())

    return file.filename

@router.get("/get_video/{video_file:str},{media_use:str}")
async def get_media_files(video_file: str, media_use: str):

    if media_use not in MEDIA_PATHS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"We don't have media files for this media type!")
    
    if not os.path.exists(PARENT_MEDIA_NAME):
        os.makedirs(PARENT_MEDIA_NAME)

    # Vérifier si le répertoire enfant existe
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    if not os.path.exists(child_path):
        os.makedirs(child_path)
        
    child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
    video_path = os.path.join(child_path, video_file)

    if os.path.exists(video_path):
        return FileResponse(video_path)
      
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")


# delet media
async def delete_media(media_delet: str, media_use: str):
    """
    Endpoint pour supprimer un fichier média.

    Parameters:
    - `media_delet`: Le nom du fichier média dans le système de fichiers.

    Returns:
    - Message indiquant si la suppression a réussi ou non.
    """
    if media_use not in MEDIA_PATHS:
        raise HTTPException(status_code=404, detail=f"We don't have this media files!")
    
    try:
        # Construction du chemin complet du fichier média
        full_path = os.path.join(PARENT_MEDIA_NAME, media_use, media_delet)

        # Vérifier si le fichier existe
        if os.path.exists(full_path):
            # Supprimer le fichier
            os.remove(full_path)
            return {"message": f"Le fichier {media_delet} a été supprimé avec succès."}
        else:
            raise HTTPException(status_code=404, detail=f"Le fichier {media_delet} n'a pas été trouvé.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur s'est produite lors de la suppression du fichier : {str(e)}")

# #     return responses
# @router.post("/upload_videos/")
# async def upload_videos(files: list[UploadFile] = File(...), media_use: str = None):
#     
#     if media_use not in MEDIA_PATHS:
#         raise HTTPException(status_code=403, detail="This file cannot be saved, sorry!")

#     if not os.path.exists(PARENT_MEDIA_NAME):
#         os.makedirs(PARENT_MEDIA_NAME)

#     # Vérifier si le répertoire enfant existe
#     child_path = os.path.join(PARENT_MEDIA_NAME, media_use)
#     if not os.path.exists(child_path):
#         os.makedirs(child_path)

#     responses = []

#     for file in files:
#         file_path = os.path.join(child_path, file.filename)
#         with open(file_path, "wb") as video_file:
#             video_file.write(file.file.read())
#         responses.append(FileResponse(file.filename))

#     return responses







# Suppression  des vidéos expiré
# def update_attribute(db: Session = Depends(get_db)):
    
#     # Exemple de mise à jour d'une valeur dans la table
#     formated_date = datetime.now()
#     events_queries = db.query(models.Event).filter(models.Event.active == "True").all()
#     for events_querie in events_queries :
#         if events_querie.end_date < formated_date:
#             events_querie.active = "False"
#             db.commit()
#             db.refresh(events_querie)
    
#     db.close()

# # config_sethinguration de l'ordonnanceur
# scheduler = BackgroundScheduler()
# scheduler.add_job(update_attribute, 'interval', hours=1)
# scheduler.start()

# # Tâche pour arrêter l'ordonnanceur lorsque l'application FastAPI se ferme
# def close_scheduler():
#     scheduler.shutdown()

# router.add_event_handler("shutdown", close_scheduler)