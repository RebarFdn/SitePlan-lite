# employee.py
from asyncio import sleep
import typing
from starlette.requests import Request
from logger import logger
from functools import lru_cache
from database import Recouch, local_db
try:
    from modules.utils import timestamp, load_metadata, set_metadata
    from modules.utils import generate_id
except Exception as e:
    from utils import timestamp,load_metadata, set_metadata
    from utils import generate_id
from modules.project import projects_index
from config import TEMPLATES

def page_url(page:str=None)->str:
    return f"/components/employee/{page}"


databases = { # Employee Databases
            "local":"site-workers", 
            "local_partitioned": False,
            "slave":"site-workers", 
            "slave_partitioned": False
            
            }


# connection to site-workers database 
db_connection:typing.Coroutine = local_db(db_name=databases.get('local'))   

def employee_model(key:str=None):
    EMPLOYEE_TEMPLATE = {
    "_id": None,  
    "name": "Site Worker",
    "oc": None,
    "sex": None,
    "dob": "",
    "height": None,
    "identity": None,
    "id_type": None,
    "trn": None,
    "occupation": None,
    "rating": None,
    "imgurl": None,
    "address": {
        "lot": None,
        "street": None,
        "town": None,
        "city_parish": None
    },
    "contact": {
        "tel": None,
        "mobile": None,
        "email": None
    },
    "account": {
        "bank": {
        "name": None,
        "branch": None,
        "account": "",
        "account_type": None
        },
        "payments": [],
        "loans": []
    },
    "nok": {
        "name": None,
        "relation": None,
        "address": None,
        "contact": None
    },
    "tasks": [],
    "jobs": [],
    "days": [],
    "state": {
        "active": False,
        "onleave": False,
        "terminated": False
    },
    "event": {
        "started": None,
        "onleave": [],
        "restart": [],
        "terminated": None,
        "duration": 0
    },
    "reports": [],
    
    }
    if key: return EMPLOYEE_TEMPLATE.get(key)
    else: return EMPLOYEE_TEMPLATE


#@lru_cache
async def all_workers(conn:typing.Coroutine=db_connection)->list:
    """_summary_
    Args:
        conn (typing.Coroutine, optional): _description_. Defaults to db_connection.
    Returns:
        list: _description_
    """
    data = await conn.get(_directive="_design/workers/_view/name-index") 
    try:
        return data.get('rows')
    except Exception as e:
        return {"error": str(e)}
    finally: 
        del data


async def get_worker( id:str=None, conn:typing.Coroutine=db_connection )->dict: 
    """Get a single Employee record by quering the database with employee's _id
    Args:
        id (str, optional): The employee's _id . Defaults to None.
        conn (typing.Coroutine, optional): database connection object. Defaults to db_connection.
    Returns:
        dict: key value store of employee's record.
    """               
    return await conn.get(_directive=id) 


async def get_worker_name_index()->list:   
    workers = await all_workers() 
    try: return [{"name": item.get('value').get('name'), "id": item.get('id')} for item in  workers ]   
    finally: del workers

        
async def get_worker_by_name( name:str=None, conn:typing.Coroutine=db_connection ) -> dict:
    """Retreive an employee Data from the database given the employee's full name.
    Args:
        name (str, optional): The employee's full name. Defaults to None.
        conn (typing.Coroutine, optional): Connection to couch database. Defaults to db_connection.
    Returns:
        dict: a key value container with the employee's data
    """
    index:list = await get_worker_name_index()
    id:list = [item.get('id') for item in index if item.get('name') == name]
    try:
        if id:
            id:str = id[0]
        return await get_worker(id=id)
    except Exception as e:
        return {"error": str(e)}
    finally:
        del index
        del(id)
           
# CRUD Functions  

async def save_employee(data:dict=None, user:str=None, conn:typing.Coroutine=db_connection ):        
    try:
        data["_id"] = generate_id(name=data.get('name'))
        data['imgurl'] = f"static/imgs/workers/{data.get('_id')}.png" 
        new_employee = employee_model() | data
        new_employee['meta_data'] = load_metadata(property='created', value=timestamp(), db=databases)        
        new_employee['meta_data'] = set_metadata(property='created_by', value=user, metadata=new_employee.get('meta_data'))
        await conn.post( json=new_employee)            
        return new_employee
    except Exception as e:
        return {"error": str(e)}
    

async def backup_employee(data:dict=None, conn:typing.Coroutine=db_connection ):        
    try:       
        new_employee = employee_model() | data
        await conn.post( json=new_employee)            
        return None
    except Exception as e:
        return {"error": str(e)}
    

