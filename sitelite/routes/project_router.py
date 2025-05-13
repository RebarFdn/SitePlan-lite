from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketDisconnect
from decoRouter import Router
from config import TEMPLATES
from modules.project import projectManager
from modules.employee import employeeManager
from modules.rate import rateManager
from modules.supplier import supplierManager



async def ws_project(ws: WebSocket):
    await ws.accept()#subprotocol=None, headers=None)
    #print(ws.url)
    #print(ws.headers)
    print(ws['path'])
    
    try:
        while True: 
            msg = await ws.receive_json()
            print('message', msg.get('chat_message'))
            """if msg in validator:
                json_data = search.get(msg) 
                await ws.send_json(json_data)
            elif msg in files:
                file = f"your file: {msg}".encode()
                await ws.send_bytes(file)
            elif 'Project' in msg or 'project' in msg or 'PROJECT' in msg:
                protocols = msg.split()
                project = await get_project(id=protocols[1])
                if protocols.__len__() > 2:
                    await ws.send_json(project.get(protocols[2]))
                else:
                    await ws.send_json(project)
            elif 'Employee' in msg or 'employee' in msg or 'worker' in msg:
                protocols = msg.split()
                employee = await search_employee(protocols)                       
                if protocols.__len__() > 3:
                    await ws.send_json(employee.get(protocols[3]))
                elif protocols.__len__() == 3:
                    if has_numbers(protocols[1]): # Request include employee id and property
                        await ws.send_json(employee.get(protocols[3]))
                    else: # Request is employee name
                        await ws.send_json(employee)
                elif protocols.__len__() == 2:# Request is employee id
                    await ws.send_json(employee)
                    
            else:"""
            await ws.send_text(f"<span>{msg.get('chat_message')}</span>")          
            
        ws._raise_on_disconnect(msg)
        await ws.close()
            
    except WebSocketDisconnect:
        pass



# The Project module router
router:Router = Router()


@router.get("/")
async def homepage(request:Request):
    return TEMPLATES.TemplateResponse('dashboard.jinja', {"request": request, "user": "Ian", "title": "SiteLite"})



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


@router.get("/rate/{id}/{filter}/{property}")
@router.post("/rate/{id}/{filter}/{property}")
@router.put("/rate/{id}/{filter}/{property}")
@router.delete("/rate/{id}/{filter}/{property}")
async def gppd_rate_(request:Request):
    ''' '''      
    prop = request.path_params.get('property')   
    filter = request.path_params.get('filter') 
    if prop.__len__() > 1  :
        rm = rateManager( id=request.path_params.get('id'), filter=filter, properties=[prop]) 
    else :
        rm = rateManager( id=request.path_params.get('id'), filter=filter)         
    return await rm._template(request)


@router.get("/employee/{id}/{filter}/{property}")
@router.post("/employee/{id}/{filter}/{property}")
@router.put("/employee/{id}/{filter}/{property}")
@router.delete("/employee/{id}/{filter}/{property}")
async def gppd_employee_(request:Request):
    ''' '''      
    prop = request.path_params.get('property')   
    filter = request.path_params.get('filter') 
    if prop.__len__() > 1  :
        em = employeeManager( id=request.path_params.get('id'), filter=filter, properties=[prop]) 
    else :
        em = employeeManager( id=request.path_params.get('id'), filter=filter)         
    return await em._template(request)


@router.get("/supplier/{id}/{filter}/{property}")
@router.post("/supplier/{id}/{filter}/{property}")
@router.put("/supplier/{id}/{filter}/{property}")
@router.delete("/supplier/{id}/{filter}/{property}")
async def gppd_supplier_(request:Request):
    ''' '''      
    prop = request.path_params.get('property')   
    filter = request.path_params.get('filter') 
    if prop.__len__() > 1  :
        sm = supplierManager( id=request.path_params.get('id'), filter=filter, properties=[prop]) 
    else :
        sm = supplierManager( id=request.path_params.get('id'), filter=filter)         
    return await sm._template(request)

