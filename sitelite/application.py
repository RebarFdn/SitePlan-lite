# SitePlan-lite Application context

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette_compress import CompressMiddleware
from starlette_wtf import CSRFProtectMiddleware
from starlette_htmx.middleware import HtmxMiddleware
from starlette_login.backends import SessionAuthBackend
from starlette_login.login_manager import LoginManager
from starlette_login.middleware import AuthenticationMiddleware
from routes import router
from config import  DEBUG, HOST, PORT, SECRET_KEY
from config import CERT_PATH, DATA_PATH,  DOCS_PATH, IMAGES_PATH, LOG_PATH, MAPS_PATH, PROFILES_PATH, Path
from modules.platformUser import user_list

# Pre Statrtup Tasks
def preStartApp():
    print('Checking for Documents Directory ...')
    if DOCS_PATH.exists():
        pass # delete all files
    else:
        print('Creating Documents Directory ...')
        DOCS_PATH.mkdir()
    if IMAGES_PATH.exists():
        pass
    else:
        print('Creating Images Directory ...')
        IMAGES_PATH.mkdir()
    if MAPS_PATH.exists():
        pass
    else:
        print('Creating Maps Directory ...')
        MAPS_PATH.mkdir()
    if PROFILES_PATH.exists():
        pass
    else:
        print('Creating Profiles Directory ...')
        PROFILES_PATH.mkdir()
    if LOG_PATH.exists():
        pass
    else:
        print('Creating Logs Directory ...')
        LOG_PATH.mkdir()
    if DATA_PATH.exists():
        pass
    else:
        print('Creating Data Directory ...')
        DATA_PATH.mkdir()
    if CERT_PATH.exists():
        pass    
    else:
        print('Creating Certificate Directory ...')
        CERT_PATH.mkdir()
          
    
    
login_manager = LoginManager(redirect_to='login', secret_key=SECRET_KEY)
login_manager.set_user_loader(user_list.user_loader)


# Startup Tasks
def startApp():
    print('Application is starting ... !')
    print('Checking for Database ...')
    print('clearing caches')
    #Mapper().clear_img_cache()
    print('Starting SiteApp Servers ')
    print()
    print('Analysing Router tables....')    
    print('Routes Statistics')
    print('Routes', router.__len__())
    print()
    print('Checking network for Peer Devices ....')
    #asyncio.run(process_network_peers())
    
    
# Shutdown Tasks
def shutdownApp():
    print('Application is shtting down ... !')

app = Starlette(
    debug=DEBUG,    
    middleware=[
    Middleware(SessionMiddleware, secret_key=SECRET_KEY),
    Middleware(CSRFProtectMiddleware, csrf_secret='***REPLACEME2***'),
    Middleware(HtmxMiddleware),
    Middleware(
            AuthenticationMiddleware,
            backend=SessionAuthBackend(login_manager),
            login_manager=login_manager,
            allow_websocket=False,
        ),
    Middleware(CompressMiddleware, 
        zstd_level=6, 
        brotli_quality=6, 
        gzip_level=6, 
        minimum_size=1000 )

    ],
    routes=router,
    on_startup= startApp()
    
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
    allow_origin_regex=None,
    expose_headers=[
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Cedentials",
        "Access-Control-Allow-Expose-Headers",
    ],
    max_age=3600,
)

if __name__ == '__main__':
    from  uvicorn import run
    # Perform pre-startup tasks
    preStartApp()
    
    key_path:Path = CERT_PATH /  "localhost+2-key.pem"
    cert_path:Path = CERT_PATH / "localhost+2.pem"
    # Check if the certificate and key files exist
    if not key_path.exists() or not cert_path.exists():
        print(f"Certificate or key file not found at {key_path} or {cert_path}.")
        try:
            run(
                app=app, 
                host=HOST, 
                port=PORT, 
                ssl_certfile=None, 
                ssl_keyfile=None 
            )
        except Exception as e:
            print(str(e))
    else:
        print(f"Certificate and key file found at {key_path} and {cert_path}.")
        # Start the server with SSL
        try:
            run(
                app=app, 
                host=HOST, 
                port=PORT, 
                ssl_certfile=cert_path, 
                ssl_keyfile=key_path 
            )
        except Exception as e:
            print(str(e))
    print('Server is running ...')
    print('Press Ctrl+C to stop the server.')
    