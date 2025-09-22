#!/usr/bin/env python3
# WSGI entrypoint pro Apache mod_wsgi

import os
import sys

# Ujisti se, že adresář s app.py je na import path
BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Výchozí režim (můžeš přepsat v Apache přes env)
os.environ.setdefault("REVIEWHUB_MODE", "production")

# Import aplikace a inicializační funkce
from app import app, init_app  # noqa: E402

# Inicializace konfigurace a DB podle režimu
init_app(os.environ.get("REVIEWHUB_MODE", "production"))

# mod_wsgi očekává proměnnou `application`
application = app

# Friendly varování do logu, když chybí secret key
if not os.environ.get("REVIEWHUB_SECRET_KEY"):
    print("WARN: REVIEWHUB_SECRET_KEY is not set; Flask sessions may be insecure.")
