# Application base router
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from config import TEMPLATES
from starlette.routing import Mount,Route, WebSocketRoute
from models.data_models import RegisterUser
from decoRouter import Router
# Application Modules
from modules.project import projectManager, ProjectApi, ProjectClient
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




@router.get("/project/{id}/{property}")
@router.post("/project/{id}/{property}")
@router.put("/project/{id}/{property}")
@router.delete("/project/{id}/{property}")
async def gppd_project_(request:Request): # get, post, put & delete
    ''' '''      
    prop = request.path_params.get('property')    
    if prop.__len__() > 1  :
        pm = projectManager( id=request.path_params.get('id'), properties=[prop]) 
    else :
        pm = projectManager( id=request.path_params.get('id'))         
    return await pm._template(request)


@router.get("/api_project/{id}/{property}/{atribute}")
@router.post("/api_project/{id}/{property}/{atribute}")
@router.put("/api_project/{id}/{property}/{atribute}")
@router.delete("/api_project/{id}/{property}/{atribute}")
async def api_project(request:Request): # get, post, put & delete
    ''' '''      
    prop:str = request.path_params.get('property') 
    attrib:str = request.path_params.get('atribute') 
    properties:list = []   
    if prop.__len__() > 1 : # check if property is legitimate
        properties.append(prop)
    if attrib.__len__() > 1 : # check if attribute is legitimate
        properties.append(attrib)
    if properties:
        papi = ProjectApi( id=request.path_params.get('id'), properties=properties) 
    else :
        papi = ProjectApi( id=request.path_params.get('id'))         
    return await papi._jsonapi(request)



@router.get("/Project/{id}/{property}/{atribute}")
@router.post("/Project/{id}/{property}/{atribute}")
@router.put("/Project/{id}/{property}/{atribute}")
@router.delete("/Project/{id}/{property}/{atribute}")
async def Project_(request:Request): # get, post, put & delete
    ''' '''      
    prop:str = request.path_params.get('property') 
    attrib:str = request.path_params.get('atribute') 
    properties:list = []   
    if prop.__len__() > 1 : # check if property is legitimate
        properties.append(prop)
    if attrib.__len__() > 1 : # check if attribute is legitimate
        properties.append(attrib)
    if properties:
        client = ProjectClient( id=request.path_params.get('id'), properties=properties) 
    else :
        client = ProjectClient( id=request.path_params.get('id'))         
    return await client._jsonapi(request)



@router.get("/rate/{id}/{filter}/{property}")
@router.post("/rate/{id}/{filter}/{property}")
@router.put("/rate/{id}/{filter}/{property}")
@router.delete("/rate/{id}/{filter}/{property}")
async def gppd_rate_(request:Request): # get, post, put & delete
    ''' ''' 
    filter = request.path_params.get('filter')       
    prop = request.path_params.get('property')    
    if prop.__len__() > 1  :
        pm = rateManager( id=request.path_params.get('id'), filter=filter, properties=[prop]) 
    else :
        pm = rateManager( id=request.path_params.get('id'), filter=filter)         
    return await pm._template(request)
