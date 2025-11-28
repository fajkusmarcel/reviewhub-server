# Standardní knihovny Pythonu
import os
import re
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from functools import wraps

# Knihovny třetích stran (nainstalované přes pip)
from flask import Blueprint, render_template, make_response, request, redirect, url_for, session, current_app, flash, jsonify
from flask_mysqldb import MySQL


# Vlastní moduly (část tvé aplikace)
from files.files import *
from db.sql_query import *
from utils.utils import *
from utils.decorators import *
from .gpt import *
from utils.logger import log_info, log_warning, log_error
from utils.responsive import wants_mobile, render_responsive


# Definice blueprintu pro uživatele
publication_bp = Blueprint('publication', __name__)




@publication_bp.route('/publication', methods=['GET'])
@login_required
@project_required
def publication():
    """
    Zobrazeni publikaci v projektu
    """    
    # ID vybraného projektu
    selected_project = session['selected_project']

    # Načtení vyhledávacího dotazu a možností filtrování
    search_query = request.args.get('search_query', '')
    search_option = request.args.get('search_option', 'any')
    search_terms = search_query.split() if search_query else []

    # Načtení filtrů z požadavku
    filters = {
        'filter_Casopis': request.args.get('filter_Casopis'),
        'filter_RokVydani': request.args.get('filter_RokVydani'),
        'filter_TypSenzoru': request.args.get('filter_TypSenzoru'),
        'filter_PrincipSenzoru': request.args.get('filter_PrincipSenzoru'),
        'filter_Velicina': request.args.get('filter_Velicina'),
        'filter_ZpusobZapouzdreni': request.args.get('filter_ZpusobZapouzdreni'),
        'filter_ZpusobImplementace': request.args.get('filter_ZpusobImplementace'),
        'filter_Kategorie': request.args.get('filter_Kategorie'),
        'filter_Podkategorie': request.args.get('filter_Podkategorie'),
        'filter_UsedInReview': request.args.get('filter_UsedInReview'),
        'filter_Pubtype': request.args.get('filter_Pubtype')

    }

    # Razeni vysledku
    sorting = {
        'sort_column_name': request.args.get('sort_column_name'),
        'sort_order': request.args.get('sort_order')
    }

    # Načtení publikací s filtry a vyhledáváním
    clanky = sql_get_filtered_publications(selected_project, search_terms, search_option, filters, sorting)
    pocetClanku = len(clanky)
    pocetClankuCelkem = sql_get_number_of_publications_in_project(selected_project)

    # Načtení unikátních hodnot pro filtry
    casopisy = sql_get_unique_values(selected_project, 'journal')
    roky_vydani = sql_get_unique_values(selected_project, 'year_publication')
    typy_senzoru = sql_get_unique_values(selected_project, 'sensor_type')
    principy_senzoru = sql_get_unique_values(selected_project, 'sensor_principle')
    veliciny = sql_get_unique_values(selected_project, 'measured_value')
    zpusoby_zapouzdreni = sql_get_unique_values(selected_project, 'encapsulation')
    zpusoby_implementace = sql_get_unique_values(selected_project, 'implementation')
    kategorie = sql_get_unique_values(selected_project, 'category')
    podkategorie = sql_get_unique_values(selected_project, 'subcategory')
    usedInReview = ['ANO', 'NE']
    pub_types = ['article', 'review', 'patent', 'UV', 'FVZ', 'poloprovoz', 'Zenodo', 'URL', 'book', 'chapter']

    sorting = [
        {'column_name': 'publication_id', 'display_name': 'Inserted'},
        {'column_name': 'publication_name', 'display_name': 'Publication name'},
        {'column_name': 'journal', 'display_name': 'Journal'},
        {'column_name': 'year_publication', 'display_name': 'Year of publication'},
        {'column_name': 'category', 'display_name': 'Category'},
        {'column_name': 'subcategory', 'display_name': 'Sub-category'},
        {'column_name': 'encapsulation', 'display_name': 'Encapsulation'},
        {'column_name': 'implementation', 'display_name': 'Implementation'},
        {'column_name': 'sensor_type', 'display_name': 'Sensor type'},
        {'column_name': 'sensor_principle', 'display_name': 'Sensor principle'},
        {'column_name': 'construction_principle', 'display_name': 'Construction principle'},
        {'column_name': 'measured_value', 'display_name': 'Measured value'}
    ]
    sorting_order = [
        {'order': 'desc', 'display_name': 'Sestupně'},
        {'order': 'asc', 'display_name': 'Vzestupně'}
    ]

    projekt = sql_get_project(selected_project)

    view = request.args.get('view') or session.get('article_view', 'table')
    if view not in ('table', 'cards'):
        view = 'table'
        session['article_view'] = view

    template_name = 'publication_cards.html' if view == 'cards' else 'publication.html'

    # Předání dat šabloně
    return render_responsive(template_name, 'publication_mobile.html',
                           clanky=clanky, 
                           pocetClanku=pocetClanku,
                           pocetClankuCelkem=pocetClankuCelkem,
                           casopisy=casopisy,
                           roky_vydani=roky_vydani,
                           typy_senzoru=typy_senzoru,
                           veliciny=veliciny,
                           principy_senzoru=principy_senzoru,
                           zpusoby_zapouzdreni=zpusoby_zapouzdreni,
                           zpusoby_implementace=zpusoby_implementace,
                           kategorie=kategorie,
                           podkategorie=podkategorie,
                           usedInReview=usedInReview,
                           pub_types=pub_types,
                           sorting=sorting,
                           sorting_order=sorting_order,
                           projekt=projekt,
                           site_name="Publications")

