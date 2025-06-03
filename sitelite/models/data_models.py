## Application Data Models
from datetime import date, datetime
from enum import Enum
from uuid import uuid4, UUID
from typing import List, Any
from functools import lru_cache
from pydantic import BaseModel, EmailStr, Field,  SecretStr, AliasChoices
from pydantic_extra_types.country import CountryShortName 
from pydantic_extra_types.phone_numbers import PhoneNumber
from eaziform import FormModel
try:
    from modules.utils import generate_id, timestamp, tally
except ImportError:
    pass
#from sitelite.modules.utils import generate_id, timestamp
from modules.site_db import SiteDb

def doc_count()->int:
        db = SiteDb(db_name="temp_invoice")
        return db.doc_count() + 1


class Department(Enum):
    HR = 'HR'
    SALES = 'SALES'
    IT = 'IT'
    ENGINEERING = 'ENGINEERING'
    CONSTRUCTION= 'CONSTRUCTION'


class Roles(Enum):
    ADMIN = 'ADMIN'
    GUEST = 'GUEST'
    USER = 'USER'
    STAFF = 'STAFF'
    WORKER = 'WORKER'


class Address(BaseModel):
    lot: str | None = None
    street: str = Field(default=None, min_length=2, max_length=12) 
    town: str = Field(default=None, min_length=2, max_length=12)
    city_parish: str = Field(default=None, min_length=5, max_length=20)
    country:CountryShortName | None = None
    zip: str | None = Field(default=None, min_length=3, max_length=6)


class Contact(BaseModel):
    """Usage Contact(tel="+18762982925")
    """
    tel: PhoneNumber | None = None
    mobile: PhoneNumber | None = None
    email: EmailStr | None = None
    watsapp: PhoneNumber | None = None


## Financial and Accounting Models

class Bank(BaseModel):
    name: str = Field(default=None, min_length=2, max_length=32) 
    branch: str = Field(default=None, min_length=2, max_length=32)
    account: str = Field(default=None, min_length=2, max_length=16)
    account_type: str = Field(default="savings",  max_length=16)


