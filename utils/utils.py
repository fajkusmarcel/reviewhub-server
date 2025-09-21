import os
import requests
from functools import wraps

from flask import request, session, redirect, url_for, flash, current_app



import bcrypt

from db.sql_query import *


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("=== login_required check ===")
        print("Request path:", request.path)
        print("Session keys:", list(session.keys()))
        print("Session content:", dict(session))
        cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')  # Flask 3
        print("Cookie name:", cookie_name)
        print("Cookie in request:", request.cookies.get(cookie_name))

        if current_app.config.get('DEBUG_MODE', False):
            return f(*args, **kwargs)

        if 'user_id' not in session:
            print(">> user_id NOT in session -> redirect /login")
            return redirect(url_for('login'))
        print(">> user_id OK, pokračuju")
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
                
        if session.get('user_role') != 'admin':
            flash('Nemáte administrátorská práva.', 'danger')
            return redirect(url_for('index'))  # Přesměrování na hlavní stránku
        return f(*args, **kwargs)
    return decorated_function


def load_ai_a_config():
    """
    Načte textový soubor definovaný v config.py a uloží obsah do proměnné.
    """
    AI_A_file_path = current_app.config['AI_A_file_path']

    if not os.path.exists(AI_A_file_path):
        raise FileNotFoundError(f"Soubor {AI_A_file_path} neexistuje.")

    with open(AI_A_file_path, 'r', encoding='utf-8') as file:
        ai_a_config = file.read()

    return ai_a_config

def load_ai_b_config():
    """
    Načte textový soubor definovaný v config.py a uloží obsah do proměnné.
    """
    AI_B_file_path = current_app.config['AI_B_file_path']

    if not os.path.exists(AI_B_file_path):
        raise FileNotFoundError(f"Soubor {AI_B_file_path} neexistuje.")

    with open(AI_B_file_path, 'r', encoding='utf-8') as file:
        ai_b_config = file.read()

    return ai_b_config

def extract_form_data(request):
    """
    Obecná funkce pro extrahování všech dat z formuláře jako slovník.
    """
    form_data = {key: value.strip() for key, value in request.form.items()}
    return form_data


