# The Application base Router 
from starlette.routing import Mount,Route, WebSocketRoute
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from config import STATIC_PATH, FAVICON_PATH
# Routes 
from routes.app_base_routes import router as app_base_router
from routes.data_analysis_routes import router as data_analysis_router


async def favicon(request): 
    """ Serves The Site Favicon file."""   
    return FileResponse(FAVICON_PATH)


# routes aggregator
router:list = [
    # WebSocketRoute("/pws", ws_project),
    Route('/favicon.ico', endpoint=favicon),
    Mount("/static", StaticFiles(directory=STATIC_PATH))
    ]

router.extend([route for route in app_base_router])
router.extend([route for route in data_analysis_router])