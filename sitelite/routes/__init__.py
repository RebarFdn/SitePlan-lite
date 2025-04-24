# The Application base Router 
from starlette.routing import Mount,WebSocketRoute
from starlette.staticfiles import StaticFiles
from config import STATIC_PATH

#from .project_router import router as project_router, ws_project


# routes aggregator
router:list = [
   # WebSocketRoute("/pws", ws_project),
    Mount("/static", StaticFiles(directory=STATIC_PATH))
    ]

#router.extend([route for route in project_router])
#router.extend([route for route in planning_router])