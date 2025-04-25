# The Application base Router 
from starlette.routing import Mount,Route, WebSocketRoute
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles
from config import STATIC_PATH, FAVICON_PATH

#from .project_router import router as project_router, ws_project

async def favicon(request): 
    """ Serves The Site Favicon file."""   
    return FileResponse(FAVICON_PATH)

# routes aggregator
router:list = [
    # WebSocketRoute("/pws", ws_project),
    Route('/favicon.ico', endpoint=favicon),
    Mount("/static", StaticFiles(directory=STATIC_PATH))
    ]

#router.extend([route for route in project_router])
#router.extend([route for route in planning_router])