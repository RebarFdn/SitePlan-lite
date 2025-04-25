from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from config import TEMPLATES
from starlette.routing import Mount,Route, WebSocketRoute
from models.auth_models import Password, RegisterUser
# Application Home Page


async def HomePage(request:Request):
    return TEMPLATES.TemplateResponse('/index.html', {'request': request})


async def Register(request:Request):
    '''  '''
    if request.method == 'POST':
        form = await request.form()
        err = RegisterUser().validate(value=form)
        if err:
            return err
        else:
            data = RegisterUser( **form, password=Password( **form ))
            return HTMLResponse(f"""<div>{data}</div>""")
    else:
        form = RegisterUser().form()
        return form



# routes aggregator
routes:list = [
    # WebSocketRoute("/pws", ws_project),
    Route('/', endpoint=HomePage),
    Route('/register', endpoint=Register, methods=['GET', 'POST'])
    
    ]
