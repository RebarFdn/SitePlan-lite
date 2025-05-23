# supplier.py
from asyncio import sleep
import typing
from starlette.requests import Request
from logger import logger
from functools import lru_cache
from database import Recouch, local_db
from modules.utils import timestamp, load_metadata, set_metadata, generate_id
from config import TEMPLATES

def page_url(page:str=None)->str:
    return f"/components/supplier/{page}"


databases = { # Suppliers Databases
            "local":"site-suppliers", 
            "local_partitioned": False,
            "slave":"site-suppliers", 
            "slave_partitioned": False            
            }

# connection to site-suppliers database 
db_connection:typing.Coroutine = local_db(db_name=databases.get('local')) 

def supplier_model(key:str=None)->dict:
    SUPPLIER_TEMPLATE = {
    "_id": None,    
    "name": "Supplier Name",
    "account": {
        "bank": {
        "branch": None,
        "name": None,
        "account": None,
        "account_type": None
        },
        "transactions": [
        
        ]
    },
    "address": {
        "lot": None,
        "street": None,
        "town": None,
        "city_parish": None,
        "country": None
    },
    "contact": {
        "tel": None,
        "mobile": None,
        "email": None
    },
    "taxid": None,
    
    }
    if key : return SUPPLIER_TEMPLATE.get(key)
    else: return SUPPLIER_TEMPLATE


async def all_suppliers_ref(conn:typing.Coroutine=db_connection)->list:
    try:
        r:dict = await conn.get(_directive="_all_docs") 
        return r.get('rows')           
    except Exception as e: logger().exception(e)
    finally: del(r)


async def all_suppliers(conn:typing.Coroutine=db_connection)->list:
    try:
        r:dict = await conn.get(_directive="_design/suppliers/_view/all") 
        return r.get('rows')           
    except Exception as e: logger().exception(e)
    finally: del(r)


async def supplier_name_index(conn:typing.Coroutine=db_connection)->list:
    def processIndex(p): return p.get('key')
    try:
        r:dict = await conn.get(_directive="_design/suppliers/_view/name-index") 
        return list(map( processIndex,  r.get('rows')))            
    except Exception as e: logger().exception(e)
    finally: del(r)


async def supplier_invoice_id_index(conn:typing.Coroutine=db_connection)->list:
    def processIndex(p): return  p.get('key')
    try:
        r:dict = await conn.get(_directive="_design/project-index/_view/invoice-id") 
        return list(map( processIndex,  r.get('rows')))            
    except Exception as e: logger().exception(e)
    finally: del(r)


async def get_supplier( id:str=None, conn:typing.Coroutine=db_connection)->dict:
    try:
        r:dict = await conn.get(_directive=id) 
        return r  
    except Exception as e: logger().exception(e)
    finally: del(r)



async def save_supplier(data:dict, user:str=None, conn:typing.Coroutine=db_connection):    
    if data.get("_id"):
        pass
    else:
        data["_id"] = generate_id(name=data.get('name'))
    new_supplier = supplier_model() | data
    if new_supplier.get('meta_data'): # meta_data is existing
        new_supplier['meta_data']['created'] = timestamp()
        new_supplier['meta_data']['created_by'] = user
    else:
        new_supplier['meta_data'] = load_metadata(property='created', value=timestamp(), db=databases)
        new_supplier['meta_data'] = set_metadata(property='created_by', value=user, metadata=new_supplier.get('meta_data'))
    try:
        await conn.post( json=new_supplier)  
        return new_supplier                      
    except Exception as e: logger().exception(e)
    finally:
        del(data)
        del(new_supplier)


async def update_supplier( data:dict=None, conn:typing.Coroutine=db_connection)->dict:
    payload = None
    supplier = await get_supplier(id=data.get('_id'))        
    try:
        payload = supplier | data
        await conn.put(json=payload) 
        return payload           
    except Exception as e: logger().exception(e)
    finally: 
        del(payload)
        del(supplier)


async def delete_supplier( id:str=None, conn:typing.Coroutine=db_connection ):
    try: return await conn.delete(_id=id)           
    except Exception as e: logger().exception(e)
    

    

class supplierManager:
    id:str = None
    PROPERTIES_INDEX:list = ['about', 'index', 'model']
    def __init__(self, id:str=None, filter:str=None, properties:list=[]):
        self.id = id
        self.properties = properties
        self.filter = filter        
        
    async def load_data(self):
        self.supplier = await get_supplier(id=self.id)

    async def load_suppliers(self):
        self.suppliers = await supplier_name_index()

    async def filter_suppliers(self):        
        if self.filter:            
            if self.filter == 'all' or self.filter == 'None':            
                return self.suppliers
            else:                
                return [supplier for supplier in self.suppliers if supplier.get("address").get("city_parish") == self.filter]
    
    async def create_new_supplier(self, request:Request):
        data = supplier_model()     
        async with request.form() as form:
            data['name'] = form.get('name')
            data['taxid'] = form.get('taxid')
            # Address Info
            data['address']['lot'] = form.get('lot')
            data['address']['street'] = form.get('street')
            data['address']['town'] = form.get('town')
            data['address']['city_parish'] = form.get('city_parish')
            data['address']['country'] = form.get('country')
            # Contact Info
            data['contact']['tel'] = form.get('tel')
            data['contact']['mobile'] = form.get('mobile')
            data['contact']['email'] = form.get('email')
            # Banking Info
            data['account']['bank']['branch'] = form.get('branch')
            data['account']['bank']['name'] = form.get('bank')
            data['account']['bank']['account'] = form.get('account_no')
            data['account']['bank']['account_type'] = form.get('account_type')             
        try:                
            await save_supplier(data=data, user='ian') #request.user.username)            
        except Exception as e: 
            print(str(e))
        finally: 
            del(data)

    
    async def _template(self, request:Request):
        if request.method == 'POST':            
            if self.properties.__len__() > 0 and self.properties[0] == 'save':
                await self.create_new_supplier(request=request)
            else:
                pass
        elif request.method == 'DELETE':
            await delete_supplier(id=self.id) 
            await sleep(0.5)           
            self.id = 'index'
                
        else:
            pass
                
        if self.id in self.PROPERTIES_INDEX:            
            await self.load_suppliers()
            property_search = {
                'index': TEMPLATES.TemplateResponse(page_url('Index.html'),
                    {
                        "request": request,
                        "suppliers": self.suppliers,
                        "filter": self.filter,
                        "locations": {supplier.get("address").get("city_parish") for supplier in self.suppliers },
                        "filtered": await self.filter_suppliers()
                    }
                        ),
                'about': TEMPLATES.TemplateResponse(page_url('About.html'),
                    {
                        "request": request,                                               
                        "locations": {supplier.get("address").get("city_parish") for supplier in self.suppliers },
                        
                    }
                        )
            }        
            return property_search.get(self.id)
        else:
            pass
        # Handle Update requests here 
        await self.load_data()
       

        search_ = {
            'id': TEMPLATES.TemplateResponse(page_url('Supplier.html'), 
                {"request": request, "supplier": self.supplier , 'total_transactions': 0.00 }),
            
        }
        if self.properties:
            return search_.get(self.properties[0])
        else:
            return search_.get('id')


 