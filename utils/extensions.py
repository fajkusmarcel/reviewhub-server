from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



#extensions.py je místo, kde vytvoříš instance rozšíření (bez init_app). Díky tomu:
# - se vyhneš cirkulárním importům,
# - všechna rozšíření spravuješ na jednom místě,
# - v app.py je jen čistá inicializace *.init_app(app).
#
# Priklady
#
# limiter = Limiter(key_func=get_remote_address)
# csrf = CSRFProtect()
# socketio = SocketIO(async_mode='eventlet')
# db = SQLAlchemy()
# migrate = Migrate()
# cache = Cache()
# babel = Babel()

# Vytvoří instanci Flask-Limiteru a určí, jak se identifikuje klient.
# get_remote_address vrací IP adresu (respektuje ProxyFix / X-Forwarded-For).
# Tuhle instanci je lepší držet v extensions.py a jen ji tady naimportovat.
limiter = Limiter(key_func=get_remote_address)