#rate.py
import typing
from starlette.requests import Request
from logger import logger
from functools import lru_cache
from modules.utils import timestamp,  to_dollars, generate_id, load_metadata, set_metadata
from database import Recouch, local_db
from config import TEMPLATES

def page_url(page:str=None)->str:
    return f"/components/rate/{page}"

databases = { # industry rate Databases
            "local":"rate-sheet", 
            "local_partitioned": False,
            "slave":"rate-sheet", 
            "slave_partitioned": False            
            }

# connection to site-projects database 
db_connection:typing.Coroutine = local_db(db_name=databases.get('local'))  



@lru_cache
def rate_categories():
    return {
            "excavation": "Excavation",
            "steelwork": "Steelwork",
            "masonry": "Masonry",
            "carpentry": "Carpentry",
            "joinery": "Joinery",
            "painting": "Painting",
            "plumbing": "Plumbing",
            "scaffolding": "Scaffolding",
            "tiling": "Tiling",
            "welding": "Welding",
            "electrical": "electrical"
    }

@lru_cache
def rate_model()->dict:
    return {
            "_id": None,            
            "title": None,
            "description": None,
            "metric": {
                "unit": None,
                "price": 0,
                "quantity":0,
                "total": 0
            },
            "imperial": {
                "unit": None,
                "price": 0,
                "quantity": 0,
                "total": 0
            },
            "state": {
                "active": False,
                "complete": False,
                "pause": False,
                "terminate": False
            },
            "event": {
                "started": None,
                "completed": None,
                "paused": [],
                "restart": [],
                "terminated": None
            },
            "assigned": False,
            "assignedto": None,
            "phase": None,
            "paid": None,
            "timestamp": 0,
            "comments": [],
            "progress": 0,
            "output": {
                "metric": 0,
                "imperial": 0
            },
            "category": None
            
            }


async def all_rates_ref(conn:typing.Coroutine=db_connection)->list:
    rates:dict = await conn.get(_directive = "_all_docs")   
    try:            
        return  rates.get('rows')        
    except Exception as e: logger().exception(e)
    finally: del rates


async def all_rates(conn:typing.Coroutine=db_connection)->list: 
        '''Retreives a list of rate data.
        ''' 
        r = None      
        def processrates(rate):
            return rate['value']            
        try:
            r = await conn.get(_directive="_design/index/_view/document")
            return list(map(processrates,  r.get('rows', []) ))
        except Exception as e: logger().exception(e)
        finally: del(r)

 

async def get_industry_rate(id:str, conn:typing.Coroutine=db_connection)->dict:
    rate = await conn.get(_directive=id) 
    try:
        return rate
    except Exception: logger().exception(Exception)
    finally: del rate
    
#@profile(precision=2, stream=fp)
async def save_rate(data:dict=None, cloned:str=None, user:str=None, conn:typing.Coroutine=db_connection)->dict:      
    '''Stores a Rate Item Permanently on the Platform.'''
    data['_id'] = generate_id(name=data.get('title')) 
    new_rate:dict = rate_model() | data
    try:
        new_rate['meta_data'] = load_metadata(property='created', value=timestamp(), db=databases)
        new_rate['meta_data'] = set_metadata(property='created_by', value=user, metadata=new_rate.get('meta_data'))
        if cloned:
            new_rate['meta_data'] = set_metadata(property='cloned', value={"from": cloned}, metadata=new_rate.get('meta_data'))
        await conn.post(json=new_rate) 
        return new_rate
    except Exception as e: logger().exception(e)  
    finally: del new_rate


async def backup_industry_rate(data:dict=None, conn:typing.Coroutine=db_connection)->dict:      
    '''restores and existing  Rate Item Permanently on the Platform.'''    
    new_rate:dict = rate_model() | data
    try:
        await conn.post(json=new_rate) 
        return new_rate
    except Exception as e: logger().exception(e)  
    finally: del new_rate

        
        
#@profile(precision=2, stream=fp)
async def update_rate(data:dict=None, conn:typing.Coroutine=db_connection):
    '''Updates a Rate Item with data provided.
    --- Footnote:
            enshure data has property _id
    extra:
        updates the objects meta_data property 
        or create and stamp the meta_data field
        if missing                 
    '''
    if '_rev' in list(data.keys()): del(data['_rev'])      
    try: return await conn.put(json=data)            
    except Exception as e: logger().exception(e)
        

