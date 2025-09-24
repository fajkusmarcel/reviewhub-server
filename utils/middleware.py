# core/middleware.py
from time import time
from flask import current_app, session, redirect, url_for, flash, request

def register_session_guard(app):
    @app.before_request
    def session_guard():
        # výjimky: login/logout, statika apod.
        if request.endpoint in ('auth.login', 'auth.logout', 'static'):
            return
        if current_app.config.get('DEBUG_MODE', False):
            return

        # Když není přihlášený, nic neřeším – zachytí login_required
        if not session.get('user_id'):
            return

        now = time()
        last_seen  = session.get('last_seen', now)
        login_time = session.get('login_time', now)

        ina = current_app.config.get('INACTIVITY_LIMIT_SECONDS', 3600)
        abs_ = current_app.config.get('ABSOLUTE_LIMIT_SECONDS', 8*3600)

        # Inaktivita
        if now - last_seen > ina:
            session.clear()
            flash('Byl jsi automaticky odhlášen pro neaktivitu.', 'warning')
            return redirect(url_for('auth.login'))

        # Absolutní timeout
        if now - login_time > abs_:
            session.clear()
            flash('Sezení vypršelo. Přihlas se prosím znovu.', 'warning')
            return redirect(url_for('auth.login'))

        # Posuň last_seen (živé sezení)
        session['last_seen'] = now
