# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
import bcrypt
from functools import wraps

# Knihovny třetích stran (nainstalované přes pip)
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from flask_mysqldb import MySQL

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from utils.utils import *
from utils.decorators import *
from db.sql_query import *


# Definice blueprintu pro uživatele
user_bp = Blueprint('user', __name__)


@user_bp.route('/users')
@login_required
@project_required
def users():
    """
    Seznam uzivatelu
    """        
    users = sql_get_users()    
    return render_template('user.html', users=users, site_name="Users")


@user_bp.route('/user_edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@project_required
@admin_required
def user_edit(user_id):
    """
    Editace uzivatele s ID=user_id
    """  
    print(user_id)
    if request.method == 'POST':
        # Načíst data z formuláře
        form_data = extract_form_data(request)
        print(form_data)
        # Aktualizace uživatele v databázi
        rows_updated = sql_update_user(user_id, form_data)
        msg = {}
        if rows_updated > 0:
            msg = {"LEVEL": "INFO", "TEXT": "Uživatel byl úspěšně aktualizován."}
        else:
            msg = {"LEVEL": "WARNING", "TEXT": "Nebyl aktualizován žádný záznam."}
        users = sql_get_users()
        return render_template('user.html', users=users, msg=msg)

    # Načtení uživatele pro editaci
    user = sql_get_user_by_id(user_id)    

    return render_template('user_edit.html', user=user, site_name="Edit user")
        
@user_bp.route('/user_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
@project_required
@admin_required
def user_password(user_id):
    """
    Změna hesla uživatele s ID=user_id
    """    
    if request.method == 'POST':
        # Načíst data z formuláře
        form_data = extract_form_data(request)
        # Získání hashovaného hesla z DB
        password_in_db = sql_get_user_password(user_id)
        msg = {}
        # Ověření starého hesla
        if bcrypt.checkpw(form_data['passwordOld'].encode('utf-8'), password_in_db.encode('utf-8')):
            # Hashování nového hesla
            password_new_hash = hash_password(form_data['passwordNew'])
            # Aktualizace hesla v databázi
            rows_updated = sql_update_user_password(user_id, password_new_hash)
            if rows_updated > 0:
                msg = {"LEVEL": "INFO", "TEXT": "Heslo bylo úspěšně změněno."}
            else:
                msg = {"LEVEL": "WARNING", "TEXT": "Změna hesla neproběhla, nebyl aktualizován žádný záznam."}
        else:
            msg = {"LEVEL": "WARNING", "TEXT": "Špatně zadané staré heslo, heslo nebylo změněno."}

        users = sql_get_users()
        return render_template('user.html', users=users, msg=msg, site_name="User paassword")

    # Načtení uživatele
    user = sql_get_user_by_id(user_id)  # Předpokládám, že máš funkci na získání uživatele
    return render_template('user_password.html', user=user)
    

@user_bp.route('/user_add', methods=['GET', 'POST'])
@login_required
@project_required
@admin_required
def user_add():
    """
    Pridani uzivatele do databaze.
    """    
    if request.method == 'POST':
        # nacist data z formulare
        form_data = extract_form_data(request)
        # Hashování hesla
        heslo_HASH = hash_password(form_data['heslo'])        
        # Vložení uživatele do databáze
        sql_insert_user_into_db(form_data, heslo_HASH)
        return redirect(url_for('user.users'))

    return render_template('user_add.html', site_name="Add user")

@user_bp.route('/user_delete/<int:user_id>', methods=['GET'])
@login_required
@project_required
@admin_required
def user_delete(user_id):
    mysql = current_app.config['mysql'] 
    cursor = mysql.connection.cursor()    
    # Kdyz se maze uzivatel, ktery mel zpracovane clanky, clanky se priradi  administratorovi
    user_id_default = 1
    cursor.execute('UPDATE publicationtracking SET user_id_added = %s WHERE user_id_added = %s', (user_id_default, user_id, ))
    cursor.execute('UPDATE publicationtracking SET user_id_last_modified = %s, last_modified_at = NULL WHERE user_id_last_modified = %s', (user_id_default, user_id,))
    cursor.execute('UPDATE publicationtracking SET user_id_completed = %s, completed_at = NULL WHERE user_id_completed = %s', (user_id_default, user_id,))
    # Smazani prirazeni do projektu
    cursor.execute('DELETE FROM userproject WHERE user_id = %s', (user_id,))
    # Smazani uzivatele
    cursor.execute('DELETE FROM user WHERE user_id = %s', (user_id,))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('user.users'))