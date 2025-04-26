from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from config import TEMPLATES
from starlette.routing import Mount,Route, WebSocketRoute
from pydantic import ValidationError, PydanticUserError
from models.auth_models import Password, RegisterUser

# Application Home Page


async def HomePage(request:Request):
    return TEMPLATES.TemplateResponse('/index.html', {'request': request})


async def Register(request:Request):
    '''  '''
    if request.method == 'POST':
        form = await request.form()
        try:
            data = RegisterUser( 
                name=form.get('name'),
                username=form.get('username'), 
                email=form.get('email'), 
                password=form.get('password') 
            )
            return HTMLResponse(f"""<div>{data.model_dump()}</div>""")
        except  ValidationError as ero:           
            return HTMLResponse(f"""<div>{ero}</div>""")       
        
    else:
        form = RegisterUser().form()
        return form



# routes aggregator
routes:list = [
    # WebSocketRoute("/pws", ws_project),
    Route('/', endpoint=HomePage),
    Route('/register', endpoint=Register, methods=['GET', 'POST'])
    
    ]