@publication_bp.route('/publication_all', methods=['GET', 'POST'])
@login_required
@project_required
def publication_all():
    """
    Zobrazeni všech publikací
    """    
    # ID vybraného projektu
    selected_project = session['selected_project']

    # Načtení vyhledávacího dotazu a možností filtrování
    search_query = request.args.get('search_query', '')
    search_option = request.args.get('search_option', 'any')
    search_terms = search_query.split() if search_query else []
    
    # Načtení filtrů z požadavku
    filters = {
        'filter_Casopis': request.args.get('filter_Casopis'),
        'filter_RokVydani': request.args.get('filter_RokVydani'),
        'filter_TypSenzoru': request.args.get('filter_TypSenzoru'),
        'filter_PrincipSenzoru': request.args.get('filter_PrincipSenzoru'),   
        'filter_Velicina': request.args.get('filter_Velicina'),     
        'filter_ZpusobZapouzdreni': request.args.get('filter_ZpusobZapouzdreni'),
        'filter_ZpusobImplementace': request.args.get('filter_ZpusobImplementace'),
        'filter_Kategorie': request.args.get('filter_Kategorie'),
        'filter_Podkategorie': request.args.get('filter_Podkategorie'),
        'filter_UsedInReview': request.args.get('filter_UsedInReview'),
        'filter_UsedInProject': request.args.get('filter_UsedInProject')
    }


    # Razeni vysledku
    sorting = {
        'sort_column_name': request.args.get('sort'),
        'sort_order': request.args.get('sort_order')
    }

    # Načtení publikací s filtry a vyhledáváním
    clanky = sql_get_all_publications(search_terms, search_option, filters, selected_project, sorting)
    pocetClanku = len(clanky)
    pocetClankuCelkem = sql_get_number_of_publications_in_system()
    # Získání informace, zda je článek již přiřazen k projektu
    for clanek in clanky:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM publicationproject WHERE publication_id = %s AND project_id = %s', (clanek['publication_id'], selected_project))
        assigned_project = cursor.fetchone()
        clanek['assigned'] = True if assigned_project else False
        cursor.close()

    selected_project = 1    # default
    # Načtení unikátních hodnot pro filtry
    casopisy = sql_get_unique_values(selected_project, 'journal')
    roky_vydani = sql_get_unique_values(selected_project, 'year_publication')
    typy_senzoru = sql_get_unique_values(selected_project, 'sensor_type')
    principy_senzoru = sql_get_unique_values(selected_project, 'sensor_principle')
    veliciny = sql_get_unique_values(selected_project, 'measured_value')
    zpusoby_zapouzdreni = sql_get_unique_values(selected_project, 'encapsulation')
    zpusoby_implementace = sql_get_unique_values(selected_project, 'implementation')
    kategorie = sql_get_unique_values(selected_project, 'category')
    podkategorie = sql_get_unique_values(selected_project, 'subcategory')
    sorting = [
        {'column_name': 'publication_id', 'display_name': 'Inserted'},
        {'column_name': 'publication_name', 'display_name': 'Publication name'},        
        {'column_name': 'journal', 'display_name': 'Journal'},
        {'column_name': 'year_publication', 'display_name': 'Year of publication'},
        {'column_name': 'category', 'display_name': 'Category'},
        {'column_name': 'subcategory', 'display_name': 'Sub-category'},
        {'column_name': 'encapsulation', 'display_name': 'Encapsulation'},
        {'column_name': 'implementation', 'display_name': 'Implementation'},
        {'column_name': 'sensor_type', 'display_name': 'Sensor type'},
        {'column_name': 'sensor_principle', 'display_name': 'Sensor principle'},
        {'column_name': 'construction_principle', 'display_name': 'Construction principle'},
        {'column_name': 'measured_value', 'display_name': 'Measured value'}        
    ]
    sorting_order = [
        {'order': 'desc', 'display_name': 'Sestupně'},
        {'order': 'asc', 'display_name': 'Vzestupně'}
    ]

    usedInReview = ['ANO', 'NE']
    usedInProject = ['ANO', 'NE']

    # Předání dat šabloně
    return render_template('publication_import.html', 
                           clanky=clanky, 
                           pocetClanku=pocetClanku,
                           pocetClankuCelkem=pocetClankuCelkem,
                           casopisy=casopisy,
                           roky_vydani=roky_vydani,
                           typy_senzoru=typy_senzoru,
                           principy_senzoru=principy_senzoru,
                           veliciny=veliciny,
                           zpusoby_zapouzdreni=zpusoby_zapouzdreni,
                           zpusoby_implementace=zpusoby_implementace,
                           kategorie=kategorie,
                           podkategorie=podkategorie,
                           usedInReview=usedInReview,
                           usedInProject=usedInProject,
                           sorting=sorting,
                           sorting_order=sorting_order,
                           site_name="Publications")


