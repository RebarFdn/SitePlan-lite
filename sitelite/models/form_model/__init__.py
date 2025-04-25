from typing import Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, ValidationError
from starlette.responses import StreamingResponse


class ModelForm(BaseModel):     
    model_config = ConfigDict(json_schema_extra={'icon': 'location-arrow'})  
    
    def form(self, insert:bool=False):
        """Generate a form for the Location model
        Args:
            request (Request): The request object
        Returns:
            HTMLResponse: The HTML response with the form
        """
        print("Generating form")
        
        def generate_form():
            """Generate a form for the Location model"""
            #print(self.model_json_schema())
            if not insert:
                yield """<!DOCTYPE html><html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{{ title }} </title>
                    <link rel="stylesheet" href="/static/fontawesome-free-6.7.2-web/css/fontawesome.css" />
                    <link rel="stylesheet" href="/static/fontawesome-free-6.7.2-web/css/brands.css" />
                    <link rel="stylesheet" href="/static/fontawesome-free-6.7.2-web/css/solid.css" />
                    <link rel="stylesheet" href="/static/fontawesome-free-6.7.2-web/css/svg-with-js.css" />
                    <link rel="stylesheet" type="text/css" href="/static/css/bulma-1.0.2/bulma/css/bulma.min.css">                    
                    <link rel="stylesheet" type="text/css" href="/static/uikit-3/css/uikit.min.css">
                     <script src="/static/uikit-3/js/uikit.min.js"></script>
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
                        <input class="input is_primary" type="{value.get('type')}" step="0.001" name="{key}" id="{key}" value="{getattr(self, key)}" />
                         <span class="icon is-small is-left">
                            <i class="fas fa-{value.get('icon')}"></i>
                        </span>                      
                        
                        </div>                        
                        """
                        ## if value.validation_error:
                            # yield f""" <span class="is-size-7 has-text-danger has-text-weight-bold">{value.get(errors)[0]}</span>
                    # do further checks for file upload field, radio buttons, checkboxes,select fields etc...
                    else:
                        yield f"""<div class="control has-icons-left"> <input class="input is_primary" type="{value.get('type')}" name="{key}" id="{key}" value="{getattr(self, key)}" />
                        <span class="icon is-small is-left">
                            <i class="fas fa-{value.get('icon')}"></i>
                        </span>                      
                        
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
                            yield f"""<div class="control has-icons-left"> <input  class="input is_primary" type="{value3.get('type')}" step="0.001" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" /><span class="icon is-small is-left">
                            <i class="fas fa-{value3.get('icon')}"></i>
                        </span>                      
                        
                            </div>"""
                        # do further checks for file upload field, radio buttons, checkboxes,select fields etc...
                        else:
                            yield f"""<div class="control has-icons-left"> <input  class="input is_primary" type="{value3.get('type')}" name="{key3}" id="{key3}" placeholder="{value3.get('title')}" /><span class="icon is-small is-left">
                            <i class="fas fa-{value3.get('icon')}"></i>
                        </span></div>
                                   
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
        return StreamingResponse( generate_form(), media_type="text/html")
    
    def validate(self, value: Any) -> Any:        
        try:
            model = Model(**value)
            print(model)
        except ValidationError as ero:
            error_locations = ero.errors() #[e['loc'] for e in ero.errors()]
            print("PydanticUserError", error_locations)
            return ero.errors()
        return value
    
    
    def process_form(self, form):
        nested = self.model_json_schema().get('$defs')
        
        try:
            model = self(**data)
            print(model)
        except ValidationError as ero:
            error_locations = ero.errors() #[e['loc'] for e in ero.errors()]
            print("PydanticUserError", error_locations)
        
        return {"nested": nested.keys(), "form": form }

