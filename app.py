# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import bcrypt
from functools import wraps
import config

# Knihovny třetích stran (nainstalované přes pip)
from flask import Flask, render_template, request, redirect, url_for, jsonify, g, session, flash  # Flask moduly
from flask_mysqldb import MySQL  # Flask-MySQL pro práci s databází
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utils.logger import setup_logging, log_info, log_warning, log_error

from flask_socketio import SocketIO, send, emit
from socketio_instance import socketio
socketio = SocketIO(async_mode='eventlet')  # nebo 'gevent'

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from db.sql_query import *
from utils.utils import *

from blueprints.dashboard import dashboard_bp
from blueprints.project import project_bp
from blueprints.user import user_bp
from blueprints.publication import publication_bp
from blueprints.settings import settings_bp
from blueprints.gpt import gpt_bp

app = Flask(__name__)
app.secret_key = os.environ.get("REVIEWHUB_SECRET_KEY")
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
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

# Inicializace limiteru - omeyuje pocet prihlaseni/login za minutu
limiter = Limiter(key_func=get_remote_address)

# Použití limiteru na aplikaci
#limiter.init_app(app)

# Registrace blueprintů
app.register_blueprint(dashboard_bp)
app.register_blueprint(project_bp)
app.register_blueprint(user_bp)
app.register_blueprint(publication_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(gpt_bp)



limiter.init_app(app)
socketio.init_app(app)

# SOuvisi s logovanim
@app.before_request
def _inject_user_into_logs():
    full_name = " ".join(x for x in [session.get("user_name"), session.get("user_surname")] if x)
    g.user_login = session.get("user_login") or full_name or session.get("user_id") or "-"




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

    return render_template('index.html', projekty=projekty, user_count=user_count, site_name="Home")


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT user_id, name, surname, login, password, role FROM user WHERE login = %s ', (username, ))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            log_info("auth", f"user '{username}' neni registrovany uzivatel {request.remote_addr}")
            flash('Nesprávné uživatelské jméno nebo heslo.')
            return redirect(url_for('login'))


        passwordInDB_HASH = user['password']

        try:
            ok = bcrypt.checkpw(password.encode('utf-8'), passwordInDB_HASH.encode('utf-8'))
        except Exception as e:
            ok = False

        if ok:
            # Login - spravne zadane heslo
            log_info("auth", f"user '{username}' logged in from {request.remote_addr}")
            session['user_id'] = user['user_id']
            session['user_login'] = username
            session['user_name'] = user['name']
            session['user_surname'] = user['surname']
            session['user_role'] = user['role']
            session['ModeApp'] = app.config.get('ModeApp')
            resp = redirect(url_for('dashboard.dashboard'))
            return resp
        else:
            # Login - chybne zadane heslo
            log_warning("auth", f"user '{username}' zadal nespravne heslo {request.remote_addr} ")
            flash('Nesprávné uživatelské jméno nebo heslo.')
            return redirect(url_for('login'))


    return render_template('login.html', site_name="Login")  # Vytvoříme šablonu login.html


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_role', None)
    session.pop('selected_project', None)
    return redirect(url_for('dashboard.dashboard'))  # Nebo jinou cílovou stránku

@app.route('/select_mode/<string:mode>', methods=['GET', 'POST'])
@login_required
@project_required
def select_mode(mode):
    print('Pozadavek na zmenu mode ', mode)
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
        print('Nastavuji mode ', mode)
        app.config['UPLOAD_FOLDER'] = config.pdf_path_test
        app.config['MYSQL_HOST'] = config.MYSQL_HOST
        app.config['MYSQL_USER'] = config.MYSQL_USER
        app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
        app.config['MYSQL_DB'] = config.MYSQL_DB_test
        app.config['ModeApp'] = 'test'
    elif(mode == 'production'):
        print('Nastavuji mode ', mode)
        app.config['UPLOAD_FOLDER'] = config.pdf_path
        app.config['MYSQL_HOST'] = config.MYSQL_HOST
        app.config['MYSQL_USER'] = config.MYSQL_USER
        app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
        app.config['MYSQL_DB'] = config.MYSQL_DB
        app.config['ModeApp'] = 'production'
    else:
        print("Musi vybrat mode: test nebo production")

    app.config["MAX_CONTENT_LENGTH"] = getattr(config, "MAX_CONTENT_LENGTH", 50 * 1024 * 1024)
    app.config["ALLOWED_EXTENSIONS"] = getattr(config, "ALLOWED_EXTENSIONS", {"pdf"})

    app.config['AI_A_file_path'] = config.AI_A_file_path
    app.config['AI_B_file_path'] = config.AI_B_file_path


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