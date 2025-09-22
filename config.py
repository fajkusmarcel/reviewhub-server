from pathlib import Path

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


# Debugovani - odstrani kontrolu prihlaseneho uzivatele apod.
DEBUG_MODE = True

# AI configuration
AI_A_file_path = './config/AI_reviewA.txt'
AI_B_file_path = './config/AI_reviewB.txt'

#test