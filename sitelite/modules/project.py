from typing import Coroutine, List, Any
from asyncio import sleep
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from database import Recouch, local_db
from logger import logger
from modules.utils import timestamp, load_metadata, set_metadata, generate_id
from models import Project, project_phases, project_template ,DepositModel
from config import TEMPLATES

import time
from plyer import notification
#from tabulate import tabulate

_databases:dict = { # Project Databases
            "local":"lite-projects", 
            "local_partitioned": False,
            "slave":"lite-projects", 
            "slave_partitioned": False            
            }
# connection to site-projects database 
db_connection:Coroutine = local_db(db_name=_databases.get('local'))   

# CRUD OPERATIONS

async def all_projects( conn:Coroutine=db_connection )->list:
    try:
        projects:dict = await conn.get(_directive="_design/project-index/_view/name-view") 
        return projects.get('rows')          
    except Exception as e:
        logger().error( str(e))
    finally: del(projects)


async def get_project(id:str=None, conn:Coroutine=db_connection)->dict:
    """Retreive a single Project Object from storage

    Args:
        id (str, optional): The project _id . Defaults to None.
        conn (Coroutine, optional): connection to a couchdb  database. Defaults to db_connection.

    Returns:
        dict: The Project Object
    """
    r:dict = await conn.get(_directive=id)
    try:       
        return r
    except Exception as e:
        logger().error(str(e))        
    finally: del(r)  


async def save_project(data:dict=None, user:str=None, conn:Coroutine=db_connection )->dict:   
    try:
        data['_id'] = generate_id(name=data.get('name')) 
        new_project = project_template() | data
        new_project['meta_data'] = load_metadata(property='properties', value=list(new_project.keys()), db=_databases)
        new_project['meta_data'] = set_metadata(property='created', value=timestamp(),  metadata=new_project.get('meta_data'))
        new_project['meta_data'] = set_metadata(property='created_by', value=user, metadata=new_project.get('meta_data'))
        await conn.post( json=new_project )  
        return new_project  
    except Exception as e:
        print(e)  
        

async def update_project(data:dict=None, conn:Coroutine=db_connection):
        try:            
            return await conn.put( json=data)            
        except Exception as e:
            logger().exception(e)
            

async def delete_project( id:str=None, conn:Coroutine=db_connection ):    
    try:            
        await conn.delete(_id=id)
    except Exception as e:
        logger().exception(e)
    
# Utility Methods 
async def projects_index()->list:
    """   

    Returns:
        list: _description_
    """
    return [{"_id": project.get('id'), "name": project.get('key')} for project in await all_projects()]


async def get_project_ids()->list:
    return [project.get('id') for project in await all_projects()]


# Project accounting utilities 
async def transact_deposit( project:dict=None, data:dict=None )->dict:
    """Handle Funds Deposit records on a project's account"""
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)
    if data:                       
        project['account']['transactions']['deposit'].append(data)
        project['activity_logs'].append(
            {
                "id": timestamp(),
                "title": "Funds Deposit",
                "description": f"""Account {data.get('type') } with Refference {data.get('ref')} was added to Project  {project.get('_id')}
                Account Transactions by { data.get('user') }"""
            }
            ) 
        project['account']['updated'] = timestamp()
        try:
            await update_project(data=project)
            return {"_id": project.get('_id'), "account": project.get('account')}
        except Exception as e:
                logger().exception(e)
        finally:                
                del(project) # clean up
    else:
        return {"error": 501, "message": "You did not provide any data for processing."}

    


async def transact_withdrawal( project:dict=None, data:dict=None )->dict:  
    """Handle Withrawals records on a project's account""" 
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if data:               
        project['account']['transactions']['withdraw'].append(data)
        project['activity_logs'].append(
                {
                    "id": timestamp(),
                    "title": "Funds Withdrawal",
                    "description": f"""Account {data.get('type') } with Refference {data.get('ref')} was done on Project  {project.get('_id')}
                        Account Transactions by { data.get('user') }"""
                })  
        #processProjectAccountBallance()
        project['account']['updated'] = timestamp()
        try:
            await update_project(data=project)
            return {"_id": project.get('_id'), "account": project.get('account')}
        except Exception as e:
                logger().exception(e)
        finally:                
                del(project) # clean up
    else:
        return {"error": 501, "message": "You did not provide any data for processing."}

   

