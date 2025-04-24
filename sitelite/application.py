# SitePlan-lite Application context

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette_wtf import CSRFProtectMiddleware
from starlette_htmx.middleware import HtmxMiddleware
from starlette_login.backends import SessionAuthBackend
from starlette_login.login_manager import LoginManager
from starlette_login.decorator import login_required
from starlette_login.middleware import AuthenticationMiddleware
from routes import router
from config import CERT_PATH, DEBUG, DOCS_PATH, HOST, PORT, SECRET_KEY, Path
from modules.platformUser import user_list

login_manager = LoginManager(redirect_to='login', secret_key=SECRET_KEY)
login_manager.set_user_loader(user_list.user_loader)

# Startup Tasks
def startApp():
    #reset_invoice_repo()
    print('Checking for Documents Directory ...')
    if DOCS_PATH.exists():
        pass # delete all files
    else:
        print('Creating Documents Directory ...')
        DOCS_PATH.mkdir()
    print()
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

    ],
    routes=router,
    on_startup= startApp(),
    on_shutdown= shutdownApp()
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
    import uvicorn
    key_path:Path = CERT_PATH /  "localhost+2-key.pem"
    cert_path:Path = CERT_PATH / "localhost+2.pem"
    try:
        uvicorn.run(
            app=app, 
            host=HOST, 
            port=PORT, 
            ssl_certfile=cert_path, 
            ssl_keyfile=key_path 
        )
    except Exception as e:
        print(str(e))