def hash_password(password):
    """
    Funkce pro hashování hesla.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# DEPRECATED
def check_user_and_project():
    """
    Funkce zkontroluje, zda je uživatel přihlášený a zda je vybraný projekt.
    Vrátí redirect v případě, že nejsou splněny podmínky.
    """

    # Kontrola přihlášení
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Kontrola, zda je projekt vybrán
    if 'selected_project' not in session:
        return redirect(url_for('project.project_select'))

    # Vše je v pořádku, vrací None
    return None

# DEPRECATED
def check_user_logged():
    """
    Funkce zkontroluje, zda je uživatel přihlášený a zda je vybraný projekt.
    Vrátí redirect v případě, že nejsou splněny podmínky.
    """
    # Kontrola přihlášení
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Vše je v pořádku, vrací None
    return None

# DEPRECATED
def check_user_role_admin():
    if session['user_role'] == 'admin':
        return None
    else:
        return redirect(url_for('index'))

def log_debug(msg):
    if log == 1:
        print(msg)



def get_article_info_from_SCOPUS(article_title, article_id):
    # URL pro CrossRef API s dotazem na název článku
    url = f"https://api.crossref.org/works?query.title={article_title}"
    
    # Odeslání GET požadavku
    response = requests.get(url)
    
    # Kontrola úspěšnosti dotazu
    if response.status_code == 200:
        data = response.json()
        
        if data['message']['items']:
            # Projdeme všechny vrácené položky a hledáme přesnou shodu názvu článku
            for article_data in data['message']['items']:
                title = article_data.get('title', ['N/A'])[0].strip()

                if title.lower() == article_title.lower():
                    # Extrakce autorů - kontrola existence křestního jména a příjmení
                    authors_list = []
                    for author in article_data.get('author', []):
                        family_name = author.get('family', 'Unknown')  # Příjmení
                        given_name = author.get('given', '')  # Křestní jméno (pokud existuje)
                        
                        if given_name:
                            authors_list.append(f"{family_name}, {given_name}")
                        else:
                            authors_list.append(f"{family_name}")  # Pokud křestní jméno chybí, použije se pouze příjmení
                    
                    authors = ' and '.join(authors_list)
                    
                    # Získání dalších údajů
                    journal_or_conference = article_data.get('container-title', ['N/A'])[0]
                    year = article_data.get('published-print', {}).get('date-parts', [[None]])[0][0]
                    if not year:
                        year = article_data.get('published-online', {}).get('date-parts', [[None]])[0][0]
                    if not year:
                        year = article_data.get('issued', {}).get('date-parts', [[None]])[0][0]
                    year = year if year else '0'
                    
                    doi = article_data.get('DOI', 'N/A')
                    url = article_data.get('URL', 'N/A')
                    volume = article_data.get('volume', 'N/A')
                    issue = article_data.get('issue', 'N/A')
                    type_publication = article_data.get('type', 'journal-article')

                     # Generování citace podle typu publikace
                    if type_publication == 'journal-article':
                        bibtex_citation = f"@ARTICLE{{{article_id},\n"
                        bibtex_citation += f"\tauthor = {{{authors}}},\n"
                        bibtex_citation += f"\ttitle = {{{title}}},\n"
                        bibtex_citation += f"\tyear = {{{year}}},\n"
                        bibtex_citation += f"\tjournal = {{{journal_or_conference}}},\n"
                        if volume != 'N/A':
                            bibtex_citation += f"\tvolume = {{{volume}}},\n"
                        if issue != 'N/A':
                            bibtex_citation += f"\tissue = {{{issue}}},\n"
                        bibtex_citation += f"\tdoi = {{{doi}}},\n"
                        bibtex_citation += f"\turl = {{{url}}}\n"
                        bibtex_citation += f"}}"
                    
                    elif type_publication == 'proceedings-article':
                        bibtex_citation = f"@CONFERENCE{{{article_id},\n"
                        bibtex_citation += f"\tauthor = {{{authors}}},\n"
                        bibtex_citation += f"\ttitle = {{{title}}},\n"
                        bibtex_citation += f"\tyear = {{{year}}},\n"
                        bibtex_citation += f"\tbooktitle = {{{journal_or_conference}}},\n"
                        bibtex_citation += f"\tdoi = {{{doi}}},\n"
                        bibtex_citation += f"\turl = {{{url}}}\n"
                        bibtex_citation += f"}}"
                    
                    else:
                        bibtex_citation = f"@MISC{{{article_id},\n"
                        bibtex_citation += f"\tauthor = {{{authors}}},\n"
                        bibtex_citation += f"\ttitle = {{{title}}},\n"
                        bibtex_citation += f"\tyear = {{{year}}},\n"
                        bibtex_citation += f"\thowpublished = {{{journal_or_conference}}},\n"
                        bibtex_citation += f"\tdoi = {{{doi}}},\n"
                        bibtex_citation += f"\turl = {{{url}}}\n"
                        bibtex_citation += f"}}"
                        
                    
                    # Další typy publikací
                    # (kód pro další typy článků zůstává stejný)
                    
                    # Výstupní data
                    return {
                        'title': title,
                        'authors': authors,
                        'journal_or_conference': journal_or_conference,
                        'year': year,
                        'doi': doi,
                        'url': url,
                        'volume': volume,
                        'issue': issue,
                        'bibtex_citation': bibtex_citation
                    }

            # Pokud nebyla nalezena žádná shoda
            return {"error": "Název článku nesouhlasí s výsledky z API."}
        
        else:
            return {"error": "Žádné výsledky nebyly nalezeny."}
    else:
        return {"error": "Chyba při dotazu na API."}