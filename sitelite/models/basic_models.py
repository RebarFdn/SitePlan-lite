from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.country import CountryShortName 
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator
from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4
from typing import List, Any, Annotated
from decimal import Decimal


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
    bank: Bank | None = None
    transactions: list = []




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
    
