# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from functools import wraps
import subprocess
from datetime import datetime
import mysql.connector

# Knihovny třetích stran (nainstalované přes pip)
from flask import Flask, Blueprint, render_template, current_app, request, redirect, url_for, jsonify, session, flash  
from flask_mysqldb import MySQL

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from utils.utils import *
from db.sql_query import *
from .gpt import *


# Definice blueprintu pro uživatele
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET'])
@login_required
@project_required
@admin_required
def settings():

    return render_template('settings.html', site_name="Settings")


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