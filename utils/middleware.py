# core/middleware.py
from time import time
from flask import current_app, session, redirect, url_for, flash, request

def register_session_guard(app):
    """
    Zaregistruje before_request handler, který:
      - hlídá neaktivitu (INACTIVITY_LIMIT_SECONDS) a absolutní délku sezení (ABSOLUTE_LIMIT_SECONDS),
      - po vypršení sezení vyčistí session, zobrazí flash zprávu a přesměruje na login,
      - při každém "normálním" požadavku aktualizuje session['last_seen'].

    Předpoklady:
      - Při úspěšném loginu nastavujete:
          session['user_id']   – identifikátor přihlášeného uživatele
          session['login_time']– timestamp vzniku sezení
          session['last_seen'] – timestamp poslední aktivity
      - V app.config jsou definovány:
          INACTIVITY_LIMIT_SECONDS (např. 3600)
          ABSOLUTE_LIMIT_SECONDS   (např. 8*3600)
          DEBUG_MODE                (True/False) – v debug režimu guard přeskočí
      - Endpoints 'auth.login', 'auth.logout' a 'static' se ignorují (nechceme smyčky redirectů).

    Poznámky:
      - Guard se vyhodnotí PŘED každým requestem.
      - "Automatické" odhlášení se projeví při dalším požadavku (klik, reload, AJAX).
      - Socket.IO heartbeat ("/socket.io") neaktualizuje last_seen, aby trvalé websockety
        neudržovaly sezení donekonečna. Přesto při požadavku přes tento endpoint proběhne kontrola,
        takže při překročení limitu dojde k odhlášení.
    """

    @app.before_request
    def session_guard():
        # 1) Vynecháme login/logout a statiku (nechceme zacyklení a zbytečné flash zprávy)
        if request.endpoint in ('auth.login', 'auth.logout', 'static'):
            return
        # 2) V debug režimu guard neaplikujeme (rychlejší vývoj, menší překážky)
        if current_app.config.get('DEBUG_MODE', False):
            return

        # 3) Když není přihlášený uživatel, neděláme nic – login_required to dořeší
        if not session.get('user_id'):
            return

        now = time()
        last_seen  = session.get('last_seen', now)
        login_time = session.get('login_time', now)

        # 4) Načti limity z configu, s rozumnými defaulty pro případ, že chybí
        ina = current_app.config.get('INACTIVITY_LIMIT_SECONDS', 5600)
        abs_ = current_app.config.get('ABSOLUTE_LIMIT_SECONDS', 8*3600)

        # 5) Kontrola neaktivity – uživatel nic neudělal déle než limit?
        if now - last_seen > ina:
            session.clear()
            flash('Byl jsi automaticky odhlášen pro neaktivitu.', 'warning')
            return redirect(url_for('auth.login'))

        # 6) Kontrola absolutního limitu – sezení je starší než X hodin?
        if now - login_time > abs_:
            session.clear()
            flash('Sezení vypršelo. Přihlas se prosím znovu.', 'warning')
            return redirect(url_for('auth.login'))

        # 7) Aktualizace last_seen jen pro "běžné" HTTP požadavky,
        #    ne pro Socket.IO heartbeaty, které by jinak držely sezení věčně aktivní.
        session['last_seen'] = now