async def update_employee(data:dict=None, conn:typing.Coroutine=db_connection ):   
    payload =  await conn.put( json=data)   
    try:           
        return payload
    except Exception as e:
        return {"error": str(e)}
    finally: 
        del payload

async def delete_employee( id:str=None, conn:typing.Coroutine=db_connection ):
    try: 
        return await conn.delete(_id=id)           
    except Exception as e: 
        print(str(e)) #logger().exception(e)
    

# Utility Methods 
async def employee_projects(employee:dict)->list:
    """_summary_

    Args:
        id (str, optional): _description_. Defaults to None.

    Returns:
        list: _description_
    """

    projects_ids = set() # List of project ids
    for item in employee.get('jobs'):
        if '-' in item:
            projects_ids.add(item.split('-')[0])
        else:
            projects_ids.add(item)
    projects_list = await projects_index() # list of projects 
    invol_projects = []
    for project in projects_list:
        if project.get('_id') in list(projects_ids):
            invol_projects.append(project)
    return invol_projects


class employeeManager:
    id:str = None
    PROPERTIES_INDEX:list = ['about', 'index', 'trades', 'model']
    def __init__(self, id:str=None, filter:str=None, properties:list=[]):
        self.id = id
        self.properties = properties
        self.filter = filter        
        
    async def load_data(self):
        self.employee = await get_worker(id=self.id)

    async def load_employees(self):
        self.employees = await all_workers()

    async def filter_employees(self):        
        if self.filter:            
            if self.filter == 'all' or self.filter == 'None':            
                return self.employees
            else:                
                return [employee for employee in self.employees if employee.get('value').get("occupation") == self.filter]
    

    def occupation_index(self):        
        occ_index:set = set()
        for item in self.employees:        
            occ_index.add(item.get('value').get('occupation') )   
        return occ_index
    

    async def create_new_employee(self, request:Request):
        payload = employee_model()   
        async with request.form() as form:            
            payload['name'] = form.get('name')
            payload['oc'] = form.get('oc')
            payload['sex'] = form.get('sex')
            payload['dob'] = form.get('dob')
            payload['height'] = form.get('height')
            payload['identity'] = form.get('identity')
            payload['id_type'] = form.get('id_type')
            payload['trn'] = form.get('trn')
            payload['occupation'] = form.get('occupation')
            payload['rating'] = form.get('rating')
            payload['imgurl'] = ""
            payload['address'] = {
                'lot': form.get('lot'),
                'street': form.get('street'),
                  'town': form.get('town'),
                   'city_parish': form.get('city_parish')
                }
            payload['contact'] = {
                'tel': form.get('tel'),
                'mobile': form.get('mobile'),
                'email': form.get('email')
                
            }
            payload['account'] = {
                "bank": {
                "name": form.get('bank'),
                "branch": form.get('bank_branch'),
                "account": form.get('account_no'),
                "account_type": form.get('account_type')
                }                
            }
            payload["nok"] = {
                "name": form.get('kin_name'),
                "relation": form.get('kin_relation'),
                "address": form.get('kin_address'),
                "contact":  form.get('kin_contact')
            }                      
            payload["state"]["active"] = True
        try:
            await save_employee(data=payload, user='ian') #request.user.username)   
        except Exception as e: 
            print(str(e))
        finally: 
            del(payload)


    async def _template(self, request:Request):
        if request.method == 'POST':            
            if self.properties.__len__() > 0 and self.properties[0] == 'save':
                await self.create_new_employee(request=request)
            else:
                pass
        elif request.method == 'DELETE':
            await delete_employee(id=self.id) 
            await sleep(0.5)           
            self.id = 'index'
                
        else:
            pass

        if self.id in self.PROPERTIES_INDEX:            
            await self.load_employees()
            property_search = {
                'index': TEMPLATES.TemplateResponse(page_url('employeesIndex.html'),
                    {
                        "request": request,
                        "workers": await self.filter_employees(),
                        "filter": self.filter,
                        "occupation_index": list(self.occupation_index())
                    }
                        )
            }        
            return property_search.get(self.id)
        else:
            pass
        
        await self.load_data()
        
        projects = await employee_projects(self.employee)
        search_ = {
            'id': TEMPLATES.TemplateResponse(page_url('Employee.html'), 
                {
                    "request": request, 
                    "employee": self.employee , 
                    "projects": projects, 
                    
                    }),
            
        }
        if self.properties:
            return search_.get(self.properties[0])
        else:
            return search_.get('id')


 
