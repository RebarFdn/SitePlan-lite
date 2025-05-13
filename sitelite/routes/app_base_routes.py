# Application base router
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from config import TEMPLATES
from starlette.routing import Mount,Route, WebSocketRoute
from models.data_models import RegisterUser
from decoRouter import Router
# Application Modules
from modules.project import projectManager
from modules.employee import employeeManager
from modules.rate import rateManager
from modules.supplier import supplierManager


router:Router = Router()

@router.get('/')
async def HomePage(request:Request):
    return TEMPLATES.TemplateResponse('/app_interface.html', {'request': request})


@router.post('/register')
@router.get('/register')
async def register_user(request:Request):
    """Handles registration of users  

    Args:
        request (Request): _description_
    """
    header:str = "CentryPlan Inc. User Registration"
    try:
        async with request.form() as form:
            model = await RegisterUser().validateForm(header=header, request_data=form, schema=RegisterUser, post='/register')
        return HTMLResponse(model)
    except:
        form = RegisterUser().data_form()
        html_form = RegisterUser().html_form(header=header, post='/register', form=form)