# SitePlan-lite Application configuration File
# April 23 2025

from pathlib import Path
from starlette.config import Config
from starlette.datastructures import Secret
from starlette.templating import Jinja2Templates
from modules.utils import converTime, convert_timestamp, to_dollars, to_project_id


# Documents Paths
BASE_PATH:Path = Path(__file__).parent.parent
STATIC_PATH:Path = BASE_PATH / 'static'
TEMPLATES_PATH:Path = BASE_PATH / 'templates'

DOCS_PATH:Path = STATIC_PATH / 'docs'
IMAGES_PATH:Path = STATIC_PATH / 'imgs'
MAPS_PATH:Path = STATIC_PATH / 'maps'
PROFILES_PATH:Path = IMAGES_PATH / 'workers'
DATA_PATH:Path = BASE_PATH.parent / 'SiteLiteData'
# Logs
LOG_PATH:Path = Path.joinpath(BASE_PATH, 'logs')
SYSTEM_LOG_PATH:Path = Path.joinpath(LOG_PATH, 'system.log')
SERVER_LOG_PATH:Path = Path.joinpath(LOG_PATH, 'server.log')
APP_LOG_PATH:Path = Path.joinpath(LOG_PATH, 'app.log')


# File Paths
ENV_PATH:Path = Path.joinpath(BASE_PATH, '.env') 
# Certificate and Key paths
CERT_PATH:Path = BASE_PATH / 'keys'
# Icons Path
ICONS_PATH:Path = IMAGES_PATH / 'icons' 
FAVICON_PATH:Path = ICONS_PATH / 'favicon-16x16.png'
# Application Secrets
__config:Config = Config(ENV_PATH)

# Application Specific Settings

DEBUG:bool = True
DATABASE_URL:str = 'http://localhost:5984/'
SECRET_KEY:Secret = __config('SECRET_KEY',  cast=Secret)
DB_ADMIN:Secret  = __config('DB_ACCESS',  cast=Secret)
ADMIN_ACCESS:Secret  = __config('DB_SECRET',  cast=Secret)

# Network
ALLOWED_HOSTS:list = ['127.0.0.1', 'localhost']
PORT:int = 9092
HOST:str = '0.0.0.0'

# Templates Engine
TEMPLATES = Jinja2Templates(TEMPLATES_PATH)



env = TEMPLATES.env
env.filters['to_dollars'] = to_dollars
env.filters['convert_timestamp'] = convert_timestamp
env.filters['convert_time'] = converTime
env.filters['to_project_id'] = to_project_id



