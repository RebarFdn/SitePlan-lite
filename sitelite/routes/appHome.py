from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from config import TEMPLATES
from starlette.routing import Mount,Route, WebSocketRoute
from pydantic import BaseModel, Field, ValidationError,field_validator
from models.auth_models import Password, RegisterUser
from models.form_model import ModelForm

# Application Home Page

class MyForm(ModelForm):
    name: str = Field(default=None, min_length=1)
    age: int = None

    @field_validator('age')
    @classmethod
    def age_must_be_over_30(cls, value, values):
        if value <=30:
            raise ValueError("30's are your new 20's")
        return value





async def HomePage(request:Request):
    return TEMPLATES.TemplateResponse('/index.html', {'request': request})


async def Register(request:Request):
    '''  '''
    if request.method == 'POST':
        form = await request.form() 
        if MyForm.model_validate_json(form):
            model = MyForm( **form )
            return HTMLResponse(f"<p>Hello {model.name} you are { model.age } years old.</p>")
        else:
            return TEMPLATES.TemplateResponse('user_form.html', {"request":request, 'form': form})
        """
                data = RegisterUser( 
                    name=form.get('name'),
                    username=form.get('username'), 
                    email=form.get('email'), 
                    password=form.get('password') 
                )
        """
        
    else:
        #dataForm = await PydanticForm.create(request, MyForm)
        form = MyForm().html_form()
        return form



# routes aggregator
routes:list = [
    # WebSocketRoute("/pws", ws_project),
    Route('/', endpoint=HomePage),
    Route('/register', endpoint=Register, methods=['GET', 'POST'])
    
    ]
