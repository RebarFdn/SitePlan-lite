from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from config import TEMPLATES
from starlette.routing import Mount,Route, WebSocketRoute

# Application Home Page
async def HomePage(request:Request):
    return TEMPLATES.TemplateResponse('/index.html', {'request': request})


# routes aggregator
routes:list = [
    # WebSocketRoute("/pws", ws_project),
    Route('/', endpoint=HomePage),
    
    ]
