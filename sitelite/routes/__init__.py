# The Application base Router 
from starlette.routing import Mount,Route, WebSocketRoute
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from config import STATIC_PATH, FAVICON_PATH

# Routes 
from routes.appHome import routes as app_home_routes

async def favicon(request): 
    """ Serves The Site Favicon file."""   
    return FileResponse(FAVICON_PATH)

# routes aggregator
router:list = [
    # WebSocketRoute("/pws", ws_project),
    Route('/favicon.ico', endpoint=favicon),
    Mount("/static", StaticFiles(directory=STATIC_PATH))
    ]

router.extend([route for route in app_home_routes])
#router.extend([route for route in planning_router])