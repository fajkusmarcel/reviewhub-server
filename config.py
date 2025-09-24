from pathlib import Path
from datetime import timedelta

# Konfigurace MySQL připojení
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'fajkus'
MYSQL_DB = 'reviewhub'
MYSQL_DB_test = 'reviewhub_test'

# PATH
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uplouds"  # zatím necháme na původním místě


pdf_path = str(UPLOAD_DIR)
pdf_path_test = str(UPLOAD_DIR / "test")
tmp_path = str(UPLOAD_DIR / "tmp")

MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {"pdf"}

# Konfigurace prihlasovani
SESSION_COOKIE_NAME = "session"                      # Session cookie název
SESSION_REFRESH_EACH_REQUEST = True                  # Obnova expirace při každém requestu – posouvá timeout při aktivitě
PERMANENT_SESSION_LIFETIME = timedelta(minutes=10)    # Session životnost

# Vlastní hlídače
INACTIVITY_LIMIT_SECONDS = 10 * 60        # 10 min bez požadavku => odhlásit
ABSOLUTE_LIMIT_SECONDS   = 20 * 60 * 60   # max délka sezení (i když je aktivní)


# Debugovani - odstrani kontrolu prihlaseneho uzivatele apod.
DEBUG_MODE = False

# AI configuration
AI_A_file_path = './config/AI_reviewA.txt'
AI_B_file_path = './config/AI_reviewB.txt'

#test