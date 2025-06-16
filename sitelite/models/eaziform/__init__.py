from pathlib import Path
from secrets import token_urlsafe
from pydantic import BaseModel, Field, ConfigDict, ValidationError 
from typing import Generic, TypeVar, Optional, Dict, Any

# Config
T = TypeVar('T', bound=BaseModel)
LOC = Path(__file__).resolve().parent
CSS = LOC /  "site.css"


class FormField(BaseModel):
    """A class to represent a form field"""
    name: str = None
    error: str = None
    value: Optional[Any] | None = None
    
    class Config:
        frozen = True


class Form(BaseModel, Generic[T]):
    """A class to represent a form"""
    csrf: str = token_urlsafe(16)
    fields: Dict[str, FormField]= Field(default_factory=dict)
    model: Optional[T] = None
    

class FormModel(BaseModel):     
    model_config = ConfigDict(json_schema_extra={'icon': 'location-arrow'}) 
    
    def html_form(self, header:str=None, post:str=None, target:str=None, insert:bool=False, form:Form=None, values:bool=False, errors:bool=False):
        """Returns a html form of the model 

        Args:
            insert (bool, optional): to insert css and icons resources or use local resources.
        """
        form_html:str =""
        for i in  self.generate_html_form(header=header, post=post, target=target, insert=insert, form=form, values=values, errors=errors):
            form_html = form_html + i
        return  form_html
    
   # Forms Generator
    def generate_html_form(self, header:str=None, form:Form=None, post:str=None, target:str=None, insert:bool=False,  values:bool=False, errors:bool=False):
            """Generates a Html form of the instantiated model"""  
            with open(CSS) as file:
                scss = file.read() 
                
            if form:
                pass
            else:
                form = self.data_form()          
            if not insert:
                yield f"""<!DOCTYPE html><html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>PerForm </title>
                    <link rel="stylesheet" href="/static/fontawesome/css/fontawesome.css" />
                    <link rel="stylesheet" href="/static/fontawesome/css/brands.css" />
                    <link rel="stylesheet" href="/static/fontawesome/css/solid.css" />
                    <link rel="stylesheet" href="/static/fontawesome/css/svg-with-js.css" />                   
                   
                    <style>{scss}</style>
                     
                </head>
                <body> """
            yield f"""<div class="text-lg my-5 mx-5">{header}</div><div id="eaziform"> """
            if post and target:
                yield f"""<div style="margin:50px;"><form method="POST" hx-post="{post}" hx-target="#{target}">"""
            else:
                yield """<div style="margin:50px;"><form method="POST">"""
            yield f"""          
                <input type="hidden" name="csrf" value="{form.get('csrf')}" />"""
            yield f""" <h3 class="title is-4">{ self.model_json_schema().get('title')}</h3> """
            
            for key, value in self.model_json_schema().get('properties').items():                
                if value.get('$ref'):
                    pass
                else:
                    yield f""" <fieldset class="fieldset">                    
                    <label class="label" for="{key}">{value.get('title')}<span class="fa fa-{value.get('icon')}"></span>"""
                    # Numerical Input Fields...
                    if value.get('type') == 'number':                        
                        if values:
                            yield f""" <input class="input is_primary" type="number" step="0.001" name="{key}" id="{key}" placeholder="{value.get('title')}" value="{form.get('fields', {}).get(key, {}).get('value')}" />"""
                        else:
                            yield f""" <input class="input is_primary" type="number" step="0.001" name="{key}" id="{key}" placeholder="{value.get('title')}"  />"""
                       
                        if errors and form.get('fields', {}).get(key, {}).get('error'):
                            yield f"""</label> <div class="text-xs text-red-500 font-semibold">{form.get('fields', {}).get(key, {}).get('error')}</div></fieldset>"""
                        else:
                            yield """</label></fieldset>"""
                        # Checkbox Fields...
                    elif value.get('type') == 'boolean':
                        
                        if not value.get('default'):
                            yield f"""<input type="checkbox" name="{key}" id="{key}"  class="checkbox checkbox-primary checkbox-sm" />"""
                        else:
                            yield f"""<input type="checkbox" name="{key}" id="{key}"  checked="checked" class="checkbox checkbox-primary checkbox-sm" />"""
                        yield f""" {key}
                            </label>
                        </fieldset>"""
                        # do further checks for file upload field, radio buttons, fields etc...
                        # Select Fields...
                    elif value.get('options'):
                        yield f""" <select name="{key}" id="{key}" class="select">
                                <option disabled selected>Pick a {value.get('title')}</option>"""
                        for option in value.get('options'):
                            yield f"""<option>{option}</option>"""                               
                        yield " </select></fieldset>"
                    # Range Fields...
                    elif value.get('range'):
                        yield f"""<output class="range-output" for="{key}"></output>
                        <input type="range" min="{value.get('min')}" max="{value.get('max')}" step="{value.get('step')}" name="{key}" id="{key}" value="{value.get('default')}"  />
                        </label></fieldset>
                        <script type="module">
                            const range = document.querySelector("#{key}");
                            const output = document.querySelector(".range-output");

                            output.textContent = range.value;"""

                        yield """ range.addEventListener("input", () => {output.textContent = range.value; });
                        </script>
                        """

                    else:
                        # Text, Email, Password  Input Fields...
                        if values:
                            yield f""" <input class="input is_primary" type="{value.get('type')}" name="{key}" id="{key}" placeholder="{value.get('title')}" value="{form.get('fields', {}).get(key, {}).get('value')}" hx-post="{post}" hx-trigger="keyup changed delay:500ms" hx-target="#{target}" />"""
                        else:
                            yield f""" <input class="input is_primary" type="{value.get('type')}" name="{key}" id="{key}" placeholder="{value.get('title')}" hx-post="{post}" hx-trigger="keyup changed delay:1000ms" hx-target="#{target}" />"""
                                         
                        if errors and form.get('fields', {}).get(key, {}).get('error'):
                            yield f"""</label> <div class="text-xs text-red-500 font-semibold">{form.get('fields', {}).get(key, {}).get('error')}</div></fieldset>"""
                        else:
                            yield """</label></fieldset>"""
            # process the nested fields
            if self.model_json_schema().get('$defs'):
                yield """<div class="join join-vertical bg-base-100">"""
               
                for key2, value2 in self.model_json_schema().get('$defs').items():
                    yield f"""<div class="collapse collapse-arrow join-item border-base-300 border">
                        <input type="radio" name="my-accordion-0"/>                    
                        <div class="collapse-title font-semibold"> <div class="badge badge-outline badge-primary ">{key2}</div></div>
                        <div class="collapse-content text-sm">""" 
                                       
                    for key3, value3 in value2.get('properties').items():
                        yield f"""<fieldset class="fieldset">        
                            <label class="label" for="{key3}">{value3.get('title')}<span class="fa fa-{value3.get('icon')}"></span>"""
                        if value3.get('type') == 'number':
                            if values:
                                yield f"""
                                    <input  class="input is_primary" type="{value3.get('type')}" step="0.001" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" value="{form.get('fields', {}).get(key3, {}).get('value')}" />"""
                            else:
                                yield f"""<input  class="input is_primary" type="number" step="0.001" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" />"""
                                                
                            if errors and form.get('fields', {}).get(key3, {}).get('error'):
                                yield f"""</label> <div class="text-xs text-red-500 font-semibold">{form.get('fields', {}).get(key3, {}).get('error')}</div></fieldset>"""
                            else:
                                yield """</label></fieldset>"""
                        
                        elif value3.get('type') == 'boolean':
                        
                            if not value3.get('default'):
                                yield f"""<input type="checkbox" name="{key3}" id="{key3}"  class="checkbox checkbox-primary checkbox-sm" />"""
                            else:
                                yield f"""<input type="checkbox" name="{key3}" id="{key3}"  checked="checked" class="checkbox checkbox-primary checkbox-sm" />"""
                            yield f""" {key3}
                                </label>
                            </fieldset>"""
                        elif value3.get('options'):
                            yield f""" <select name="{key3}" id="{key3}" class="select">
                                    <option disabled selected>Pick a {value3.get('title')}</option>"""
                            for option in value3.get('options'):
                                yield f"""<option>{option}</option>"""                               
                            yield "</select></fieldset>"

                        # do further checks for file upload field, radio buttons,select fields etc...
                        else:  
                                                      
                            if values:
                                yield f""" <input  class="input is_primary" type="{value3.get('type')}" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" value="{form.get('fields', {}).get(key3, {}).get('value')}"/>"""
                            else:
                                yield f""" <input  class="input is_primary" type="{value3.get('type')}" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" />"""
                                                                             
                            if errors and form.get('fields', {}).get(key3, {}).get('error'):
                                yield f"""</label><div class="text-xs text-red-500 font-semibold">{form.get('fields', {}).get(key3, {}).get('error')}</div></fieldset>"""
                            else:
                                yield """</label></fieldset>"""
                    yield """</div>"""
                yield """</div>"""                 
                    
            yield """<div class="field flex flex-row is-grouped mt-5">
                        <div class="control">
                            <input type="submit" class="btn btn-primary rounded-md btn-sm" value="Submit"></input>
                        </div>
                        <div class="control mx-5">
                            <button class="btn btn-outline btn-sm rounded-md">Cancel</button>
                        </div>
                    </div>
                    </form>
                    </div>
                    
                    <p class="text-xs text-blue-500 font-fine mt-5"><strong>Forms By EaziForm&reg </strong></p>
                    """
            if not insert: 
                yield """<script src="https://unpkg.com/htmx.org@2.0.4" integrity="sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+" crossorigin="anonymous"></script>
                        </div></body></html>"""

    
    @property        
    def model_data(self)->set:        
        return dict(self.model_dump())
    
    @property        
    def model_nested_fields(self)->list:        
        # checking for nested fields
        def_props:list = []
        if '$defs' in self.json_schema.keys():
            defs:dict = self.json_schema.get('$defs')
            def_keys:list = defs.keys()
            for m_field in def_keys:
                def_props.append(defs.get(m_field).get('properties'))
        return def_props 
        
    
    @property        
    def formfields(self)->set: 
        
        # checking for nested fields
        def_props:list = []
        if '$defs' in self.json_schema.keys():
            defs:dict = self.json_schema.get('$defs')
            def_keys:list = defs.keys()
            for m_field in def_keys:
                def_props.append(defs.get(m_field).get('properties').keys())
            nested_form_fields = set([item for row in def_props for item in row])
            return self.model_fields_set.union(nested_form_fields)
        else:
            return self.model_fields_set
        
    
    @property
    def json_schema(self):
        return self.model_json_schema()
    
    
    def data_form(self)->dict:
        pd_form:Form = Form(model=self)
        for field in self.formfields:
            pd_form.fields[field] = FormField(name=field, value=pd_form.model.model_dump().get(field))
        return pd_form.model_dump()
    
    
    def validateRequestData(self, data:dict=None):

        """Validates data returned from the request object
        expected form data ex. 
        FormData([('csrf', 'DEc3T68GVHgelV8SW5UZBA'), ('name', 'Mar a Largo'), ('age', '52')])
        Args:
            request (_type_, optional): _description_. Defaults to None.
        Returns:
            _type_: _description_
        """
        try:
            model:BaseModel = self.model_validate( data ) #.model_validate(mf)
            return model
        except ValidationError as e:        
            return {'ERROR': e.json()}  
                 
   
    async def validateForm(self, header:str=None,request_data:dict=None, schema:BaseModel=None, post:str=None, target:str='eaziform', insert:bool=False, json_data:bool=False): 
        """Validates the form data and returns a HTML form with errors if any.
        Args:   
            request_data (dict, optional): raw key values returned from the generated html model form. Defaults to None.
            schema (BaseModel, optional):Model schema of the Form's data model. Defaults to None.  
            json_data (bool, optional):opt to return a json representation of the data . Defaults to False.
        Returns:        
            _type_:Returns the  FormData with error field or an Html of the result if Json_data is set to False
        """
        from json import loads
        data = request_data
        modeled_data = schema().model_data 
        for key, value in modeled_data.items():
            if type(value) is dict:
                for key2 in value.keys():
                    if key2 in data:
                        value[key2] = data.get(key2)
                    else:
                        pass
            else:
                modeled_data[key] = data.get(key)        
        result = self.validateRequestData(data=modeled_data)
        if 'ERROR' in result: #.get('ERROR'):
            errors = loads(result.get('ERROR'))
            pd_form:Form = Form()
            data = dict(data)
            for key, value in data.items():
                if key == 'csrf':
                    pass
                else:
                    for err in errors:
                        if key in err.get('loc'):
                            pd_form.fields[key] = FormField(name=key, error=err.get('msg') ,value=value)
                        else:
                            pd_form.fields[key] = FormField(name=key, value=value)
            pd_form.csrf = data.get('csrf')
            pd_form.model = schema
            form = schema()            
            form_html = form.html_form(header=header, post=post, target=target, insert=insert, form=pd_form.model_dump(), values=True, errors=True)
            return form_html
            #return pd_form #pd_form #dict(data)
        
        if json_data:
            return result.model_dump()            
            
        else:
            return  f"""<div class="card w-96 bg-base-100 card-xs shadow-sm">
                                    <div class="card-body">
                                        <h2 class="card-title">Data Exchange</h2>
                                        <p>{result}</p>
                                        <p class="text-xs text-blue-500">{data}</p>
                                        
                                        <div class="justify-end card-actions">
                                        <button class="btn btn-success btn-sm">Success</button>
                                        </div>
                                    </div>
                        </div>"""


if __name__ == '__main__':
    print('EaziForm  Auto generated  Forms ')
    
    