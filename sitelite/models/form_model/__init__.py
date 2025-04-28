from typing import Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, ValidationError ,field_validator
from starlette.responses import StreamingResponse,  HTMLResponse



class ModelForm(BaseModel):     
    model_config = ConfigDict(json_schema_extra={'icon': 'location-arrow'})  

    
    def form_template(self, insert:bool=False):
        """Returns a Jinja templated html form of the model 

        Args:
            insert (bool, optional): to insert css and icons resources or use local resources.
        """
        form_html:str =""
        for i in  self.generate_html_form(insert=insert):
            form_html = form_html + i
        return  form_html
    

    def html_form(self, insert:bool=False):
        """Returns a html form of the model 

        Args:
            insert (bool, optional): to insert css and icons resources or use local resources.
        """
        form_html:str =""
        for i in  self.generate_html_form(insert=insert):
            form_html = form_html + i
        return  HTMLResponse(form_html)

    
    def stream_html_form(self, insert:bool=False):
        """Streams the Generated html form for the model
        Args:
            request (Request): The request object
        Returns:
            HTMLResponse: The HTML response with the form
        """
        print("Streaming form")

        return StreamingResponse( self.generate_html_form(insert=insert), media_type="text/html")


    def generate_html_form(self, insert=False):
            """Generates a Html form of the instantiated model"""            
            if not insert:
                yield """<!DOCTYPE html><html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{{ title }} </title>
                    <link rel="stylesheet" href="/static/jscss/fontawesome-free-6.7.2-web/css/fontawesome.css" />
                    <link rel="stylesheet" href="/static/jscss/fontawesome-free-6.7.2-web/css/brands.css" />
                    <link rel="stylesheet" href="/static/jscss/fontawesome-free-6.7.2-web/css/solid.css" />
                    <link rel="stylesheet" href="/static/jscss/fontawesome-free-6.7.2-web/css/svg-with-js.css" />
                    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.4/css/bulma.min.css">
                    <link rel="stylesheet" type="text/css" href="/static/site.css">
                     
                </head>
                <body>"""
            yield """<div style="margin:50px;"><form method="POST">                
                <input type="hidden" name="csrf" value="{{form.csrf}}" />"""
            yield f""" <h3 class="title is-4">{ self.model_json_schema().get('title')}</h3> """
            
            for key, value in self.model_json_schema().get('properties').items():                
                if value.get('$ref'):
                    pass
                else:
                    yield f""" <div class="field">    
                    <label class="label" for="{key}">{value.get('title')}</label>"""
                    if value.get('type') == 'number':
                        yield f"""<div class="control has-icons-left">
                        <input class="input is_primary" type="{value.get('type')}" step="0.001" name="{key}" id="{key}" placeholder="{value.get('title')}" value="{{form.fields[{key}].value}}" />
                         <span class="icon is-small is-left">
                            <i class="fas fa-{value.get('icon')}"></i>
                        </span>                      
                         <div id="error"></div>
                        </div>                        
                        """
                        ## if value.validation_error:
                            # yield f""" <span class="is-size-7 has-text-danger has-text-weight-bold">{value.get(errors)[0]}</span>
                    # do further checks for file upload field, radio buttons, checkboxes,select fields etc...
                    else:
                        yield f"""<div class="control has-icons-left"> <input class="input is_primary" type="{value.get('type')}" name="{key}" id="{key}" placeholder="{value.get('title')}" value="{{form.fields[{key}].value}}" />
                        <span class="icon is-small is-left">
                            <i class="fas fa-{value.get('icon')}"></i>
                        </span>                      
                         <div id="error"></div>
                        </div>"""
            # process the nested fields
            if self.model_json_schema().get('$defs'):
                yield f"""<ul uk-accordion>"""
                for key2, value2 in self.model_json_schema().get('$defs').items():
                    yield f""" <li><a class="uk-accordion-title" href>{key2}</a>
                    <div class="uk-accordion-content">"""                    
                    for key3, value3 in value2.get('properties').items():
                        yield f"""<div class="field">        
                            <label class="label" for="{key3}">{value3.get('title')}</label>"""
                        if value3.get('type') == 'number':
                            yield f"""<div class="control has-icons-left"> <input  class="input is_primary" type="{value3.get('type')}" step="0.001" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" value="{{form.fields[{key3}].value}}" />
                            <span class="icon is-small is-left">
                            <i class="fas fa-{value3.get('icon')}"></i>
                            </span>                      
                             <div>{{ form.fields.[{key3}].error }}</div>
                            </div>"""
                        # do further checks for file upload field, radio buttons, checkboxes,select fields etc...
                        else:
                            yield f"""<div class="control has-icons-left"> 
                            <input  class="input is_primary" type="{value3.get('type')}" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" value="{{form.fields[{key3}].value}}"/>
                            <span class="icon is-small is-left">
                            <i class="fas fa-{value3.get('icon')}"></i>
                            </span>
                             <div>{{ form.fields.[{key3}].error }}</div>
                            </div>
                                   
                            """
                    yield """</div></li>"""
                yield """</ul>"""                 
                    
            yield """<div class="field is-grouped uk-margin-top">
                    <div class="control has-icons-left">
                        <input type="submit" button class="button is-link" value="Submit"></input>
                    </div>
                    <div class="control has-icons-left">
                        <button class="button is-link is-light">Cancel</button>
                    </div></div></form></div>"""
            if not insert: 
                yield """</body></html>"""
            

if __name__ == '__main__':
    
    class MyForm(ModelForm):
        name: str = Field(default=None, min_length=1)
        age: int = None

        @field_validator('age')
        @classmethod
        def age_must_be_over_30(cls, value, values):
            if value <=20:
                raise ValueError("30's are your new 20's")
            return value
        
    mf:dict = {'name': "Anuk Amen-RA", 'age':23} 
    try:
        model = MyForm() #.model_validate(mf)
        print(model.form_template())
        
    except ValidationError as ve:
        print(ve)