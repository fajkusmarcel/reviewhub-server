from functools import wraps
from flask import current_app, session, redirect, url_for, flash

from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')  # Flask 3

        if current_app.config.get('DEBUG_MODE', False):
            return f(*args, **kwargs)

        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function




# Dekorátor pro ověření, zda je vybraný projekt
def project_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('DEBUG_MODE', False):
            # Pokud je aplikace v debug režimu, přeskočíme kontrolu přihlášení
            return f(*args, **kwargs)

        if 'selected_project' not in session:
            #flash('Musíte vybrat projekt, abyste měli přístup k této stránce.', 'warning')
            return redirect(url_for('project.project_select'))  # Přesměrování na výběr projektu

        return f(*args, **kwargs)
    return decorated_function


# Dekorátor pro ověření, zda je uživatel administrátor
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('DEBUG_MODE', False):
            # Pokud je aplikace v debug režimu, přeskočíme kontrolu přihlášení
            return f(*args, **kwargs)


        if not session.get('user_id'):
            return redirect(url_for('auth.login'))

        if session.get('user_role') != 'admin':
            flash('Nemáte administrátorská práva.', 'danger')
            return redirect(url_for('index'))  # Přesměrování na hlavní stránku
        return f(*args, **kwargs)
    return decorated_function