# Project specific utilities
def set_prop( prop:str=None ):
    if prop[len(prop)-1: ] == 's':
        return prop[ :-1]
    else:
        return prop




class projectManager:
    """Handles Client side requests and responses 

        Returns an Html template 
    """
    id:str = None
    PROPERTIES_INDEX:list = ['index', 'phases', 'model']

    def __init__(self, id:str=None, properties:list=[]):
        self.id = id
        self.properties = properties
        
    
    async def create_new_project(self, request:Request):
        payload = project_template()
        async with request.form() as form:
            payload["name"] = form.get('name')
            payload["category"] = form.get('category')
            payload["standard"] = form.get('standard')
            payload["address"] = {
                    "lot": form.get('lot'), 
                    "street": form.get('street'), 
                    "town": form.get('town'),
                    "city_parish": form.get('city_parish'),
                    "country": form.get('country', "Jamaica") 
                }
            payload["owner"] = {
                "name": form.get('owner'),
                "contact": None,
                "address": {"lot": None, "street": None, "town": None,"city_parish": None,"country": None, }
                }
            payload["admin"]["leader"] =  form.get('lead')            
        try:     
            return await save_project(data=payload, user='ian') #username) 
        except Exception as e:
            return str(e)
        finally:            
            del(payload)
            
    
    async def _template(self, request:Request):
        # Process Create New and Delete Requests
        if request.method == 'POST':            
            if self.properties.__len__() > 0 and self.properties[0] == 'save':
                await self.create_new_project(request=request)
            else:
                pass
        elif request.method == 'DELETE':
            await delete_project(id=self.id) 
            await sleep(0.5)           
            self.id = 'index'                
        else:
            pass
        # Process Get Requests
        property_search = {
            'index': TEMPLATES.TemplateResponse('/components/project/Index.html', 
                        {"request": request, "projects": await all_projects()})
        }
        # 
        if self.id in self.PROPERTIES_INDEX:
            return property_search.get(self.id)
        else:
            pass
        # if self.id is a project id 
        self.project = await get_project(id=self.id)
        notification.notify(
            title = "HEADING HERE",
            message=" DESCRIPTION HERE" ,
          
            # displaying time
            timeout=2 
        )
        search_ = {
            'id': TEMPLATES.TemplateResponse(
                '/components/project/Project.html', 
                {"request": request, "project": self.project ,"paybill":{}}),
            'account': TEMPLATES.TemplateResponse(
                '/components/project/Account.html', 
                {"request": request, "project": self.project }),
        }
        if self.properties:
            return search_.get(self.properties[0])
        else:
            return search_.get('id')



