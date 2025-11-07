from flask import render_template, request, redirect, url_for, session, current_app, flash
from time import time
import bcrypt

from flask import Blueprint, render_template, make_response, request, redirect, url_for, session, current_app, flash

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from db.sql_query import *
from utils.utils import *
from utils.logger import *
from utils.extensions import limiter
from utils.decorators import *
from utils.responsive import wants_mobile, render_responsive

auth_bp = Blueprint('auth', __name__)




@auth_bp.route('/login', methods=['GET', 'POST'])
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
        conn.close()

        if not user:
            log_info("auth", f"user '{username}' neni registrovany uzivatel {request.remote_addr}")
            flash('Nesprávné uživatelské jméno nebo heslo.')
            return redirect(url_for('auth.login'))


        passwordInDB_HASH = user['password']

        try:
            ok = bcrypt.checkpw(password.encode('utf-8'), passwordInDB_HASH.encode('utf-8'))
        except Exception as e:
            ok = False

        if ok:
            # Login - spravne zadane heslo
            session.clear()
            log_info("auth", f"user '{username}' logged in from {request.remote_addr}")
            session['user_id'] = user['user_id']
            session['user_login'] = username
            session['user_name'] = user['name']
            session['user_surname'] = user['surname']
            session['user_role'] = user['role']
            session['ModeApp'] = current_app.config.get('ModeApp')
            session.permanent = True
            resp = redirect(url_for('dashboard.dashboard'))
            #Ulož si čas vytvoření a poslední aktivitu (pro vlastní logiku)
            session['login_time'] = time()
            session['last_seen'] = time()
            return resp
        else:
            # Login - chybne zadane heslo
            log_warning("auth", f"user '{username}' zadal nespravne heslo {request.remote_addr} ")
            flash('Nesprávné uživatelské jméno nebo heslo.')
            return redirect(url_for('auth.login'))


    return render_responsive('login.html', 'login_mobile.html', site_name="Login")  # Vytvoříme šablonu login.html


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('dashboard.dashboard'))  # Nebo jinou cílovou stránku