#@profile(precision=2, stream=fp)
async def delete_rate(id:str=None, conn:typing.Coroutine=db_connection):
        '''Permanently Remove a Rate Item from the Platform.
        ---Requires:
            name: _id
            value: string 
            inrequest_args: True
        '''        
        try: return await conn.delete(_id=id)
        except Exception as e: logger().exception(e)


async def rate_index_generator(filter:str=None):
    rates = await all_rates()
    categories = {rate.get('category') for rate in rates }
    if filter:
        if filter == 'all' or filter == 'None':            
            filtered = rates
        else:
            filtered = [rate for rate in rates if rate.get("category") == filter]

        yield f"""
                <div>
                <p class="text-center text-xs">Rates Index Html Generator</p>
                <div class="flex flex-row bg-gray-300 py-3 px-4 items-inline text-center rounded relative">
                <span class="cursor-pointer" uk-toggle="target: #new-rate-modal"uk-icon="plus"></span>
                    <p class="mx-10">Industry Rates Index</p>                
                    <span class="uk-badge">{len(filtered)}</span>
                       <a href class="absolute right-0">Filter <span uk-drop-parent-icon></span></a>
                    <div uk-dropdown="pos: bottom-center">
                    <ul class="uk-nav uk-dropdown-nav">
                     <li class="uk-nav-header">Filter Rates</li>
                     <li><a 
                                href="#"
                                hx-get="/rates_html_index/{'all'}"
                                hx-target="#dash-left-pane"
                                hx-trigger="click"                                 
                                >All Categories</a>
                        </li>
                    """

        for item in categories:
            yield f""" <li>
                                <a 
                                href="#"
                                hx-get="/rates_html_index/{item}"
                                hx-target="#dash-left-pane"
                                hx-trigger="click"                                 
                                >{item}</a></li>"""
                       
                        
        yield f""" </ul>
                </div>                 
                       
                    </div>
                <ul class="uk-list uk-list-striped h-96 p-2 overflow-y-auto">
                """
        
        for rate in filtered:
                yield f"""<li>
                <div class="flex flex-col text-sm bg-gray-300 py-2 px-3 my-2 border rounded cursor-pointer hover:bg-gray-100"
                    hx-get="/rate/{rate.get('_id')}"
                    hx-target="#dash-content-pane"
                    hx-trigger="click"
                >
                <h1>{rate.get('_id')} <span class="mx-2">{rate.get('title')}</span></h1>
                <span 
                    class="inline-flex items-center gap-x-1.5 py-1 px-2 rounded-full text-xs w-auto max-w-32 font-medium bg-blue-300 text-gray-600"
                    >{rate.get('category')}
                </span></div></li>             
                """
        yield """</ul></div>       
                
                            <!-- New Rate modal -->
                <div id="new-rate-modal" uk-modal>
                    <div class="uk-modal-dialog uk-modal-body">
                        <h2 class="uk-modal-title">New Industry Rate</h2>
                        <form>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-large" type="text" placeholder="Rate Title" aria-label="Small" name="title">
                            </div>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-medium" type="text" placeholder="Description" aria-label="Medium" name="Description">
                            </div>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-small" type="text" placeholder="Small" aria-label="Small">
                            </div>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-xsmall" type="text" placeholder="X-Small" aria-label="X-Small">
                            </div>

                        </form>
                        
                        <p class="uk-text-right">
                            <button class="uk-button uk-button-default uk-modal-close" type="button">Cancel</button>
                            <button class="uk-button uk-button-primary" type="button">Save</button>
                        </p>
                    </div>
                </div>
            
            """
    else:            
        yield f"""
                <div>
                 <p class="text-center text-xs">Rates Index Html Generator</p>
                <div class="flex flex-row bg-gray-300 py-3 px-4 items-inline text-center rounded relative">
                <span class="cursor-pointer" uk-toggle="target: #new-rate-modal"uk-icon="plus"></span>
                    <p class="mx-5">Industry Rates Index</>               
                    
                     <span class="uk-badge">{len(rates)}</span>
                    <a href class="absolute right-0">Filter <span uk-drop-parent-icon></span></a>
                    <div uk-dropdown="pos: bottom-center">
                    <ul class="uk-nav uk-dropdown-nav">
                     <li class="uk-nav-header">Filter Rates</li>
                     <li><a 
                                href="#"
                                hx-get="/rates_html_index/{'all'}"
                                hx-target="#dash-left-pane"
                                hx-trigger="click"                                 
                                >All Categories</a>
                        </li>
                    """

        for item in categories:
            yield f""" <li>
                                <a 
                                href="#"
                                hx-get="/rates_html_index/{item}"
                                hx-target="#dash-left-pane"
                                hx-trigger="click"                                 
                                >{item}</a></li>"""
                       
                        
        yield f""" </ul>
                </div>                        
                        
                    </div>
                <ul class="uk-list uk-list-striped h-96 p-2 overflow-y-auto">
                """
        
        for rate in rates:
                yield f"""<li>
                <div class="flex flex-col text-sm bg-gray-300 py-2 px-3 my-2 border rounded cursor-pointer hover:bg-gray-100"
                    hx-get="/rate/{rate.get('_id')}"
                    hx-target="#dash-content-pane"
                    hx-trigger="click"
                >
                <h1>{rate.get('_id')} <span class="mx-2">{rate.get('title')}</span></h1>
                <span 
                    class="inline-flex items-center gap-x-1.5 py-1 px-2 rounded-full text-xs w-auto max-w-32 font-medium bg-blue-300 text-gray-600"
                    >{rate.get('category')}
                </span></div></li>             
                """
        yield """</ul></div>       
                
                            <!-- New Rate modal -->
                <div id="new-rate-modal" uk-modal>
                    <div class="uk-modal-dialog uk-modal-body">
                        <h2 class="uk-modal-title">New Industry Rate</h2>
                        <form>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-large" type="text" placeholder="Rate Title" aria-label="Small" name="title">
                            </div>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-medium" type="text" placeholder="Description" aria-label="Medium" name="Description">
                            </div>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-small" type="text" placeholder="Small" aria-label="Small">
                            </div>

                            <div class="uk-margin">
                                <input class="uk-input uk-form-width-xsmall" type="text" placeholder="X-Small" aria-label="X-Small">
                            </div>

                        </form>
                        
                        <p class="uk-text-right">
                            <button class="uk-button uk-button-default uk-modal-close" type="button">Cancel</button>
                            <button class="uk-button uk-button-primary" type="button">Save</button>
                        </p>
                    </div>
                </div>
            
            """
       

