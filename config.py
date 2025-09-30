from pathlib import Path
from datetime import timedelta

# ===== Obecné / režimy ============================================================================

APP_NAME = "ReviewHub"                                # název aplikace (volitelné)
DEBUG_MODE = False                                    # rezim ladeni


# ===== Databáze (MySQL) ===========================================================================
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'fajkus'
MYSQL_DB = 'reviewhub'
MYSQL_DB_test = 'reviewhub_test'

# ===== Cesty / uploady / vlastní soubory ===========================================================
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uplouds"          # adresar pro uploud souboru

pdf_path = str(UPLOAD_DIR)                            # adresar pro nahravani clanku v pdf
pdf_path_test = str(UPLOAD_DIR / "test")              # testovaci adresar pro nahravani souboru
tmp_path = str(UPLOAD_DIR / "tmp")                    # adresar pro docasne soubory (pdf2text, export.json, ...)

AI_A_file_path = './config/AI_reviewA.txt'            # soubor s konfiguraci AI
AI_B_file_path = './config/AI_reviewB.txt'            # soubor s konfiguraci AI


MAX_CONTENT_LENGTH = 20 * 1024 * 1024                 # maximální velikost uploadu (50 MB)
ALLOWED_EXTENSIONS = {"pdf"}                          # povolené přípony uploadů

# ===== Bezpečnost a session =======================================================================
SESSION_COOKIE_NAME = "session"                       # Session cookie název
SESSION_REFRESH_EACH_REQUEST = True                   # Obnova expirace při každém requestu – posouvá timeout při aktivitě
PERMANENT_SESSION_LIFETIME = timedelta(minutes=10)    # Session životnost

# Vlastní hlídače
INACTIVITY_LIMIT_SECONDS = 60 * 60                    # server-side neaktivita: odhlásit po 60 min bez akce
ABSOLUTE_LIMIT_SECONDS   = 20 * 60 * 60               # server-side absolutní limit: max 8 h od přihlášení



