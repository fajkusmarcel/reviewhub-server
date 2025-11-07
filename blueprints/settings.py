# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from functools import wraps
import subprocess
from datetime import datetime
import mysql.connector


# --- DOPLNIT NA ZAČÁTEK SOUBORU ---
import re
from flask import send_file
from typing import Iterable, List
from collections import deque

# Knihovny třetích stran (nainstalované přes pip)
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from flask_mysqldb import MySQL

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from utils.utils import *
from utils.responsive import wants_mobile, render_responsive
from utils.decorators import *
from utils.responsive import wants_mobile, render_responsive
from db.sql_query import *
from .gpt import *


# Definice blueprintu pro uživatele
settings_bp = Blueprint('settings', __name__)





LOG_FILE = "/var/log/virtualserver/reviewhub.log"
ROTATED_COUNT = 5  # odpovídá backupCount=5 v RotatingFileHandler

LOG_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '(?P<user>[^']*)' "
    r"\[(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\] "
    r"\[(?P<etype>[^\]]*)\] (?P<msg>.*)$"
)



@settings_bp.route('/settings', methods=['GET'])
@login_required
@project_required
@admin_required
def settings():
    
    return render_responsive('settings.html', 'settings_mobile.html', site_name="Settings")


# KONFIGURACE AI
@settings_bp.route('/configure_ai', methods=['GET', 'POST'])
@login_required
@project_required
@admin_required
def configure_ai():
    # Základní načtení stránky s AI konfigurací
    gptModels = getGPTModels()
    return render_template('settings_configure_ai.html', ai_config_text='', site_name="Configure GPT", gptModels=gptModels)

@settings_bp.route('/load_ai_config/<string:type>', methods=['GET'])
@login_required
@project_required
@admin_required
def load_ai_config(type):
    print('LOAD CONFIG')
    # Cesta k souboru podle zvoleného typu
    if type == 'A':
        file_path = current_app.config['AI_A_file_path']
    elif type == 'B':
        file_path = current_app.config['AI_B_file_path']
    else:
        return redirect(url_for('settings.configure_ai'))

    # Načtení obsahu konfiguračního souboru
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config_text = file.read()
            print(config_text)
        return jsonify({'config_text': config_text})
    except Exception as e:
        return redirect(url_for('settings.configure_ai'))

@settings_bp.route('/save_ai_config', methods=['POST'])
@login_required
@project_required
@admin_required
def save_ai_config():
    # Získání upraveného textu a typu souboru
    config_text = request.form.get('ai_config_text')
    file_type = request.form.get('file_type')

    # Určení cesty k souboru podle typu
    if file_type == 'A':
        file_path = current_app.config['AI_A_file_path']
    elif file_type == 'B':
        file_path = current_app.config['AI_B_file_path']
    else:
        return redirect(url_for('settings.configure_ai'))

    # Uložení upravené konfigurace do souboru
    try:
        # Rozdělení textu na řádky a odstranění nadbytečných prázdných řádků
        lines = config_text.splitlines()  # Rozdělit na jednotlivé řádky
        cleaned_text = "\n".join(line.rstrip() for line in lines)  # Odstranit prázdné řádky na konci každého řádku

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_text)  # Uložit bez dodatečných prázdných řádků

        return redirect(url_for('ai_config'))
    except Exception as e:
        return redirect(url_for('settings.configure_ai'))