@publication_bp.route('/publication_search', methods=['GET', 'POST'])
@login_required
@project_required
def publication_search():
    
    if request.method == 'GET':
        return render_template('publication_search.html', site_name="Hledat")
    
    search_data = request.get_json()
    search_query = search_data.get('search_query', '')
    search_query = search_query.replace('-', ' ')

    
    
    if not search_query:
        return jsonify([])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    

    # Fulltextové vyhledávání pomocí MATCH a AGAINST
    cursor.execute('''
        SELECT publication_id, publication_name, journal, year_publication, authors
            FROM publication 
            WHERE MATCH(publication_name) AGAINST (%s IN BOOLEAN MODE);
    ''', (search_query,))
    #ORDER BY exact_match DESC, MATCH(publication_name) AGAINST(%s IN BOOLEAN MODE) DESC

    results = cursor.fetchall()
    print(results)
    cursor.close()

    return jsonify(results)
    

@publication_bp.route('/publication_import/<int:clanek_id>', methods=['GET', 'POST'])
@login_required
@project_required
def publication_import(clanek_id):
    """
    Přidá článek k vybranému projektu.
    """
    selected_project = session.get('selected_project')  # ID aktuálně vybraného projektu
    user_id = session.get('user_id')  # ID přihlášeného uživatele
    
    # Zkontroluj, zda již není článek přiřazen k projektu
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT * FROM publicationproject WHERE publication_id = %s AND project_id = %s
    ''', (clanek_id, selected_project))
    existing_assignment = cursor.fetchone()
    
    if existing_assignment:
        flash('Tento článek již byl přiřazen k tomuto projektu.', 'warning')
        return redirect(url_for('publication.publication_all'))  # Přesměrování zpět na seznam článků

    # Vložení záznamu do tabulky PublicationProject
    cursor.execute('''
        INSERT INTO publicationproject (publication_id, project_id) 
        VALUES (%s, %s)
    ''', (clanek_id, selected_project))
    conn.commit()

    cursor.execute('''
        SELECT * FROM publicationtracking
        WHERE publication_id = %s AND project_id = 1            
    ''', (clanek_id, ))
    tracking = cursor.fetchone()
    print(tracking)

    if(tracking is None):
        cursor.execute('''
            INSERT INTO publicationtracking (publication_id, project_id, user_id_added, user_id_last_modified, user_id_completed) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (clanek_id, selected_project, user_id, user_id, user_id))
    else:
        cursor.execute('''
            INSERT INTO publicationtracking (publication_id, project_id, user_id_added, added_at, user_id_last_modified, last_modified_at, user_id_completed, completed_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (clanek_id, selected_project, tracking['user_id_added'], tracking['added_at'], tracking['user_id_last_modified'], tracking['last_modified_at'], tracking['user_id_completed'], tracking['completed_at']))
    conn.commit()

    # Vložení do tabulky PublicationTracking
    #sql_insert_publication_tracking(clanek_id, selected_project, user_id)
    #sql_update_publication_tracking(clanek_id, selected_project, user_id)

    return redirect(url_for('publication.publication_all'))



@publication_bp.route('/publication_add', methods=['GET', 'POST'])
@login_required
@project_required
def publication_add():
    """
    Pridani publikace
    """
    # ID vybraneho projektu
    selected_project = session['selected_project']


    if request.method == 'POST':
        # Načtení dat z formuláře
        form_data = extract_form_data(request)

        # Zpracování nahraného PDF souboru
        pdf_soubor = request.files['pdf_soubor']
        pdf_filename = None  # Výchozí hodnota, pokud není nahrán žádný soubor

        # Získání unikátního ID pro nový záznam
        next_id = sql_get_next_publication_id()

        # Ověření, zda soubor byl nahrán a je to PDF
        if pdf_soubor and pdf_soubor.filename.endswith('.pdf'):

            # Název souboru ve formátu "ID_nazev_clanku.pdf"
            pdf_filename = f"{next_id}_{secure_filename(form_data['nazev_clanku'])}.pdf"
            # Cesta k adresáři projektu
            projekt_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])  # Upravena cesta pro adresář projektu
            os.makedirs(projekt_dir, exist_ok=True)  # Vytvoří adresář, pokud neexistuje

            # Uložení souboru do adresáře projektu
            pdf_path = os.path.join(projekt_dir, pdf_filename)
            pdf_soubor.save(pdf_path)  # Uložení souboru            

        # Inicializace promenne
        publication_id = 0

        # Informace z databaze SCOPUS
        scopus_data = get_article_info_from_SCOPUS(form_data['nazev_clanku'], next_id)

        
        if 'error' in scopus_data: 
            # Informace z formulare

            # Vyber kategorie z roletkoveho menu nebo zapsane

            selected = request.form.get('kategorie_select')
            category = request.form.get('kategorie') if selected == '__NEW__' else selected
            selected = request.form.get('podkategorie_select')
            subcategory = request.form.get('podkategorie') if selected == '__NEW__' else selected
            pub_type = request.form.get('pubtype_select')

            # Pokud neni rok vydani vyplnen - prevedeme prazdny retezec na 1900
            rok_raw = form_data['rok_vydani']
            try:
                rok_vydani = int(rok_raw) if rok_raw else 1900
            except ValueError:
                rok_vydani = 1990

            publication_id = sql_insert_publication(selected_project, form_data['nazev_clanku'], form_data['abstract'], form_data['casopis'],
                                rok_vydani, form_data['typ_senzoru'], form_data['princip_senzoru'], form_data['konstrukce_senzoru'],
                                form_data['typ_optickeho_vlakna'], form_data['zpusob_zapouzdreni'], form_data['zpusob_implementace'],
                                category, subcategory, form_data['merena_velicina'],
                                form_data['rozsah_merani'], form_data['citlivost'], form_data['presnost'], form_data['frekvencni_rozsah'],
                                form_data['vyhody'], form_data['nevyhody'], form_data['aplikace_studie'], form_data['klicove_poznatky'], form_data['summary'],
                                form_data['poznamky'], pdf_filename, form_data['obrazky'], form_data['autori'], form_data['doi'], form_data['citaceBib'], 0, pub_type, form_data['rating'])
        else:
            # Informace ze SCOPUS - ověření a ošetření hodnot
            title = scopus_data["title"] if scopus_data.get("title") != 'N/A' else form_data['nazev_clanku']
            journal = scopus_data["journal_or_conference"] if scopus_data.get("journal_or_conference") != 'N/A' else form_data['casopis']

            # Pokud rok není číslo, nastavíme na form_data nebo 2024 jako výchozí hodnotu
            try:
                year = int(scopus_data["year"]) if scopus_data.get("year") and scopus_data["year"] != 'N/A' else int(form_data['rok_vydani'])
            except ValueError:
                # Defaultní hodnota, pokud API vrátí neplatný rok
                year = 1900

            authors = scopus_data.get("authors", form_data['autori'])
            doi = scopus_data.get("doi", form_data['doi'])
            bibtex_citation = scopus_data.get("bibtex_citation", form_data['citaceBib'])

            # Vložení záznamu do databáze s kontrolovanými hodnotami


            # Vyber kategorie z roletkoveho menu nebo zapsane

            selected = request.form.get('kategorie_select')
            category = request.form.get('kategorie') if selected == '__NEW__' else selected
            selected = request.form.get('podkategorie_select')
            subcategory = request.form.get('podkategorie') if selected == '__NEW__' else selected
            pub_type = request.form.get('pubtype_select')

            publication_id = sql_insert_publication(
                selected_project, title, form_data['abstract'], journal,
                year, form_data['typ_senzoru'], form_data['princip_senzoru'], form_data['konstrukce_senzoru'],
                form_data['typ_optickeho_vlakna'], form_data['zpusob_zapouzdreni'], form_data['zpusob_implementace'],
                category, subcategory, form_data['merena_velicina'],
                form_data['rozsah_merani'], form_data['citlivost'], form_data['presnost'], form_data['frekvencni_rozsah'],
                form_data['vyhody'], form_data['nevyhody'], form_data['aplikace_studie'], form_data['klicove_poznatky'], form_data['summary'],
                form_data['poznamky'], pdf_filename, form_data['obrazky'], authors, doi, bibtex_citation, 1, pub_type, form_data['rating'])

        # Vložení do tabulky ArticleTracking
        user_id = session['user_id']  # ID přihlášeného uživatele


        # Volání funkcí pro vložení a nastavení stavu v tabulce PublicationTracking        
        sql_insert_publication_to_project(publication_id, selected_project)  # Vložení nové publikace

        # Pokud je selected_project různé od 1, vloží publikaci i do projektu s ID 1
        #if int(selected_project) != 1:
        #    sql_insert_publication_to_project(publication_id, 1)

        # Volání funkcí pro vložení a nastavení stavu v tabulce PublicationTracking
        sql_insert_publication_tracking(publication_id, selected_project, user_id)  # Vložení nové publikace
        sql_update_publication_tracking(publication_id, selected_project, user_id)  # Aktualizace s časem poslední změny
        sql_complete_publication_tracking(publication_id, selected_project, user_id, form_data['stav'])


        # Přesměrování po úspěšném vložení
        title = form_data['nazev_clanku']
        log_info("pub_add", f"uzivatel vlozil clanek {title} do databaze")

        return redirect(url_for('publication.publication'))

    # Při GET načteme seznam projektů pro roletkové menu ve formuláři
    projekty = sql_get_projects()
    kategorie = sorted(sql_get_categories())
    podkategorie = sorted(sql_get_subcategories())
    pub_types = ['article', 'review', 'patent', 'UV', 'FVZ', 'poloprovoz', 'Zenodo', 'URL', 'book', 'chapter']

    return render_template('publication_add.html', projekty=projekty, kategorie=kategorie, podkategorie=podkategorie, pub_types=pub_types, site_name="Add publication")



@publication_bp.route('/publication_edit/<int:clanek_id>', methods=['GET'])
@login_required
@project_required
def publication_edit(clanek_id):
    """
    Editace publikace
    """    
    # ID vybraného projektu
    selected_project = session['selected_project']

    # Načtení detailů článku
    clanek_dict = sql_get_publication(clanek_id, selected_project)

    if clanek_dict is None:
        return "Článek nebyl nalezen.", 404

    # Načtení všech projektů
    projekty = sql_get_projects()

    pub_types = ['article', 'review', 'patent', 'UV', 'FVZ', 'poloprovoz', 'Zenodo', 'URL', 'book', 'chapter']

    # Zkontroluj, zda PDF soubor existuje
    pdf_name = f"{clanek_id}_{secure_filename(clanek_dict['publication_name'])}.pdf" 
    projekt_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])    
    file_path = os.path.join(projekt_dir, pdf_name) 
    pdf_exists = os.path.exists(file_path)

    # Předání dat do šablony
    return render_template('publication_edit.html', clanek=clanek_dict, projekty=projekty, pdf_exists=pdf_exists, pub_types=pub_types,site_name="Edit publication")


@publication_bp.route('/publication_pdf2text', methods=['GET', 'POST'])
@login_required
@project_required
def publication_pdf2text():
    """
    Konverze PDF na text
    """    
    if request.method == 'GET':
        return render_template('publication_pdf2text.html')

            
    # Pokud je POST požadavek s nahraným souborem
    if 'pdf_soubor' in request.files:
        pdf_file = request.files['pdf_soubor']

        projekt_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'tmp') 
        pdf_name = pdf_file.filename        
        pdf_path = os.path.join(projekt_dir, pdf_name)
        save_file(pdf_file, projekt_dir, pdf_name)
    
        # Extrakce textu ze souboru
        text = pdf2text(pdf_path)

        # Smazani docasneho souboru
        delete_file(pdf_path)

        ai_a_config_text = ''
        if session['user_role'] == 'admin':
            ai_a_config_text = load_ai_a_config()
        
        with open("./static/uplouds/tmp/export.txt", "w", encoding="utf-8") as file:
            file.write(text)

        # Vrácení textu jako JSON odpověď
        return jsonify({'text': text, 'ai_a_config': ai_a_config_text})

    return jsonify({'error': 'PDF soubor nebyl nahrán.'}), 400


@publication_bp.route('/publication_update/<int:clanek_id>', methods=['POST'])
@login_required
@project_required
def publication_update(clanek_id):
    # ID vybraného projektu
    selected_project = session['selected_project']


    # Získání dat z formuláře
    form_data = extract_form_data(request)
    nazev_clanku = form_data['nazev_clanku']

    pdf_file = request.files['pdf_soubor']
    projekt_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])   
    
    pdf_name_old = sql_get_pdf_filename(clanek_id)
    if pdf_name_old is None:            
        file_path_old = ''
    else:
        file_path_old = os.path.join(projekt_dir, pdf_name_old)

    # Zpracování nového PDF souboru
    pdf_name_new = ''         
    file_path_new = ''            
    
    
    if pdf_file and pdf_file.filename != '':
        # SOUBOR BYL VLOZEN - smazani stareho a ulozeni noveho
        pdf_name_new = f"{clanek_id}_{secure_filename(nazev_clanku)}.pdf"        
        file_path_new = os.path.join(projekt_dir, pdf_name_new)            
        delete_file(file_path_old)
        save_file(pdf_file, projekt_dir, pdf_name_new)
    else:
        # SOUBOR NEBYL VLOZEN
        if os.path.exists(file_path_old):
            if pdf_name_old  != pdf_name_new:
                # SOUBOR NEBYL VLOZEN - ale doslo k prejmenovani clanku                  
                pdf_name_new = f"{clanek_id}_{secure_filename(nazev_clanku)}.pdf"   
                file_path_new = os.path.join(projekt_dir, pdf_name_new)
                rename_file(file_path_old, file_path_new)

    pub_type = form_data['pubtype_select']

    # Aktualizace článku
    sql_update_publication(clanek_id, form_data['nazev_clanku'], form_data['abstract'], form_data['casopis'],
                        form_data['rok_vydani'], form_data['typ_senzoru'], form_data['princip_senzoru'], form_data['konstrukce_senzoru'],
                        form_data['typ_optickeho_vlakna'], form_data['zpusob_zapouzdreni'], form_data['zpusob_implementace'],
                        form_data['kategorie'], form_data['podkategorie'], form_data['merena_velicina'],
                        form_data['rozsah_merani'], form_data['citlivost'], form_data['presnost'],
                        form_data['frekvencni_rozsah'], form_data['vyhody'], form_data['nevyhody'], form_data['aplikace_studie'],
                        form_data['klicove_poznatky'], form_data['summary'], form_data['poznamky'], form_data['obrazky'], form_data['autori'], form_data['doi'], form_data['citaceBib'],
                        form_data['stav'], selected_project, pdf_name_new, pub_type, form_data['rating'])
    


    # Vložení do tabulky ArticleTracking
    user_id = session['user_id']  # ID přihlášeného uživatele
    # Volání funkcí pro vložení a nastavení stavu v tabulce PublicationTracking
    sql_update_publication_tracking(clanek_id, selected_project, user_id)  # Aktualizace s časem poslední změny
    sql_complete_publication_tracking(clanek_id, selected_project, user_id, form_data['stav'])    

    return redirect(url_for('publication.publication'))  # Přesměrování zpět na seznam článků


@publication_bp.route('/publication_check', methods=['GET', 'POST'])
@login_required
@project_required
def publication_check():
    """
    Kontrola, zda nazev clanku jiz neni v databazi
    """    
    print("Publication check")
    if request.method == 'POST':
        # Načtení dat z požadavku
        form_data = request.get_json()
        nazev = form_data.get('nazev_clanku')

        # Zkontroluj, zda článek existuje
        exists = sql_check_publication_name_exists(nazev)

        # Vrácení výsledku jako JSON
        return jsonify({'exists': exists})
        
    return render_template('publication_check.html')




    

@publication_bp.route('/publication_delete/<int:clanek_id>', methods=['GET', 'DELETE'])
@login_required
@project_required
def publication_delete(clanek_id):
    """
    Odstraneni publikace
    """    
    # ID vybraneho projektu
    selected_project = session['selected_project']

    # Načtení názvu PDF souboru
    pdf_filename = sql_get_pdf_filename(clanek_id)

    # Smazání článku z tabulky Publikace
    sql_delete_publication(clanek_id, selected_project)

    # Zjistíme, zda bude článek smazán i z tabulky Publication
    publication_exist = sql_exist_publication(clanek_id)

    # Odstranění PDF souboru, pokud existuje
    if publication_exist == False and pdf_filename and pdf_filename[0]:  # Přidání kontroly pro prázdný název souboru
        projekt_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])
        pdf_path = os.path.join(projekt_dir, pdf_filename[0])
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    return redirect(url_for('publication.publication'))

@publication_bp.route('/publication_delete_from_system/<int:clanek_id>', methods=['DELETE'])
@login_required
@project_required
def publication_delete_from_system(clanek_id):
    """
    Odstraneni publikace
    """    
    # ID vybraneho projektu
    selected_project = session['selected_project']

    # Načtení názvu PDF souboru
    pdf_filename = sql_get_pdf_filename(clanek_id)

    # Smazání článku z tabulky Publikace
    sql_delete_publication_from_system(clanek_id, selected_project)

    
    # Odstranění PDF souboru, pokud existuje
    if pdf_filename:  # Přidání kontroly pro prázdný název souboru
        projekt_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])
        pdf_path = os.path.join(projekt_dir, pdf_filename)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    return '', 204  # Vrátí 204 No Content


@publication_bp.route('/publication_detail/<int:clanek_id>')
@login_required
@project_required
def publication_detail(clanek_id):
    """
    Vrati informace  clanku ve formatu JSON - zobrazeni informaci 
    v postrannim paneu v seznamu clanku
    """    
    # Načtení detailů článku
    clanek = sql_get_publication(clanek_id)

    if clanek is None:
        return "Článek nebyl nalezen.", 404

    return(clanek)


@publication_bp.route('/publication_update_UsedInReview', methods=['POST'])
@login_required
@project_required
def publication_update_UsedInReview():    
    data = request.get_json()  # Získá data z AJAX požadavku
    article_id = data.get('articleId')
    project_id = session['selected_project']
    used_in_review = data.get('usedInReview')

    if(sql_check_publication_in_review(article_id, project_id, used_in_review) == False):
        sql_publication_update_UsedInReview(article_id, project_id, used_in_review)
    
    return jsonify({'message': 'Úspěšně uloženo'})



@publication_bp.route('/publication_bib', methods=['GET', 'POST'])
@login_required
@project_required
def publication_bib():
    """
    Seznam BIB referenci z poskztnuteho textu, kde id clanku jsou v hranatych zavorkach
    """    
    # ID vybraneho projektu
    selected_project = session['selected_project']

    response = {}

    if request.method == 'POST':
        text = request.form['input_text']
        response['input_text'] = text;

         # Vyhledání všech čísel v hranatých závorkách
        ids_in_text = re.findall(r'\[(\d+)\]', text)

        # Unikátní čísla
        unique_ids = list(set(ids_in_text))

        # Seznam pro citace
        references = []

        # Pro každé ID proveď dotaz do databáze
        for pub_id in unique_ids:
            citation = sql_get_citation_by_id_article(pub_id)
            if citation:
                references.append(citation)

        # Vytvoření řetězce citací, oddělených prázdným řádkem
        response['references'] = '\n'.join(references)

        # Předáš reference šabloně a vrátíš ji
        return render_template('publication_bib.html', response=response, site_name="Citations")
        
    else:
        # V případě GET requestu jen zobrazíš prázdnou šablonu
        return render_template('publication_bib.html', response=response, site_name="Citations")


@publication_bp.route('/publication_setRating/<int:article_id>', methods=['POST'])
@login_required
@project_required
def publication_setRating(article_id):
    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get('rating', 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, error='Bad rating'), 400
    if rating not in (0, 1, 2, 3):
        return jsonify(ok=False, error='Out of range'), 400

    # TODO: ověř, že článek patří do vybraného projektu uživatele
    sql_update_publication_rating(article_id, rating)
    return jsonify(ok=True, rating=rating)