class Loan(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    date: date = None
    amount:float = Field(default=None, max_digits=4)
    borrower: str = Field(default=None, min_length=2, max_length=32)
    refference:str = Field(default=None, min_length=2, max_length=8)


class Payment(BaseModel):
    id: str
    date:date
    amount:float
    payee:str
    refference:str


class EmployeeAccount(BaseModel):
    bank: Bank | None = None
    payments: List[Payment]
    loans: List[Loan]


class CommercialAccount(BaseModel):
    bank: Bank = Bank() 
    transactions: list = []


class DepositModel(BaseModel):
    id:str = Field(default=generate_id(name='account deposit') )
    date:int = timestamp()
    type:str = Field(default="deposit")
    ref:str = None
    amount:float = None
    payee:str = None
    user:str = Field(default="Ian")

class WithdrawalModel(BaseModel):
    id:str = Field(default=generate_id(name='account withdraw') )
    date:int = timestamp()
    type:str = Field(default="withdrawal")
    ref:str = None
    amount:float = None
    recipient:str = None
    user:str = Field(default="Ian")
 
class ExpenceModel(BaseModel):
    id:str = Field(default=generate_id(name='account expence') )
    ref:str = None
    date:int = timestamp()
    description:str = Field(default=None)
    claimant:str = None
    total:float = None
    method:str = Field(default="cash")    
    user:str = Field(default="Ian")


# Account Paybill related models
class BillFees(BaseModel):
    contractor:int = Field(default=0)
    insurance:int = Field(default=0)
    misc:int = Field(default=0)
    overhead:int = Field(default=0)
    unit:str = Field(default="%")


class BillExpence(BaseModel):
    contractor:float = Field(default=0.001)
    insurance:float = Field(default=0.001)
    misc:float = Field(default=0.001)
    overhead:float = Field(default=0.001)
    total:float = Field(default=0.001)

 
class PaybillModel(BaseModel):
    id:str = Field(default=generate_id(name='pay bill') ) # Bill internal id
    ref:str = Field(default=None)   # Bill to job refference no
    project_id:str = Field(default=None) # Current project _id
    date:int = Field(default=timestamp())  # Paybill generation date
    date_starting:int = Field(default=timestamp()) # Work period starting
    date_ending:int = Field(default=timestamp())   # Work period ending
    mainTitle:str = Field(default=None) # Bill heading
    subTitle:str = Field(default=None)  # Bill sub headings
    itemsTotal:float = Field(default=0.001)   # Bill items total
    total:float = Field(default=0.001)   # Bill Total
    items:list = []    
    days_work:list = []
    user:str = Field(default="Ian")
    expence:BillExpence = BillExpence()
    fees:BillFees = BillFees()


class Supplier(BaseModel):
    id: str = Field(default=None, validation_alias=AliasChoices('id', '_id'))
    name:str = Field(default=None)     
    taxid: str = Field(default=None)

    


class InvoiceItem(BaseModel):
    iid:str = Field(default=generate_id(name='invoice item'))
    itemno:int = Field(default=doc_count())  
    description:str = Field(default=None) 
    quantity:float = Field(default=0.01) 
    unit:str = Field(default=None) 
    price:float = Field(default=0.01)    


class InvoiceModel(BaseModel):
    inv_id: str = Field(default=generate_id(name='purchase invoice'))
    supplier:Supplier = Supplier()
    invoiceno:str = Field(default= None) 
    date:int = Field(default=timestamp()) 
    items:list = []
    tax:float = Field(default=0.001) 
    total:float = Field(default=0.001) 
    billed:bool = Field(default=False) 

   



class InventoryItem(BaseModel):   
    ref:str=None
    name:str
    amt:int
    unit:str
    stocking_date:str = None
    supplier:Supplier


class Inventory(BaseModel): 
    id:UUID = uuid4()
    name:str
    items:list = []
    dispenced:list = []
    
    @property
    def stocking(self)->list:
        stocking_:list = [item.get('amt') for item in self.items ]
        return stocking_
    
    @property
    def stock(self):        
        return sum(self.stocking)
    
    @property
    def stock_usage(self)->int:           
        store = 0
        if len(self.dispenced) > 0:
            for item in self.dispenced:
                store += item[1]                
        else: pass
        return store
    
    @property
    def available_stock(self):       
        return self.stock - self.stock_usage


class Identity(BaseModel):
    identity: str | None = None
    id_type: str | None = None
    trn: str | None = None

class Occupation(BaseModel):
    occupation: str | None = None
    rating: float | None = None  

class JobTasks(BaseModel):
    jobs: List[ str ]
    tasks: List[ str ]
    

# Password Model
class Password(BaseModel):
    password: SecretStr = Field(
        default=None, min_length=6, max_length=12,
        json_schema_extra={"icon": "shield", "help": "Password should be between 6 and 12 letters."} 
    )
    def validate(self, value:Any) -> Any:
        try:
            model = Password( **value )
        except ValidationError as ero:
            error_locations = ero
            return error_locations
        return value
    

# Registration Model
class RegisterUser(FormModel):
    name: str = Field(default=None, min_length=3, max_length=32)
    username: str = Field(default=None, min_length=3, max_length=8)
    email: EmailStr = None
    password:SecretStr = Field(
        default=None, min_length=6, max_length=12,
        json_schema_extra={"icon": "shield", "help": "Password should be between 6 and 12 letters."} 
    )
    

    def validate(self, value:Any) -> Any:
        try:
            model = RegisterUser( **value )
        except ValidationError as ero:
            error_locations = ero.errors
            return error_locations
        return value


class NextOfKin(BaseModel):
    name: str | None = None
    relation: str | None = None
    address: Address | None = None
    contact: Contact | None = None

class EmployeeState(BaseModel):
    employed: bool = False    
    on_leave: bool = False
    terminated: bool | None = False
    active: bool | None = False
    

class EmployeeEvent(BaseModel):
    employed: date | None = None
    started: date | None = None
    on_leave: List[ date ] | None = None
    resumption: List[ date ] | None = None
    terminated: date | None = None


class EmployeeStats(BaseModel):
    sex: str | None = None
    dob: date | None = None
    height: str | None = None


class EmployeeModel(BaseModel):
    employee_id:UUID = uuid4() 
    _id:str | None = None
    name: str
    oc: str | None = None
    identity: Identity | None = None
    stats: EmployeeStats | None = None
    occupation: Occupation | None = None
    added: date | None = None      
    imgurl: str | None = None    
    address: Address | None = None
    contact: Contact | None = None
    account: EmployeeAccount | None = None
    nok: NextOfKin | None = None
    jobtask: JobTasks 
    state: EmployeeState | None = None
    event: EmployeeEvent | None = None
    department: Department | None = None
    role: Roles | None = None


class MaterialSupplier(BaseModel):
    id: str = Field(default=None )
    name:str = Field(default=None)     
    taxid: str = Field(default=None)
    account:CommercialAccount = CommercialAccount()
    address:Address = Address()
    contact: Contact = Contact()


class ProjectClient(BaseModel):
    name:str
    contact: Contact | None = None
    address: Address | None = None
        


class Project(BaseModel):
    name: str
    id:str = None
    category:str
    standard:str
    address:Address | None = None
    owner:ProjectClient | None = None
    

    def generate_id(self):
        self.id = generate_id(name=self.name)


# A standard project Template        
def project_template(key:str=None):
    """A standard Project Template 
    representing a the most common elements of a 
    construction project.

    Args:
        key (str, optional): an element of the construction project. Defaults to None.
    
    Usage:
        >>> project_template('address')
        --- {'lot': None, 'street': None, ...}
    """
    PROJECT_TEMPLATE = dict( 
                name = "Test Project",
                category = "residential",
                standard = "metric",
                address = {"lot": None, "street": None, "town": None,"city_parish": None,"country": "Jamaica", },
                owner = {
                "name": None,
                "contact": None,
                "address": {"lot": None, "street": None, "town": None,"city_parish": None,"country": None, }
            },
                account = {
                    "bank": {
                        "name": None,
                        "branch": None,
                        "account": None,
                        "account_type": None
                        },
                    "budget": None,
                    "ballance": 0,
                    "started": timestamp(),
                    "transactions": {
                        "deposit": [], 
                        "withdraw": []
                    },
                    "expences": [],
                    "records": {
                        "invoices": [],
                        "purchase_orders": [],
                        "salary_statements": [],
                        "paybills": []
                    }
                },
                admin = {
                "leader": None,
                "staff": {
                "accountant": None,
                "architect": None,
                "engineer":None,
                "quantitysurveyor": None,
                "landsurveyor": None,
                "supervisors": []
                }
    },
                workers = [],
                jobs = [],
                rates = [],
                days = [],
                inventorys = [],            
                events = {
                    "started": 0,
                    "completed": 0,
                    "paused": [],
                    "restart": [],
                    "terminated": 0
                },
                states =  {
                    "active": False,
                    "completed": False,
                    "paused": False,
                    "terminated": False
                },      
                progress =  {
                "overall": None,
                "planning": None,
                "design": None,
                "estimates": None,
                "contract": None,
                "development": None,
                "build": None,
                "unit": None
                },
                activity_logs = [],
                reports = [],
                estimates = [],
                meta_data = None
                
                )
    if key: return PROJECT_TEMPLATE.get(key)
    else: return PROJECT_TEMPLATE

      

def project_phases()->dict:
    """Construction development phases

    Returns:
        dict: key value of project phases
    """        
    return {     
                
            'preliminary':'Preliminary',
            'substructure': 'Substructrue',
            'superstructure': 'Superstructure',
            'floors': 'Floors',
            'roofing': 'Roofing',
            'installations': 'Installations',
            'electrical': 'Electrical',
            'plumbung': 'Plumbing',
            'finishes': 'Finishes',
            'landscaping': 'Landscaping',      
            
    }
   