@settings_bp.route('/backup_db', methods=['GET'])
@login_required
@project_required
@admin_required
def backup_db():
    # Parametry pro připojení k databázi
    db_user = current_app.config['MYSQL_USER']
    db_password = current_app.config['MYSQL_PASSWORD']
    db_name = current_app.config['MYSQL_DB']
    print(db_user)
    print(db_password)
    print(db_name)

    # Vytvoření názvu souboru ve formátu reviewhub_YYYY-MM-DD.sql
    today_date = datetime.now().strftime("%Y-%m-%d")
    backup_dir = 'DB_backup'
    backup_file = f"reviewhub_{today_date}.sql"
    backup_path = os.path.join(backup_dir, backup_file)

    # Zajištění, že adresář pro zálohu existuje
    os.makedirs(backup_dir, exist_ok=True)

    # Příkaz pro zálohování databáze
    command = ["D:\\webserver\\Mysql\\bin\\mysqldump", "-u", db_user, f"-p{db_password}", db_name]

    # Otevři soubor pro zápis
    with open(backup_path, "w") as output_file:
        try:
            # Spusť příkaz a přesměruj výstup do souboru
            subprocess.run(command, stdout=output_file, stderr=subprocess.PIPE, check=True)
            print("Záloha databáze byla úspěšně vytvořena.")
        except subprocess.CalledProcessError as e:
            print(f"Došlo k chybě při záloze databáze: {e}")
            
    return redirect(url_for('settings.settings'))



@settings_bp.route('/update_publications_from_scopus', methods=['GET'])
@login_required
@project_required
@admin_required
def update_publications_from_scopus():
    # Získáme seznam všech článků
    publications = sql_get_all_publications_without_filters()

    updated_publications = []
    error_publications = []

    # Projdeme každý článek a zaktualizujeme jeho data ze Scopusu
    for publication in publications:

        publication_name = publication['publication_name']
        publication_id = publication['publication_id']

        scopus_data = get_article_info_from_SCOPUS(publication_name,  publication_id)
        
        if 'error' not in scopus_data:
            # Pokud nejsou chyby, zaktualizujeme článek
            sql_update_publications_scopus_data(
                publication['publication_id'],
                scopus_data['title'],
                scopus_data['authors'],
                scopus_data['journal_or_conference'],
                scopus_data['year'],
                scopus_data['doi'],
                scopus_data['bibtex_citation']
            )
            updated_publications.append({
                'id': publication['publication_id'],
                'title': scopus_data['title'],
                'authors': scopus_data['authors'],
                'journal': scopus_data['journal_or_conference'],
                'year': scopus_data['year'],
                'status': 'success'
            })
        else:
            error_publications.append({
                'id': publication['publication_id'],
                'title': publication['publication_name'],
                'error_message': scopus_data['error'],
                'status': 'error'
            })

    # Spojení seznamů pro zobrazení
    result_publications = updated_publications + error_publications
    
    # Zobrazíme stránku s výsledky
    return render_template('publication_scopus_update_results.html', publications=result_publications)



# --- DOPLNIT ROUTY ---

@settings_bp.route('/logs', methods=['GET'])
@login_required
@project_required
@admin_required
def logs():
    # Parametry z URL (GET) – pohodlnější pro sdílení odkazu
    lines = max(int(request.args.get('lines', 200)), 1)
    level = request.args.get('level', 'ALL').upper()        # ALL|INFO|WARNING|ERROR|DEBUG|CRITICAL
    event_type = request.args.get('event_type', '').strip() # substring match (case-insensitive)
    query = request.args.get('q', '').strip()               # fulltext v message i user
    include_archived = request.args.get('archived', '0') == '1'
    order = request.args.get('order', 'newest')             # newest|oldest
    autoreload = request.args.get('autoreload', '0')        # v sekundách (string), '0' = off

    raw_lines = _collect_log_lines(include_archived, lines * 4)  # trošku nadvýběr, ať mají filtry z čeho ořezat

    filtered: List[dict] = []
    q_low = query.lower()
    et_low = event_type.lower()

    for line in reversed(raw_lines):  # začneme od nejnovějších
        m = LOG_LINE_RE.match(line)
        if not m:
            # neparsovatelný řádek taky zobrazíme (může jít o traceback)
            rec = {"raw": line, "ts": "", "user": "", "level": "", "etype": "", "msg": line}
        else:
            rec = {
                "raw": line,
                "ts": m.group("ts"),
                "user": m.group("user"),
                "level": m.group("level"),
                "etype": m.group("etype"),
                "msg": m.group("msg"),
            }

        # Filtr LEVEL
        if level != 'ALL' and rec.get("level") != level:
            continue
        # Filtr event_type (substring, case-insensitive)
        if et_low and et_low not in rec.get("etype", "").lower():
            continue
        # Fulltext (user + msg + etype)
        if q_low and (q_low not in rec.get("msg", "").lower()
                      and q_low not in rec.get("user", "").lower()
                      and q_low not in rec.get("etype", "").lower()):
            continue

        filtered.append(rec)
        if len(filtered) >= lines:
            break

    # Řazení
    if order == 'oldest':
        filtered = list(reversed(filtered))

    return render_responsive(
        'settings_logs.html', 'settings_logs_mobile.html',
        site_name="Logs",
        logs=filtered,
        form={
            "lines": lines,
            "level": level,
            "event_type": event_type,
            "q": query,
            "archived": '1' if include_archived else '0',
            "order": order,
            "autoreload": autoreload,
        }
    )

