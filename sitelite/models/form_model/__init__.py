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
                        <input class="input is_primary" type="{value.get('type')}" step="0.001" name="{key}" id="{key}" placeholder="{value.get('title')}" />
                         <span class="icon is-small is-left">
                            <i class="fas fa-{value.get('icon')}"></i>
                        </span>                      
                        
                        </div>                        
                        """
                    if key == 'password':
                        yield f"""<div class="control has-icons-left">
                        <input class="input is_primary" type="{key}" name="{key}" id="{key}" placeholder="{value.get('title')}" />
                         <span class="icon is-small is-left">
                            <i class="fas fa-{value.get('icon')}"></i>
                        </span>                      
                        
                        </div>                        
                        """

                        ## if value.validation_error:
                            # yield f""" <span class="is-size-7 has-text-danger has-text-weight-bold">{value.get(errors)[0]}</span>
                    # do further checks for file upload field, radio buttons, checkboxes,select fields etc...
                    else:
                        yield f"""<div class="control has-icons-left"> <input class="input is_primary" type="{value.get('type')}" name="{key}" id="{key}" placeholder="{value.get('title')}" />
                        <span class="icon is-small is-left">
                            <i class="fas fa-{value.get('icon')}"></i>
                        </span>                      
                        
                        </div>"""
            # process the nested fields
            if self.model_json_schema().get('$defs'):
                yield f"""<div class="collapse bg-base-100 border border-base-300">
                <input type="radio" name="my-accordion-1" checked="checked" />"""
                for key2, value2 in self.model_json_schema().get('$defs').items():
                    yield f"""<div class="collapse-title font-semibold"> {key2}</div>
                            <div class="collapse-content text-sm">"""                    
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
                    yield """</div>"""
                yield """</div>"""                 
                    
            yield """<div class="field is-grouped mt-5">
                    <div class="control has-icons-left">
                        <input type="submit" button class="button is-link" value="Submit"></input>
                    </div>
                    <div class="control has-icons-left">
                        <button class="button is-link is-light">Cancel</button>
                    </div></div></form></div>"""
            if not insert: 
                yield """</body></html>"""
        return StreamingResponse( generate_form(), media_type="text/html")

    def accordion():
        return """
                <div class="collapse bg-base-100 border border-base-300">
                <input type="radio" name="my-accordion-1" checked="checked" />
                <div class="collapse-title font-semibold">How do I create an account?</div>
                <div class="collapse-content text-sm">Click the "Sign Up" button in the top right corner and follow the registration process.</div>
                </div>
                <div class="collapse bg-base-100 border border-base-300">
                <input type="radio" name="my-accordion-1" />
                <div class="collapse-title font-semibold">I forgot my password. What should I do?</div>
                <div class="collapse-content text-sm">Click on "Forgot Password" on the login page and follow the instructions sent to your email.</div>
                </div>
                <div class="collapse bg-base-100 border border-base-300">
                <input type="radio" name="my-accordion-1" />
                <div class="collapse-title font-semibold">How do I update my profile information?</div>
                <div class="collapse-content text-sm">Go to "My Account" settings and select "Edit Profile" to make changes.</div>
                </div>
        """
    
    def generate_form(self, insert=False):
            """Generate a form for the Location model"""
            #print(self.model_json_schema())
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
            return None
