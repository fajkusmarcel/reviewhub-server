# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.routing import BuildError
import bcrypt
from functools import wraps
from time import time

# Knihovny třetích stran (nainstalované přes pip)
from flask import Flask, render_template, make_response, request, redirect, url_for, jsonify, g, session, flash  # Flask moduly
from flask_mysqldb import MySQL  # Flask-MySQL pro práci s databází
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utils.logger import setup_logging, log_info, log_warning, log_error
from utils.middleware import register_session_guard  # po přejmenování
import config
from utils.extensions import limiter

from flask_socketio import SocketIO, send, emit
from socketio_instance import socketio
socketio = SocketIO(async_mode='eventlet')  # nebo 'gevent'

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from db.sql_query import *
from utils.utils import *
from utils.extensions import limiter
from utils.middleware import register_session_guard
from utils.decorators import *
from blueprints.dashboard import dashboard_bp
from blueprints.project import project_bp
from blueprints.user import user_bp
from blueprints.publication import publication_bp
from blueprints.settings import settings_bp
from blueprints.gpt import gpt_bp
from blueprints.auth import auth_bp

app = Flask(__name__)
app.secret_key = os.environ.get("REVIEWHUB_SECRET_KEY")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Načte všechny hodnoty z vašeho config.py do app.config (vč. INACTIVITY_LIMIT_SECONDS, ABSOLUTE_LIMIT_SECONDS...).
# Dávejte ideálně hned za `app = Flask(__name__)`, aby další inicializační kroky už viděly správné hodnoty.
app.config.from_object(config)

app.config.update(
    SECRET_KEY=os.getenv("GREENSTATS_SECRET_KEY", "dev-change-me/reviewhub"),
    SESSION_COOKIE_NAME="reviewhub_session",
    SESSION_COOKIE_PATH="/reviewhub",
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    REMEMBER_COOKIE_NAME="reviewhub_remember",
    REMEMBER_COOKIE_PATH="/reviewhub",
    REMEMBER_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_SECURE=False,
    APPLICATION_ROOT="/reviewhub",
)

# Databaze MySQL
mysql = None


# Propojí limiter s konkrétní Flask aplikací (zaregistruje middleware, čte config).
# Po tomhle volání začnou fungovat @limiter.limit(...) dekorátory i globální limity.
limiter.init_app(app)

# Registrace blueprintů
app.register_blueprint(dashboard_bp)
app.register_blueprint(project_bp)
app.register_blueprint(user_bp)
app.register_blueprint(publication_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(gpt_bp)
app.register_blueprint(auth_bp)

# Zaregistruje "before_request" guard, který hlídá neaktivitu a absolutní timeout sezení.
# Musí se volat až PO načtení configu (aby měl k dispozici INACTIVITY_LIMIT_SECONDS atd.).
register_session_guard(app)

socketio.init_app(app)

# SOuvisi s logovanim
@app.before_request
def _inject_user_into_logs():
    full_name = " ".join(x for x in [session.get("user_name"), session.get("user_surname")] if x)
    g.user_login = session.get("user_login") or full_name or session.get("user_id") or "-"


@app.context_processor
def inject_timeouts():
    return dict(
        INACTIVITY_SEC=app.config.get('INACTIVITY_LIMIT_SECONDS', 3600),
        ABSOLUTE_SEC=app.config.get('ABSOLUTE_LIMIT_SECONDS', 8*3600),
    )


# Existující cesta (route) pro hlavní stránku
@app.route('/')
@login_required
@project_required
def index():

    # Připojení k databázi a načtení projektů
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT project_id, project_name FROM project")
    projekty = cursor.fetchall()
    cursor.close()

    # Získání počtu uživatelů (pro kontrolu)
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM user")
    result = cursor.fetchone()
    user_count = result[0]
    cursor.close()

    #return render_template('index.html', projekty=projekty, user_count=user_count, site_name="Home")
    return render_responsive('index.html', 'index_mobile.html', projekty=projekty, user_count=user_count, site_name="Home")


@app.route('/select_mode/<string:mode>', methods=['GET', 'POST'])
@login_required
@project_required
def select_mode(mode):
    # Nastavení hodnoty do session v rámci požadavku
    if mode == 'test':
        session['ModeApp'] = 'test'
    elif mode == 'production':
        session['ModeApp'] = 'production'

    save_config(mode)
    return redirect(url_for('project.project_select'))

@socketio.on('getConfigGPTB')
def handle_getConfigGPTB():  
    configGPTB = load_ai_b_config()
    emit("configGPTB", configGPTB)


def save_config(mode):
    if(mode == 'test'):
        app.config['UPLOAD_FOLDER'] = config.pdf_path_test
        app.config['MYSQL_HOST'] = config.MYSQL_HOST
        app.config['MYSQL_USER'] = config.MYSQL_USER
        app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
        app.config['MYSQL_DB'] = config.MYSQL_DB_test
        app.config['ModeApp'] = 'test'
    elif(mode == 'production'):
        app.config['UPLOAD_FOLDER'] = config.pdf_path
        app.config['MYSQL_HOST'] = config.MYSQL_HOST
        app.config['MYSQL_USER'] = config.MYSQL_USER
        app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
        app.config['MYSQL_DB'] = config.MYSQL_DB
        app.config['ModeApp'] = 'production'

    app.config["MAX_CONTENT_LENGTH"] = getattr(config, "MAX_CONTENT_LENGTH", 50 * 1024 * 1024)
    app.config["ALLOWED_EXTENSIONS"] = getattr(config, "ALLOWED_EXTENSIONS", {"pdf"})

    app.config['AI_A_file_path'] = config.AI_A_file_path
    app.config['AI_B_file_path'] = config.AI_B_file_path

#Pomocná funkce pro výběr mobil/desktop šablony
MOBILE_KEYWORDS = ("mobile", "iphone", "ipad", "android", "opera mini", "mobi", "silk")

def wants_mobile() -> bool:
    # Volitelný ruční override přes query (?mobile=1/0) – hodí se na testy
    q = request.args.get("mobile")
    if q == "1":
        return True
    if q == "0":
        return False

    ua = (request.user_agent.string or "").lower()
    return any(k in ua for k in MOBILE_KEYWORDS)

def render_responsive(desktop_template: str, mobile_template: str, **ctx):
    if wants_mobile():
        return render_template(mobile_template, **ctx)
    return render_template(desktop_template, **ctx)

@app.context_processor
def utility_processor():
    def href(*endpoints, **values):
        """
        Zkusí postupně více endpointů; když žádný neexistuje, vrátí '#'
        místo 500 chyby.
        """
        for ep in endpoints:
            try:
                return url_for(ep, **values)
            except BuildError:
                continue
        return '#'
    return dict(href=href)

def init_app(mode='production'):
    global mysql
    save_config(mode)           # nastaví app.config z config.py

    limiter.init_app(app)
    socketio.init_app(app)

    mysql = MySQL(app)          # nebo jiný klient podle tvého kódu
    app.config['mysql'] = mysql # pokud na to ve zbytku kódu spoléháš

    setup_logging(log_dir="/var/log/virtualserver")

    return app



if __name__ == '__main__':

    init_app(mode='production')           # nebo 'test'
    app.run(host='0.0.0.0', port=5002, debug=True)