@settings_bp.route('/logs-download', methods=['GET'])
@login_required
@project_required
@admin_required
def logs_download():
    # jen aktuální log; případně můžeš rozšířit ?i=1..5 pro archiv
    return send_file(LOG_FILE, as_attachment=True, download_name='reviewhub.log')


def _safe_tail(path: str, max_lines: int):
    """
    Efektivní tail z konce souboru s ošetřením seek před začátek.
    """
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            pos = f.tell()
            buf = b""
            lines = []

            # Čti po blocích z konce, ale nikdy nejdi před 0
            block_size = 4096
            while len(lines) <= max_lines and pos > 0:
                read_size = block_size if pos >= block_size else pos
                pos -= read_size
                f.seek(pos, os.SEEK_SET)
                chunk = f.read(read_size)
                buf = chunk + buf
                lines = buf.splitlines()

            # Vezmi posledních N
            tail_bytes = lines[-max_lines:]
            return [b.decode("utf-8", errors="replace") for b in tail_bytes]
    except FileNotFoundError:
        return []
    except PermissionError:
        return [f"!!! PermissionError: {path} (zkontroluj práva čtení pro uživatele, pod kterým běží app)"]
    except Exception as e:
        return [f"!!! ReadError {path}: {e}"]


def _safe_tail2(path: str, max_lines: int):
    """
    Robustní tail: přečte soubor po řádcích a nechá si jen posledních N.
    U logu do 5 MB je to v pohodě a bez seek chyb.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            dq = deque(f, maxlen=max_lines)
        return [line.rstrip("\n") for line in dq]
    except FileNotFoundError:
        return []
    except PermissionError:
        return [f"!!! PermissionError: {path} (zkontroluj práva čtení pro uživatele, pod kterým běží app)"]
    except Exception as e:
        return [f"!!! ReadError {path}: {e}"]


def _collect_log_lines(include_archived: bool, need_lines: int) -> List[str]:
    """
    Posbírá poslední řádky z current + (volitelně) rotated logů; pořadí od nejnovějších.
    """
    files = [LOG_FILE]
    if include_archived:
        # Rotované logy jsou číslované od .1 (nejnovější) po .5 (nejstarší)
        for i in range(1, ROTATED_COUNT + 1):
            files.append(f"{LOG_FILE}.{i}")

    # Načteme z current nejvíc, pak případně doplníme z .1, .2, ...
    collected: List[str] = []
    for p in files:
        need = max(need_lines - len(collected), 0)
        if need <= 0:
            break
        chunk = _safe_tail(p, need)
        # u current tail přinese nejnovější řádky; u .1 také koncové (nejnovější v tom souboru)
        # chceme výsledně NEWEST first → zatím budeme skládat: nejdřív current, pak .1, ...
        # ale protože chunk je chronologicky od staršího k novějšímu, necháme tak.
        collected = chunk + collected  # posouváme starší dolů
    # nyní collected je vzestupně (od starších k novějším); rozumné pro následné omezení a řazení
    return collected[-need_lines:]


