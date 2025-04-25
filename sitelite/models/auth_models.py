from pydantic import BaseModel, Field, EmailStr, SecretStr, ValidationError, field_serializer
from models.form_model import ModelForm
from typing import Any

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
            error_locations = ero.errors()
            return error_locations
        return value
    

# Registration Model
class RegisterUser(ModelForm):
    name: str = Field(default=None, min_length=3, max_length=32)
    username: str = Field(default=None, min_length=3, max_length=8)
    password:Password = Password()
    email: EmailStr = None


regu = RegisterUser()
print(regu)   