class rateManager:
    id:str = None
    PROPERTIES_INDEX:list = ['about', 'index', 'categories', 'model']
    def __init__(self, id:str=None, filter:str=None, properties:list=[]):
        self.id = id
        self.properties = properties
        self.filter = filter
        
        
    async def load_data(self):
        self.rate = await get_industry_rate(id=self.id)

    async def load_rates(self):
        self.rates = await all_rates()

    async def filter_rates(self):        
        if self.filter:            
            if self.filter == 'all' or self.filter == 'None':            
                return self.rates
            else:                
                return [rate for rate in self.rates if rate.get("category") == self.filter]
 

    async def _template(self, request:Request):
        if self.id in self.PROPERTIES_INDEX:
            #if self.id == 'index':
            await self.load_rates()
            property_search = {
                'index': TEMPLATES.TemplateResponse(page_url('Rates.html'),
                            {
                                "request": request, 
                                "filter": self.filter,
                                "filtered": await self.filter_rates(), 
                                "rates": self.rates, 
                                "categories": {rate.get('category') for rate in self.rates }, 
                                "rate_categories": list(rate_categories().keys())                            
                            }
                        ),
                'categories': TEMPLATES.TemplateResponse(page_url('Categories.html'), 
                            {"request": request, "categories": rate_categories()}
                        ),
                'about': TEMPLATES.TemplateResponse(page_url('About.html'), 
                            {"request": request, "categories": rate_categories()}
                        )
            }
        
            return property_search.get(self.id)
        else:
            pass
        
        await self.load_data()
        search_ = {
            'id': TEMPLATES.TemplateResponse(page_url('Rate.html'), 
                {"request": request, "rate": self.rate }),
            
        }
        if self.properties:
            return search_.get(self.properties[0])
        else:
            return search_.get('id')


