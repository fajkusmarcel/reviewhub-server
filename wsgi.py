# /var/www/ReviewHub/wsgi.py
import os
from werkzeug.middleware.proxy_fix import ProxyFix

# --- volitelně: režim aplikace (production/test) ---
os.environ.setdefault("REVIEWHUB_MODE", "production")

# DŮLEŽITÉ: SECRET_KEY musí být dodán z ENV (systemd unit),
# tady nic nenastavujeme, jen upozorníme při startu.
if not os.environ.get("REVIEWHUB_SECRET_KEY"):
    # Nechceme shodit proces, ale je dobré to mít v logu.
    print("WARN: REVIEWHUB_SECRET_KEY is not set in environment!")

# Importuj Flask app a továrnu z tvého hlavního modulu
# Uprav název podle skutečného souboru, kde máš `app = Flask(__name__)`
# Např. pokud je to app.py v kořeni projektu:
from app import app, init_app  # <-- uprav, pokud se modul jmenuje jinak
# Pokud máš Socket.IO instanci zvlášť a nevolal jsi init už v app.py,
# můžeš případně importnout a initnout i tady:
# from socketio_instance import socketio

# Inicializace aplikace (DB, config apod.)
init_app(mode=os.environ.get("REVIEWHUB_MODE", "production"))

# Nasazení pod reverzní proxy s prefixem /reviewhub
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# URL prefix a cookies pro subcestu
app.config["APPLICATION_ROOT"] = "/reviewhub"
app.config["SESSION_COOKIE_PATH"] = "/reviewhub"
# Pokud jedeš dočasně přes HTTP:
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # na HTTPS přepni na True

# Pokud Socket.IO neinicializuješ v app.py:
# socketio.init_app(app, async_mode="eventlet")

# Exportovaný objekt `app` je entry-point pro Gunicorn: wsgi:app

