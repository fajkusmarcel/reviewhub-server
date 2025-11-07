# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from functools import wraps

# Knihovny třetích stran (nainstalované přes pip)
from flask import Blueprint, render_template, make_response, request, redirect, url_for, session, current_app, flash
from flask_mysqldb import MySQL

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from utils.utils import *
from utils.decorators import *
from utils.responsive import wants_mobile, render_responsive
from db.sql_query import *

# Definice blueprintu pro uživatele
project_bp = Blueprint('project', __name__)





## *****************************************************************************
##                 PPROJECTS
## *****************************************************************************

@project_bp.route('/project', methods=['GET', 'POST'])
@login_required
@project_required
def project():
    """
    Seznam projektu
    """    
    user_role = session.get('user_role')
    user_id = session['user_id']

     # Pokud je metoda GET, načti projekty podle role
    if user_role == 'admin':
        projekty = sql_get_projects()  # Administrátor může vidět všechny projekty
    else:
        projekty = sql_get_projects_by_user(user_id)  # Autor vidí pouze své projekty
        
    return render_responsive('project.html','project_mobile.html',  projekty=projekty, user_role=user_role, site_name="Projects")


@project_bp.route('/project_select', methods=['GET', 'POST'])
@login_required
def project_select():
    """
    Vyber projektu uzivatelem
    """    
    user_id = session['user_id']
    user_role = session.get('user_role')

    if request.method == 'POST':
        project_id = request.form.get('project_id')
        if project_id is None:
            return redirect(url_for('dashboard.dashboard'))  # Přesměrování na hlavní stránku

        # Uložení ID vybraného projektu do session
        session['selected_project'] = project_id  

        # Ulozeni nazvu projektu
        project_name = sql_get_project_name(project_id)
        session['selected_project_name'] = project_name  # Uložení názvu projektu do session

        return redirect(url_for('dashboard.dashboard'))  # Přesměrování na hlavní stránku

    # Pokud je metoda GET, načti projekty podle role
    if user_role == 'admin':
        projekty = sql_get_projects()  # Administrátor může vidět všechny projekty
    else:
        projekty = sql_get_projects_by_user(user_id)  # Autor vidí pouze své projekty

    if not projekty:
        flash('Nemáte přiřazené žádné projekty.', 'warning')
    print(projekty)
    return render_responsive('project.html','project_mobile.html', projekty=projekty, site_name="Projects")


@project_bp.route('/project_add', methods=['GET', 'POST'])
@login_required
@project_required
@admin_required
def project_add():
    """
    Pridani projektu
    """    
    if request.method == 'POST':
        # Načíst data z formuláře
        form_data = extract_form_data(request)
        sql_insert_project_into_db(form_data)

        flash('Projekt byl úspěšně přidán!', 'success')
        return redirect(url_for('project.project'))

    return render_template('project_add.html', site_name="Add project")


@project_bp.route('/project_edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
@project_required
@admin_required
def project_edit(project_id):
    """
    Editace projektu
    """       
    # ID vybraneho projektu
    selected_project = session['selected_project']

    mysql = current_app.config['mysql'] 
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        # Načíst data z formuláře
        form_data = extract_form_data(request)
        selected_users = request.form.getlist('user_ids')  # Získání vybraných projektů

        # Aktualizace názvu projektu
        sql_update_project(project_id, form_data)

        # Aktualizovat prirazeni uzivatelu do projektu
        sql_delete_users_from_project(project_id)  # Vymazání starých záznamů
        for user_id in selected_users:
            sql_insert_user_into_project(project_id, user_id)

        return redirect(url_for('project.project'))

    # Načtení aktuálních informací o projektu pro editaci
    project = sql_get_project(project_id)

    # Načtení všech uživatelů
    users = sql_get_users()

    # Načtení uživatelů přiřazených k projektu
    assigned_users = sql_get_users_in_project(project_id)
    
    cursor.close()

    return render_template('project_edit.html', project=project, users=users, assigned_users=assigned_users, site_name="Edit project")

@project_bp.route('/project_delete/<int:project_id>', methods=['GET'])
@login_required
@project_required
@admin_required
def project_delete(project_id):
    """
    Smazani projektu
    """    
    if(project_id == 1):
        flash('Defaultni projekt nelze smazat', 'warning')
        return redirect(url_for('project.project'))

    # Smazání všech uživatelů přiřazených k projektu
    sql_delete_users_from_project(project_id)

    # Smazání samotného projektu
    sql_delete_project(project_id)

    return redirect(url_for('project.project'))
