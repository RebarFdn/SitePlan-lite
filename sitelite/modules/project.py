from typing import Coroutine, List, Any
from asyncio import sleep
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from database import Recouch, local_db
from logger import logger
from modules.utils import timestamp, load_metadata, set_metadata, generate_id
from models import Project, project_phases, project_template 
from config import TEMPLATES

from tabulate import tabulate

_databases:dict = { # Project Databases
            "local":"site-projects", 
            "local_partitioned": False,
            "slave":"site-projects", 
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
        
        search_ = {
            'id': TEMPLATES.TemplateResponse(
                '/components/project/Home.html', 
                {"request": request, "project": self.project }),
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
            'index': TEMPLATES.TemplateResponse('/components/project/Index.html', 
                        {"request": request, "projects": await all_projects()}),
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
            'id': TEMPLATES.TemplateResponse(
                '/components/project/Home.html', 
                {"request": request, "project": self.project }),
            #'account': JSONResponse( self.project.get('account') ),
            
        }
        if self.properties:
            if self.properties.__len__() == 1: 
                search_[self.properties[0]] = TEMPLATES.TemplateResponse(f'/components/project/{self.properties[0].capitalize()}.html', 
                {"request": request, self.properties[0]:  self.project.get(self.properties[0])  }), 
                return search_.get(self.properties[0])
            elif self.properties.__len__() == 2:
                if self.properties[0] == 'tasks': 
                    # convert tasks list to task dictionary 
                    self.project['tasks'] = {task.get('_id'): task for task in self.project.get('tasks')}

                    search_[self.properties[0]] = TEMPLATES.TemplateResponse(f'/components/project/Task.html', 
                        {"request": request, 'job':  self.project.get(self.properties[0], {}).get(self.properties[1]) }) 
                search_ [self.properties[0]] = TEMPLATES.TemplateResponse(f'/components/project/{self.properties[0].capitalize()}.html', 
                    {"request": request, self.properties[0]:  self.project.get(self.properties[0], {}).get(self.properties[1]) })
                return search_.get(self.properties[0])
        else:
            return search_.get('id')




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
                if self.properties[0] == 'tasks': 
                    # convert tasks list to task dictionary 
                    self.project['tasks'] = {task.get('_id'): task for task in self.project.get('tasks')} 
                search_ [self.properties[0]] = JSONResponse( self.project.get(self.properties[0], {}).get(self.properties[1]) )
                return search_.get(self.properties[0])
        else:
            return search_.get('id')







