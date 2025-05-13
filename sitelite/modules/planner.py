import os
from typing import Coroutine, List
from asyncio import sleep
from starlette.requests import Request
from starlette_wtf import StarletteForm
from wtforms import StringField, SelectField, DateField , Form, FormField
from wtforms.validators	import DataRequired

from pydantic import BaseModel, EmailStr
from database import Recouch, local_db
from logger import logger
from modules.utils import timestamp, load_metadata, set_metadata, generate_id
from models import Address, Contact
from config import TEMPLATES, PLANNING


_databases:dict = { # Project Databases
            "local":"planning_dept", 
            "local_partitioned": False,
            "slave":"planning_dept", 
            "slave_partitioned": False            
            }
# connection to the planning_dept database 
db_connection:Coroutine = local_db(db_name=_databases.get('local'))  


def plan_dir():
    os.chdir(PLANNING)
    dirs = os.listdir()
    return dirs

def planModel(key:str=None)->dict:
    """A Json model of an Architectural Plan Model

    Args:
        key (str, optional): _description_. Defaults to None.

    Returns:
        dict: _description_
    """
    PLAN = {
        'name': None,
        
    }


class Address(BaseModel):
    lot: str | None = None
    street: str | None = None
    town: str | None = None
    city_parish: str | None = None
    zip: str | None = None


class Contact(BaseModel):
    tel: str | None = None
    mobile: str | None = None
    email: EmailStr | None = None
    watsapp: str | None = None

class Location(BaseModel):
    lat: float
    long: float

class ClientOwner(BaseModel):
    name:str 
    address:Address | None = None
    contact: Contact | None = None


class Draftsman(BaseModel):
    name:str 
    trn: str
    address:Address | None = None
    contact: Contact | None = None

class Designer(BaseModel):
    name:str 
    address:Address | None = None
    contact: Contact | None = None


# Plan Model
class BuildingPlan(BaseModel):
    name:str | None = None
    no:str = None
    date:str | None = None
    category:str | None = None
    address:Address | None = None
    location:Location | None = None
    owners:List[ClientOwner] | None = None
    draftsman:Draftsman | None = None
    designer: Designer | None = None
    checked_by: str | None = None

    def generate_id(self):
        self.id = generate_id(name=self.name)

## Address Form
class AddressForm(StarletteForm):
    lot = StringField("Lot", validators=[DataRequired()])
    street = StringField("Street", validators=[DataRequired()])
    town = StringField("Town", validators=[DataRequired()])
    city_parish = StringField("City or Parish", validators=[DataRequired()])
    zip = StringField("ZIP", validators=[DataRequired()])


## Planning Registration Form
class PlanForm(StarletteForm):
    name = StringField('name', validators=[DataRequired()])
    date = DateField('Date')
    category = SelectField('Building Category', choices=['residential', 'commercial', 'governmental', 'charity'])    
    checked_by = StringField('Checked By', validators=[DataRequired()])


# CRUD OPERATIONS

async def all_plans( conn:Coroutine=db_connection )->list:
    try:
        plans:dict = await conn.get(_directive="_design/project-index/_view/name-view") 
        return plans.get('rows')          
    except Exception as e:
        logger().error( str(e))
    finally: del(plans)