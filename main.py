from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
load_dotenv()
from app import config_sething
import logging
# DATABASE_URL = os.getenv("DATABASE_URL")

from app.endpoints.auths_endpoints import router as auths_endpoints_routers
from app.endpoints.users_endpoints import router as users_routers
from app.endpoints.medias_endpoints import router as medias_routers
from app.endpoints.roles_endpoints import router as roles_routers
from app.endpoints.privileges_endpoints import router as privileges_routers
from app.endpoints.family_cards_endpoints import router as family_cards_routers
from app.endpoints.type_products_endpoints import router as type_products_routers
from app.endpoints.privilege_roles_endpoints import router as privilege_roles_routers
from app.endpoints.products_endpoints import router as products_routers
from app.endpoints.menus_endpoints import router as menus_routers
from app.endpoints.cards_endpoints import router as cards_routers
from app.endpoints.countries_endpoints import router as countries_routers
from app.endpoints.towns_endpoints import router as towns_routers
from app.endpoints.quarters_endpoints import router as quarters_routers
from app.endpoints.category_sites_endpoints import router as category_sites_routers
from app.endpoints.reservations_endpoints import router as reservations_routers
from app.endpoints.comments_endpoints import router as comments_routers
from app.endpoints.schedule_times_endpoints import router as schedule_times_routers
from app.endpoints.programs_endpoints import router as programs_routers
from app.endpoints.entertainment_sites_endpoints import router as entertainment_sites_routers
from app.endpoints.anounces_endpoints import router as anounces_routers
from app.endpoints.label_events_endpoints import router as label_events_routers
from app.endpoints.events_endpoints import router as events_routers
from app.endpoints.profils_endpoints import router as profils_routers
from app.endpoints.profil_roles_endpoints import router as profil_roles_routers
from app.endpoints.profil_privileges_endpoints import router as profil_privileges_routers
from app.endpoints.anounce_multimedias_endpoints import router as anounce_multimedias_routers
from app.endpoints.event_multimedias_endpoints import router as event_multimedias_routers
from app.endpoints.likes_endpoints import router as likes_routers
from app.endpoints.category_entertainment_sites_endpoints import router as category_entertainment_sites_routers
from app.endpoints.favorites_endpoints import router as favorites_routers
from app.endpoints.entertainment_site_multimedias_endpoints import router as entertainment_site_multimedias_routers
from app.endpoints.notes_endpoints import router as notes_routers
from app.endpoints.reels_endpoints import router as reels_routers
from app.endpoints.stories_endpoints import router as stories_routers
from app.endpoints.signals_endpoints import router as signals_routers

logging.basicConfig(level=logging.INFO)  # Niveau de journalisation souhaité, par exemple INFO

# FastAPI config_sethinguration

if config_sething.debug == "True":
    app = FastAPI(title=config_sething.project_name,version=config_sething.project_version)
else:
    app = FastAPI(title=config_sething.project_name,version=config_sething.project_version, docs_url = None)


# Create a GET-based route for the root URL.
@app.get("/")
def welcome():
    return {"message": "Thank you for visiting our polo API!"}

# Routes for multiple applications should be added to the main file.

app.include_router(auths_endpoints_routers)
app.include_router(medias_routers)
app.include_router(users_routers)
app.include_router(roles_routers)
app.include_router(privileges_routers)
app.include_router(privilege_roles_routers)
app.include_router(profils_routers)
app.include_router(profil_roles_routers)
app.include_router(profil_privileges_routers)

app.include_router(family_cards_routers)
app.include_router(cards_routers)

app.include_router(type_products_routers)
app.include_router(products_routers)
app.include_router(menus_routers)

app.include_router(countries_routers)
app.include_router(towns_routers)
app.include_router(quarters_routers)

app.include_router(entertainment_sites_routers)
app.include_router(entertainment_site_multimedias_routers)
app.include_router(category_sites_routers)
app.include_router(category_entertainment_sites_routers)
app.include_router(programs_routers)
app.include_router(schedule_times_routers)
app.include_router(anounces_routers)
app.include_router(anounce_multimedias_routers)
app.include_router(label_events_routers)
app.include_router(events_routers)
app.include_router(event_multimedias_routers)
app.include_router(reservations_routers)
app.include_router(reels_routers)
app.include_router(stories_routers)
app.include_router(signals_routers)

app.include_router(notes_routers)
app.include_router(favorites_routers)
app.include_router(comments_routers)
app.include_router(likes_routers)



origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=config_sething.allow_methods,
    allow_headers=config_sething.allow_headers,
)
logging.info("Message de journalisation")

# Exécutez l'application avec uvicorn
if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="172.19.120.188", port=8000)
    uvicorn.run("main:app", host=config_sething.server_host, port=config_sething.server_port, reload=True)
    # uvicorn.run("main:app", host="172.19.120.188", port=8000, reload=True)
    # la commande de lancement est : python main.py