class ProjectClient:
    """Handles Api requests to the server  

        Returns Json 
    """
    id:str = None
    PROPERTIES_INDEX:list = ['index', 'phases', 'model']

    def __init__(self, id:str=None, properties:list=[]):
        self.id = id
        self.properties = properties   
    

    async def _jsonapi(self, request:Request):
        self._ids:list = await get_project_ids()
        _search:dict = {
            'index': TEMPLATES.TemplateResponse('/components/project/Index.html', 
                        {"request": request, "projects": await all_projects()}),
            'phases': JSONResponse( project_phases() ),
            'model': JSONResponse( project_template() )
            
        }
        
        # Process Create New and Delete Requests
        if request.method == 'POST': 
            async with request.form() as form: # Aquire the form data
                form_data = dict(form) 
            
            if self.id == 'create': # checking... if request to create a project                 
                return JSONResponse({self.id: { key: val for key, val in form_data.items()}})
                # await self.create_new_project(request=request) 
                # self.id = 'index'   
            elif self.id in self._ids: # checking... if request to modify a project                
                self.project = await get_project(id=self.id)  #get and load the project
                
                if self.properties: # get instructions from properties
                    if self.properties[0] == 'deposit':
                        form_data['date'] = timestamp(date=form_data.get('date')) 
                        deposit = DepositModel( **form_data )
                        result = await transact_deposit(project=self.project, data=deposit.model_dump())
                        return TEMPLATES.TemplateResponse(
                        '/components/project/account/Deposits.html', 
                        {"request": request, "project": result })

                   

                    else:
                        return JSONResponse(self.project.get(self.properties[0]))
                else:
                    return JSONResponse({ self.id: self.project })

            else:
                pass
        elif request.method == 'DELETE':
            await delete_project(id=self.id) 
            await sleep(0.5)           
            self.id = 'index'                
        else:
            pass
        # Process Get Requests
        
        # 
        if self.id in self.PROPERTIES_INDEX:
            return _search.get(self.id)
        else:
            pass
        # if self.id is a project id, 
        self.project = await get_project(id=self.id)  # get and load the project     
        #for item in self.project.get('days'):
        #    item['_id'] = item.get('id') 
        #    await sleep(0.05)
        #await update_project(data=self.project)

        _search['id'] = TEMPLATES.TemplateResponse(
                '/components/project/Home.html', 
                {"request": request, "project": self.project })
            
        
        if self.properties:
            if self.properties.__len__() == 1: 
                
                _search [self.properties[0]] = TEMPLATES.TemplateResponse(f'/components/project/{self.properties[0].capitalize()}.html', 
                    {"request": request, 'project': {'_id':self.id, self.properties[0]:  self.project.get(self.properties[0], {})}})             
                
                return _search.get(self.properties[0])
            elif self.properties.__len__() == 2:
                
                prop:str = set_prop(self.properties[0])
                """if self.properties[0][len(self.properties[0])-1: ] == 's':
                    prop = self.properties[0][ :-1]
                else:
                    prop = self.properties[0]"""
                
                if type(self.project.get(self.properties[0]))  == list: 
                    # convert tasks list to task dictionary 
                    self.project[self.properties[0]] = {item.get('_id') if item.get('_id') else item.get('id'): item for item in self.project.get(self.properties[0])}

                return TEMPLATES.TemplateResponse(f'/components/project/{prop.capitalize()}.html', 
                    {"request": request, prop: self.project.get(self.properties[0], {}).get(self.properties[1]) })  
                             

                
        else:
            return _search.get('id')


class ProjectApi:
    """Handles Api requests to the server  

        Returns Json 
    """
    id:str = None
    PROPERTIES_INDEX:list = ['index', 'phases', 'model']

    def __init__(self, id:str=None, properties:list=[]):
        self.id = id
        self.properties = properties

    async def _jsonapi(self, request:Request):
        # Process Create New and Delete Requests
        if request.method == 'POST':            
            if self.properties.__len__() > 0 and self.properties[0] == 'logs':
                await self.create_new_project(request=request)
            else:
                pass
        elif request.method == 'DELETE':
            await delete_project(id=self.id) 
            await sleep(0.5)           
            self.id = 'index'                
        else:
            pass
        # Process Get Requests
        property_search = {
            'index': JSONResponse( await all_projects() ),
            'phases': JSONResponse( project_phases() ),
            'model': JSONResponse( project_template() )
        }
        # 
        if self.id in self.PROPERTIES_INDEX:
            return property_search.get(self.id)
        else:
            pass
        # if self.id is a project id 
        self.project = await get_project(id=self.id)        
        
        search_ = {
            'id': JSONResponse( self.project ),
            #'account': JSONResponse( self.project.get('account') ),
            
        }
        if self.properties:
            if self.properties.__len__() == 1: 
                search_[self.properties[0]] = JSONResponse( self.project.get(self.properties[0]) )
                return search_.get(self.properties[0])
            elif self.properties.__len__() == 2:
                if self.properties[0] == 'jobs': 
                    # convert tasks list to task dictionary 
                    self.project['jobs'] = {job.get('_id'): job for job in self.project.get('jobs')} 
                    return TEMPLATES.TemplateResponse('/components/project/Job.html', 
                    {"request": request, 'job': self.project.get(self.properties[0], {}).get(self.properties[1])})
                search_ [self.properties[0]] = JSONResponse( self.project.get(self.properties[0], {}).get(self.properties[1]) )
                return search_.get(self.properties[0])
        else:
            return search_.get('id')







