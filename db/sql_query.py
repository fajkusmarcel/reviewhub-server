from flask import current_app  # Přístup ke konfiguraci aplikace
from flask_mysqldb import MySQL
from datetime import datetime, timedelta

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from utils import *  # Obecné pomocné funkce (pokud existují)

import mysql.connector

# Funkce pro připojení k databázi
def get_db_connection():
    
    conn = mysql.connector.connect(
        host = current_app.config['MYSQL_HOST'],
        user = current_app.config['MYSQL_USER'],
        password = current_app.config['MYSQL_PASSWORD'],
        database = current_app.config['MYSQL_DB']
    )
    return conn




# ***********************************************************************************************************************
#      DASHBOARD
# ***********************************************************************************************************************

def sql_get_processed_articles_by_day(project_id):
    """
    Získá počet zpracovaných článků v jednotlivých dnech.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání data prvního a posledního zpracovaného článku
    cursor.execute('''
        SELECT MIN(completed_at) AS first_date, MAX(completed_at) AS last_date
        FROM publicationtracking
        WHERE project_id = %s AND completed_at IS NOT NULL
    ''', (project_id,))
    result = cursor.fetchone()

    if result['first_date'] and result['last_date']:
        first_date = result['first_date']
        last_date = result['last_date']

        # Příprava slovníku s počty článků pro každý den
        cursor.execute('''
            SELECT DATE(added_at) AS date, COUNT(publication_id) AS count
            FROM publicationtracking
            WHERE project_id = %s AND added_at IS NOT NULL
            GROUP BY DATE(added_at)
        ''', (project_id,))
        articles_by_day = cursor.fetchall()

        # Generování všech dní mezi prvním a posledním dnem
        current_date = first_date
        date_dict = {current_date.strftime('%Y-%m-%d'): 0}

        while current_date <= last_date:
            date_dict[current_date.strftime('%Y-%m-%d')] = 0
            current_date += timedelta(days=1)

        # Aktualizace hodnot v date_dict podle skutečných dat
        for row in articles_by_day:
            date_dict[row['date'].strftime('%Y-%m-%d')] = row['count']

        cursor.close()
        return date_dict
    else:
        return {}  # Pokud nejsou zpracované žádné články
    
def sql_get_total_articles_by_project(project_id):
    """
    Získá celkový počet článků podle projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT COUNT(*) AS total
        FROM publicationproject pp
        JOIN publication p ON pp.publication_id = p.publication_id
        WHERE pp.project_id = %s
    ''', (project_id,))
    total_articles = cursor.fetchone()['total']
    cursor.close()
    return total_articles

def sql_get_total_articles_by_status(project_id, state):
    """
    Získá počet článků podle stavu (zadáno nebo zpracováno) v projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    total_articles = None
    if(state == 'zpracovano'):
        # Počet článků, které mají vyplněný completed_at (stav: zpracováno)
        cursor.execute('''
            SELECT
                SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS total_processed
            FROM publicationtracking
            WHERE project_id = %s;
        ''', (project_id,))
        total_articles = cursor.fetchone()['total_processed'] or 0
    else:
        # Počet článků, které nemají vyplněný completed_at (stav: zadáno)
        cursor.execute('''
            SELECT
                SUM(CASE WHEN completed_at IS NULL THEN 1 ELSE 0 END) AS total_entered
            FROM publicationtracking
            WHERE project_id = %s;
        ''', (project_id,))

        total_articles = cursor.fetchone()['total_entered'] or 0
    cursor.close()

    return total_articles

def get_publication_id(publication_name):
    """
    Vrací publication_id na základě názvu článku.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = '''
        SELECT publication_id
        FROM publication
        WHERE publication_name = %s
        LIMIT 1
    '''
    
    cursor.execute(query, (publication_name,))
    result = cursor.fetchone()
    cursor.close()

    # Zkontrolujeme, zda byl nalezen záznam
    if result:
        return result['publication_id']
    else:
        return None


# ************************************************************************
# Data pro clanky v projektu
def sql_get_articles_grouped_by_year(project_id):
    """
    Získá počet článků podle roku vydání a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle roku vydání a projektu
    cursor.execute('''
        SELECT
            p.year_publication AS RokVydani,
            COUNT(*) AS total
        FROM
            publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
        WHERE
            pp.project_id = %s
        GROUP BY
            p.year_publication
        ORDER BY
            p.year_publication;
    ''', (project_id,))

    articles_by_year = cursor.fetchall()
    cursor.close()

    return articles_by_year


def sql_get_articles_grouped_by_category(project_id):
    """
    Získá počet článků podle kategorie a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle roku vydání a projektu
    cursor.execute('''
        SELECT
            IFNULL(p.category, 'None') AS Kategorie,
            COUNT(*) AS total
        FROM
            publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
        WHERE
            pp.project_id = %s
        GROUP BY
            Kategorie
        ORDER BY
            total DESC;
    ''', (project_id,))

    articles_by_category = cursor.fetchall()
    cursor.close()

    return articles_by_category

def sql_get_articles_grouped_by_subcategory(project_id):
    """
    Získá počet článků podle podkategorie a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle roku vydání a projektu
    cursor.execute('''
        SELECT
            IFNULL(p.subcategory, 'None') AS Podkategorie,
            COUNT(*) AS total
        FROM
            publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
        WHERE
            pp.project_id = %s
        GROUP BY
            Podkategorie
        ORDER BY
            total DESC;
    ''', (project_id,))

    articles_by_subcategory = cursor.fetchall()
    cursor.close()

    return articles_by_subcategory


def sql_get_articles_grouped_by_sensor_type(project_id):
    """
    Získá počet článků podle typu senzorů a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle typu senzorů pro daný projekt
    cursor.execute('''
        SELECT
            COALESCE(p.sensor_type, 'Neznámý typ') AS TypSenzoru,
            COUNT(*) AS total
        FROM
            publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
        WHERE
            pp.project_id = %s
        GROUP BY
            TypSenzoru
        ORDER BY
            total DESC;
    ''', (project_id, ))

    articles_by_sensor_type = cursor.fetchall()
    cursor.close()

    return articles_by_sensor_type

# Data pro clanky v projektu zarazene do review
def sql_get_articles_in_review(project_id):
    """
    Získá počet článků použitých v review
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků použitých v review
    cursor.execute('''
        SELECT
            COUNT(*) AS total
        FROM
            publication p
            JOIN usedinreview uir ON p.publication_id = uir.publication_id
        WHERE
            uir.project_id = %s
    ''', (project_id,))

    articles_in_review = cursor.fetchall()
    cursor.close()

    return articles_in_review

# Data pro clanky v projektu zarazene do review
def sql_get_articles_grouped_by_year_in_review(project_id):
    """
    Získá počet článků podle roku vydání a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle roku vydání a projektu
    cursor.execute('''
        SELECT
            p.year_publication AS RokVydani,
            COUNT(*) AS total
        FROM
            publication p
            JOIN usedinreview uir ON p.publication_id = uir.publication_id
        WHERE
            uir.project_id = %s
        GROUP BY
            p.year_publication
        ORDER BY
            p.year_publication;
    ''', (project_id,))

    articles_by_year = cursor.fetchall()
    cursor.close()

    return articles_by_year


def sql_get_articles_grouped_by_category_in_review(project_id):
    """
    Získá počet článků podle kategorie a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle roku vydání a projektu
    cursor.execute('''
        SELECT
            IFNULL(p.category, 'None') AS Kategorie,
            COUNT(*) AS total
        FROM
            publication p
            JOIN usedinreview uir ON p.publication_id = uir.publication_id
        WHERE
            uir.project_id = %s
            AND p.category IS NOT NULL
        GROUP BY
            Kategorie
        ORDER BY
            total DESC;
    ''', (project_id,))

    articles_by_category = cursor.fetchall()
    cursor.close()

    return articles_by_category

def sql_get_articles_grouped_by_subcategory_in_review(project_id):
    """
    Získá počet článků podle podkategorie a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle roku vydání a projektu
    cursor.execute('''
        SELECT
            IFNULL(p.subcategory, 'None') AS Podkategorie,
            COUNT(*) AS total
        FROM
            publication p
            JOIN usedinreview uir ON p.publication_id = uir.publication_id
        WHERE
            uir.project_id = %s
            AND p.category IS NOT NULL
        GROUP BY
            Podkategorie
        ORDER BY
            total DESC;
    ''', (project_id,))

    articles_by_subcategory = cursor.fetchall()
    cursor.close()

    return articles_by_subcategory


def sql_get_articles_grouped_by_sensor_type_in_review(project_id):
    """
    Získá počet článků podle typu senzorů a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Získání počtu článků podle typu senzorů pro daný projekt
    cursor.execute('''
        SELECT
            COALESCE(p.sensor_type, 'Neznámý typ') AS TypSenzoru,
            COUNT(*) AS total
        FROM
            publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
            JOIN usedinreview uir ON p.publication_id = uir.publication_id
        WHERE
            uir.project_id = %s AND pp.project_id = %s
        GROUP BY
            TypSenzoru
        ORDER BY
            total DESC;
    ''', (project_id, project_id))

    articles_by_sensor_type = cursor.fetchall()
    cursor.close()

    return articles_by_sensor_type


 
def sql_get_processed_articles_by_author(project_id):
    """
    Získá počet zpracovaných článků podle autorů pro konkrétní projekt.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
        SELECT
            u.user_id,
            CONCAT(u.name, ' ', u.surname) AS full_name,
            COUNT(pt.publication_id) AS processed_count
        FROM
            user u
            JOIN userproject up ON u.user_id = up.user_id
            LEFT JOIN publicationtracking pt ON u.user_id = pt.user_id_completed AND pt.project_id = up.project_id AND pt.completed_at IS NOT NULL
        WHERE
            up.project_id = %s
        GROUP BY
            u.user_id, full_name;    

    ''', (project_id,))

    processed_articles = cursor.fetchall() or 0
    cursor.close()

    return processed_articles


def sql_get_non_processed_articles_by_author(project_id):
    """
    Získá počet nezpracovaných článků podle autorů pro konkrétní projekt.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
        SELECT
            u.user_id,
            CONCAT(u.name, ' ', u.surname) AS full_name,
            COUNT(pt.publication_id) AS non_processed_articles_count
        FROM
            user u
            JOIN userproject up ON u.user_id = up.user_id
            LEFT JOIN publicationtracking pt ON u.user_id = pt.user_id_added AND pt.project_id = up.project_id AND pt.completed_at IS NULL
        WHERE
            up.project_id = %s
        GROUP BY
            u.user_id, full_name;
    ''', (project_id,))

    non_processed_articles = cursor.fetchall() or 0
    cursor.close()

    return non_processed_articles



def sql_statistics():
    """
    
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
        SELECT
        (SELECT COUNT(*) FROM publication) AS total_articles,
        (SELECT COUNT(*) FROM publication WHERE pdf_name IS NOT NULL AND pdf_name != '') AS articles_with_pdf,
        (SELECT JSON_OBJECTAGG(year_publication, cnt)
         FROM (SELECT year_publication, COUNT(*) AS cnt FROM publication GROUP BY year_publication) AS sub_year) AS articles_by_year,
        (SELECT JSON_OBJECTAGG(category, cnt)
         FROM (SELECT category, COUNT(*) AS cnt FROM publication GROUP BY category) AS sub_category) AS articles_by_category,
        (SELECT JSON_OBJECTAGG(subcategory, cnt)
         FROM (SELECT subcategory, COUNT(*) AS cnt FROM publication GROUP BY subcategory) AS sub_subcategory) AS articles_by_subcategory,
        (SELECT JSON_OBJECTAGG(sensor_type, cnt)
         FROM (SELECT sensor_type, COUNT(*) AS cnt FROM publication GROUP BY sensor_type) AS sub_sensor_type) AS articles_by_sensor_type;
    ''')

    stat = cursor.fetchone()
    cursor.close()
    return stat

def sql_statistics_for_project(project_id):
    """
    
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
        SELECT
            (SELECT COUNT(*) 
            FROM publicationproject pp
            JOIN publication p ON pp.publication_id = p.publication_id
            WHERE pp.project_id = %s) AS total_articles,
            
            (SELECT COUNT(*)
            FROM publicationproject pp
            JOIN publication p ON pp.publication_id = p.publication_id
            WHERE pp.project_id = %s AND p.pdf_name IS NOT NULL AND p.pdf_name != '') AS articles_with_pdf,
            
            (SELECT JSON_OBJECTAGG(year_publication, cnt)
            FROM (SELECT p.year_publication, COUNT(*) AS cnt
                FROM publicationproject pp
                JOIN publication p ON pp.publication_id = p.publication_id
                WHERE pp.project_id = %s
                GROUP BY p.year_publication) AS sub_year) AS articles_by_year,
                
            (SELECT JSON_OBJECTAGG(category, cnt)
            FROM (SELECT p.category, COUNT(*) AS cnt
                FROM publicationproject pp
                JOIN publication p ON pp.publication_id = p.publication_id
                WHERE pp.project_id = %s
                GROUP BY p.category) AS sub_category) AS articles_by_category,
                
            (SELECT JSON_OBJECTAGG(subcategory, cnt)
            FROM (SELECT p.subcategory, COUNT(*) AS cnt
                FROM publicationproject pp
                JOIN publication p ON pp.publication_id = p.publication_id
                WHERE pp.project_id = %s
                GROUP BY p.subcategory) AS sub_subcategory) AS articles_by_subcategory,
                
            (SELECT JSON_OBJECTAGG(sensor_type, cnt)
            FROM (SELECT p.sensor_type, COUNT(*) AS cnt
                FROM publicationproject pp
                JOIN publication p ON pp.publication_id = p.publication_id
                WHERE pp.project_id = %s
                GROUP BY p.sensor_type) AS sub_sensor_type) AS articles_by_sensor_type;

    ''', (project_id, project_id, project_id, project_id, project_id, project_id))

    stat = cursor.fetchone()
    
    cursor.close()

    return stat
   
def sql_get_project_name_by_id(project_id):
    """
    Získá název projektu podle ID projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT project_name FROM project WHERE project_id = %s', (project_id,))
    project_name = cursor.fetchone()['project_name']
    cursor.close()
    return project_name




# ***********************************************************************************************************************
#      PUBLICATIONS
# ***********************************************************************************************************************
def sql_get_categories():
    """
    Získá seznam unikátních kategorií z tabulky publication.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT category FROM publication ORDER BY category ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Vrátíme seznam jen hodnot (ne dicty), např. ["FBG", "DAS", "Interferometry"]
    categories = [row['category'] for row in rows if row['category']]
    return categories

def sql_get_subcategories():
    """
    Získá seznam unikátních podkategorií z tabulky publication.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT subcategory FROM publication ORDER BY category ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Vrátíme seznam jen hodnot (ne dicty), např. ["FBG", "DAS", "Interferometry"]
    subcategories = [row['subcategory'] for row in rows if row['subcategory']]
    return subcategories


def sql_get_citation_by_id_article(pub_id):
    """
    Získá citaci BibTeX z publikace podle jejího ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT citation FROM publication WHERE publication_id = %s', (pub_id,))
    result = cursor.fetchone()
    cursor.close()
    return result['citation'] if result else None


def sql_get_publication(clanek_id, project_id):
    """
    Získá detaily článku podle jeho ID a projektu, včetně hodnoty usedinreview a stavu (zadaný/zpracovaný).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT p.*, uir.used_in_review, 
               CASE 
                   WHEN pt.completed_at IS NOT NULL THEN 'zpracovano' 
                   ELSE 'zadano' 
               END AS state
        FROM publication p
        LEFT JOIN usedinreview uir ON p.publication_id = uir.publication_id AND uir.project_id = %s
        LEFT JOIN publicationtracking pt ON p.publication_id = pt.publication_id AND pt.project_id = %s
        WHERE p.publication_id = %s
    ''', (project_id, project_id, clanek_id))
    
    publication = cursor.fetchone()
    cursor.close()
    return publication


def sql_get_next_publication_id():
    """
    Získá další automatické ID pro tabulku Publikace.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = "publication"')
    result = cursor.fetchone()
    cursor.close()
    return result['AUTO_INCREMENT']

def sql_get_pdf_filename(clanek_id):
    """
    Získá název PDF souboru z tabulky Publikace podle ID článku a projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT pdf_name FROM publication WHERE publication_id = %s', (clanek_id, ))
    pdf_filename = cursor.fetchone()
    cursor.close()
    return pdf_filename['pdf_name'] if pdf_filename else None


def sql_delete_publication(clanek_id, project_id):
    """
    Smazani prirazeni clanku do projektu. Smaže záznamy z tabulky publicationtracking, publicationproject a usedinreview.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Smazání trackování článku
    cursor.execute('DELETE FROM publicationtracking WHERE publication_id = %s AND project_id = %s', (clanek_id, project_id))

    # Smazání přiřazení článku k projektům z tabulky publicationproject
    cursor.execute('DELETE FROM publicationproject WHERE publication_id = %s AND project_id = %s', (clanek_id, project_id))

    # Smazání vyzuziti clanku v projektu
    cursor.execute('DELETE FROM usedinreview WHERE publication_id = %s AND project_id = %s', (clanek_id, project_id))

    # Clanek uzivatel (autor nemuze smazat clanek z tabulky publication)


    # Zjištění, zda je článek přiřazen k jiným projektům
    #cursor.execute('SELECT COUNT(*) AS project_count FROM publicationproject WHERE publication_id = %s', (clanek_id,))
    #project_count = cursor.fetchone()['project_count']

    #if project_count == 0:
    #    # Pokud není přiřazen k žádnému jinému projektu, smaže článek z tabulky publication
    #    cursor.execute('DELETE FROM publication WHERE publication_id = %s', (clanek_id,))

    conn.commit()
    cursor.close()


def sql_delete_publication_from_system(clanek_id, project_id):
    """
    Kompletni smazani clanku z databaze. Smaže záznamy z tabulky publicationtracking, publicationproject, usedinreview a publication.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Smazání trackování článku
    cursor.execute('DELETE FROM publicationtracking WHERE publication_id = %s', (clanek_id, ))

    # Smazání přiřazení článku k projektům z tabulky publicationproject
    cursor.execute('DELETE FROM publicationproject WHERE publication_id = %s', (clanek_id, ))

    # Smazání vyzuziti clanku v projektu
    cursor.execute('DELETE FROM usedinreview WHERE publication_id = %s', (clanek_id, ))

    # Clanek uzivatel (autor nemuze smazat clanek z tabulky publication)
    cursor.execute('DELETE FROM publication WHERE publication_id = %s', (clanek_id,))

    conn.commit()
    cursor.close()

def sql_exist_publication(publication_id):
    """
    Zkontroluje, zda publikace s daným ID existuje v tabulce publication.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT COUNT(*) AS count FROM publication WHERE publication_id = %s', (publication_id,))
    result = cursor.fetchone()['count']
    cursor.close()
    return result > 0  # Vrátí True, pokud publikace existuje, jinak False


def sql_check_publication_name_exists(nazev_clanku):
    """
    Zkontroluje, zda existuje článek s daným názvem.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS count FROM publication WHERE publication_name = %s", (nazev_clanku,))
    result = cursor.fetchone()
    cursor.close()
    return result['count'] > 0  # Vrátí True, pokud existuje

def sql_check_publication_name_exist_in_project(nazev_clanku, projekt_id):

    """
    Zkontroluje, zda je článek přiřazen do projektu pomocí tabulky publicationproject.
    Vrací True, pokud článek již je přiřazen do projektu, jinak False.
    """
    conn = get_db_connection()  # Předpokládám, že tato funkce vrací spojení s databází
    cursor = conn.cursor(dictionary=True)

    query = '''
        SELECT COUNT(*) as count
        FROM publication p
        JOIN publicationproject pp ON p.publication_id = pp.publication_id
        WHERE p.publication_name = %s AND pp.project_id = %s
    '''

    cursor.execute(query, (nazev_clanku, projekt_id))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    # Pokud je nalezen alespoň jeden záznam, článek je již přiřazen
    return result['count'] > 0

def sql_insert_publication(projekt_id, nazev_clanku, abstract, casopis, rok_vydani, typ_senzoru,
                           princip_senzoru, konstrukce_senzoru, typ_optickeho_vlakna, zpusob_zapouzdreni, zpusob_implementace,
                           kategorie, podkategorie, merena_velicina, rozsah_merani, citlivost,
                           presnost, frekvencni_rozsah, vyhody, nevyhody, aplikace_studie,
                           klicove_poznatky, summary, poznamky, pdf_filename, obrazky, autori, doi, citaceBib, scopus_state, pub_type, rating):
    """
    Vloží novou publikaci do databáze.
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        INSERT INTO publication (
            publication_name, abstract, journal, year_publication, sensor_type, 
            sensor_principle, construction_principle, optical_fiber, encapsulation, implementation, 
            category, subcategory, measured_value, measuring_range, sensitivity, 
            accuracy, frequency_range, advantages, disadvantages, application, 
            key_knowledge, summary, note, pdf_name, figure, authors, doi, citation, scopus, pub_type, rating
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        nazev_clanku, abstract, casopis, rok_vydani, typ_senzoru,
        princip_senzoru, konstrukce_senzoru, typ_optickeho_vlakna, zpusob_zapouzdreni, zpusob_implementace,
        kategorie, podkategorie, merena_velicina, rozsah_merani, citlivost,
        presnost, frekvencni_rozsah, vyhody, nevyhody, aplikace_studie,
        klicove_poznatky, summary, poznamky, pdf_filename, obrazky, autori, doi, citaceBib, scopus_state, pub_type, rating
    ))
    publication_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    return publication_id

def sql_insert_publication_to_project(publication_id, selected_project):
    """
    Priradi clanek do projektu
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        INSERT INTO publicationproject (publication_id, project_id)
        VALUES (%s, %s)
    ''', (publication_id, selected_project))
    conn.commit()
    cursor.close()

def sql_insert_publication_tracking(publication_id, project_id, user_id_added):
    """
    Vloží nový záznam o publikaci do publicationtracking a zároveň nastaví uživatele a čas poslední změny.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO publicationtracking (publication_id, project_id, user_id_added, added_at, user_id_last_modified, last_modified_at)
        VALUES (%s, %s, %s, NOW(), %s, NOW())
    ''', (publication_id, project_id, user_id_added, user_id_added))
    conn.commit()
    cursor.close()


def sql_update_publication_tracking(publication_id, project_id, user_id_last_modified):
    """
    Aktualizuje záznam o publikaci a nastaví čas poslední změny a uživatele.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE publicationtracking
        SET user_id_last_modified = %s, last_modified_at = NOW()
        WHERE publication_id = %s AND project_id = %s
    ''', (user_id_last_modified, publication_id, project_id))
    conn.commit()
    cursor.close()

def sql_complete_publication_tracking(publication_id, project_id, user_id_completed, stav):
    """
    Nastaví nebo zruší stav zpracováno pro článek v tabulce publicationtracking.
    Pokud je předán user_id_completed, nastaví se dokončení, jinak se stav zpracováno zruší.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if stav == 'zpracováno':
        # Nastavení dokončení
        cursor.execute('''
            UPDATE publicationtracking 
            SET user_id_completed = %s, completed_at = NOW()
            WHERE publication_id = %s AND project_id = %s
        ''', (user_id_completed, publication_id, project_id))
    else:
        # Zrušení stavu zpracováno
        cursor.execute('''
            UPDATE publicationtracking 
            SET user_id_completed = NULL, completed_at = NULL
            WHERE publication_id = %s AND project_id = %s
        ''', (publication_id, project_id))

    conn.commit()
    cursor.close()


# TODO opraveno
def sql_get_current_status(clanek_id, project_id):
    """
    Získá aktuální stav článku pro zvolený projekt podle jeho ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT used_in_review FROM usedinreview WHERE publication_id = %s AND project_id = %s', (clanek_id, project_id))
    result = cursor.fetchone()
    cursor.close()
    return result['used_in_review'] if result else None

def sql_get_filtered_publications(project_id, search_terms, search_option, filters, sort):
    """
    Načte publikace podle projektu, vyhledávacího dotazu a filtrů.
    """
    query = '''
        SELECT DISTINCT p.*, ur.used_in_review
        FROM publication p
        JOIN publicationproject pp ON p.publication_id = pp.publication_id
        LEFT JOIN usedinreview ur ON p.publication_id = ur.publication_id AND ur.project_id = pp.project_id
        WHERE pp.project_id = %s
    '''

    query = '''
        SELECT
            p.*,
            ur.used_in_review,
            CASE WHEN EXISTS (
                SELECT 1
                FROM publicationtracking pt
                WHERE pt.project_id = pp.project_id
                    AND pt.publication_id = p.publication_id
                    AND pt.completed_at IS NOT NULL
            ) THEN 1 ELSE 0 END AS state
            FROM publication p
            JOIN publicationproject pp
                ON p.publication_id = pp.publication_id
            LEFT JOIN usedinreview ur
                ON ur.publication_id = p.publication_id
                AND ur.project_id = pp.project_id
        WHERE pp.project_id = %s
    '''

    query_filters = [project_id]

    if search_terms:
        if search_option == 'all':
            query += ' AND (' + ' AND '.join(['(p.publication_name LIKE %s OR p.journal LIKE %s OR p.year_publication LIKE %s OR p.sensor_type LIKE %s OR p.sensor_principle LIKE %s OR p.encapsulation LIKE %s OR p.implementation LIKE %s OR p.category LIKE %s OR p.subcategory LIKE %s OR p.note LIKE %s OR p.key_knowledge LIKE %s OR p.applications LIKE %s OR p.doi LIKE %s OR p.authors LIKE %s)'] * len(search_terms)) + ')'
            query_filters.extend(['%' + term + '%' for term in search_terms for _ in range(14)])
        else:
            query += ' AND (' + ' OR '.join(['(p.publication_name LIKE %s OR p.journal LIKE %s OR p.year_publication LIKE %s OR p.sensor_type LIKE %s OR p.sensor_principle LIKE %s OR p.encapsulation LIKE %s OR p.implementation LIKE %s OR p.category LIKE %s OR p.subcategory LIKE %s OR p.note LIKE %s OR p.key_knowledge LIKE %s OR p.application LIKE %s OR p.doi LIKE %s  OR p.authors LIKE %s)'] * len(search_terms)) + ')'
            query_filters.extend(['%' + term + '%' for term in search_terms for _ in range(14)])

    # Přidání filtrů
    if filters.get('filter_Casopis'):
        query += ' AND p.journal = %s'
        query_filters.append(filters['filter_Casopis'])

    if filters.get('filter_Pubtype'):
        query += ' AND p.pub_type = %s'
        query_filters.append(filters['filter_Pubtype'])

    if filters.get('filter_RokVydani'):
        query += ' AND p.year_publication = %s'
        query_filters.append(filters['filter_RokVydani'])

    if filters.get('filter_TypSenzoru'):
        query += ' AND p.sensor_type LIKE %s'
        query_filters.append('%' + filters['filter_TypSenzoru'] + '%')
    
    if filters.get('filter_PrincipSenzoru'):
        query += ' AND p.sensor_principle = %s'
        query_filters.append(filters['filter_PrincipSenzoru'])

    if filters.get('filter_Velicina'):
        query += ' AND p.measured_value LIKE %s'
        query_filters.append('%' + filters['filter_Velicina'] + '%')
    
    if filters.get('filter_ZpusobZapouzdreni'):
        query += ' AND p.encapsulation = %s'
        query_filters.append(filters['filter_ZpusobZapouzdreni'])

    if filters.get('filter_ZpusobImplementace'):
        query += ' AND p.implementation = %s'
        query_filters.append(filters['filter_ZpusobImplementace'])
    
    if filters.get('filter_Kategorie'):
        query += ' AND p.category = %s'
        query_filters.append(filters['filter_Kategorie'])
    
    if filters.get('filter_Podkategorie'):
        query += ' AND p.subcategory = %s'
        query_filters.append(filters['filter_Podkategorie'])

    # Filtrování na základě stavu `usedinreview`
    if filters.get('filter_UsedInReview') == 'ANO':
        query += ' AND ur.used_in_review = %s'
        query_filters.append('ANO')
    elif filters.get('filter_UsedInReview') == 'NE':
        query += ' AND (ur.used_in_review IS NULL OR ur.used_in_review = %s)'
        query_filters.append('NE')
    
    # Přidání řazení
    if sort.get('sort_column_name') and sort.get('sort_order'):
        query += f" ORDER BY {sort['sort_column_name']} {sort['sort_order']}"
    else:
        # defaultni razeni od nejnovejsiho
        query += f" ORDER BY p.publication_id DESC"

    # Vykonání dotazu
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, query_filters)
    publications = cursor.fetchall()
    cursor.close()

    if publications is None:
        publications = []
    elif not isinstance(publications, list):
        publications = list(publications)

    # Nahrazení odřádkování (\n) v `key_knowledge` za <hr>
    for publication in publications:        
        publication['key_knowledge'] = publication['key_knowledge'].replace('\n', '<br>')
        publication['summary'] = publication['summary'].replace('\n', '<br>')
        publication['application'] = publication['application'].replace('\n', '<br>')
        publication['note'] = publication['note'].replace('\n', '<br>')
        publication['construction_principle'] = publication['construction_principle'].replace('\n', '<br>')
        publication['figure'] = publication['figure'].replace('\n', '<br>')

    return publications


def sql_get_all_publications(search_terms, search_option, filters, selected_project, sort):
    """
    Načte všechny publikace v databázi s vyhledávacím dotazem a filtry.
    Vždy vrací list (může být prázdný).
    """
    query = '''
        SELECT p.*, ur.used_in_review
        FROM publication p
        LEFT JOIN publicationproject pp ON p.publication_id = pp.publication_id
        LEFT JOIN usedinreview ur       ON p.publication_id = ur.publication_id
        WHERE 1=1
    '''
    query_filters = []

    # Vyhledávání
    if search_terms:
        cols = (
            "p.publication_name", "p.journal", "p.year_publication",
            "p.sensor_type", "p.sensor_principle", "p.encapsulation",
            "p.implementation", "p.category", "p.subcategory",
            "p.note", "p.key_knowledge", "p.applications",  # sjednoceno na 'applications'
            "p.doi", "p.authors"
        )
        # počet sloupců pro násobení placeholderů
        N = len(cols)

        if search_option == 'all':
            # all = každý termín musí být nalezen (AND)
            query += ' AND (' + ' AND '.join(
                ['(' + ' OR '.join([f"{c} LIKE %s" for c in cols]) + ')' for _ in search_terms]
            ) + ')'
            for term in search_terms:
                query_filters.extend(['%' + term + '%'] * N)
        else:
            # any = alespoň jeden termín (OR)
            query += ' AND (' + ' OR '.join(
                ['(' + ' OR '.join([f"{c} LIKE %s" for c in cols]) + ')' for _ in search_terms]
            ) + ')'
            for term in search_terms:
                query_filters.extend(['%' + term + '%'] * N)

    # Filtry
    if filters.get('filter_Casopis'):
        query += ' AND p.journal = %s'
        query_filters.append(filters['filter_Casopis'])

    if filters.get('filter_RokVydani'):
        query += ' AND p.year_publication = %s'
        query_filters.append(filters['filter_RokVydani'])

    if filters.get('filter_TypSenzoru'):
        query += ' AND p.sensor_type LIKE %s'
        query_filters.append('%' + filters['filter_TypSenzoru'] + '%')

    if filters.get('filter_PrincipSenzoru'):
        query += ' AND p.sensor_principle = %s'
        query_filters.append(filters['filter_PrincipSenzoru'])

    if filters.get('filter_Velicina'):
        query += ' AND p.measured_value LIKE %s'
        query_filters.append('%' + filters['filter_Velicina'] + '%')

    if filters.get('filter_ZpusobZapouzdreni'):
        query += ' AND p.encapsulation = %s'
        query_filters.append(filters['filter_ZpusobZapouzdreni'])

    if filters.get('filter_ZpusobImplementace'):
        query += ' AND p.implementation = %s'
        query_filters.append(filters['filter_ZpusobImplementace'])

    if filters.get('filter_Kategorie'):
        query += ' AND p.category = %s'
        query_filters.append(filters['filter_Kategorie'])

    if filters.get('filter_Podkategorie'):
        query += ' AND p.subcategory = %s'
        query_filters.append(filters['filter_Podkategorie'])

    # Použití v review
    if filters.get('filter_UsedInReview'):
        query += ' AND ur.used_in_review = %s'
        query_filters.append(filters['filter_UsedInReview'])

    # Přiřazení k projektu
    if filters.get('filter_UsedInProject') == 'ANO':
        query += ' AND pp.project_id = %s'
        query_filters.append(selected_project)
    elif filters.get('filter_UsedInProject') == 'NE':
        query += '''
            AND p.publication_id NOT IN (
                SELECT publication_id
                FROM publicationproject
                WHERE project_id = %s
            )
        '''
        query_filters.append(selected_project)

    # GROUP BY a ORDER BY
    query += " GROUP BY p.publication_id"

    if sort and sort.get('sort_column_name') and sort.get('sort_order'):
        query += f" ORDER BY {sort['sort_column_name']} {sort['sort_order']}"
    else:
        query += " ORDER BY p.publication_id DESC"

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(query, query_filters)
        publications = cursor.fetchall() or []   # nikdy None
        return publications

    except Exception as e:
        # Zaloguju a vrátím prázdný list
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def sql_get_all_publications2(search_terms, search_option, filters, selected_project, sort):
    """
    Načte všechny publikace v databázi s vyhledávacím dotazem a filtry.
    """
    query = '''
        SELECT p.*, ur.used_in_review
        FROM publication p
        LEFT JOIN publicationproject pp ON p.publication_id = pp.publication_id
        LEFT JOIN usedinreview ur ON p.publication_id = ur.publication_id
        WHERE 1=1
        
    '''
    #        GROUP BY p.publication_id
    
    query_filters = []
        
    # Vyhledávání podle klíčových slov
    if search_terms:
        if search_option == 'all':
            query += ' AND (' + ' AND '.join(['(p.publication_name LIKE %s OR p.journal LIKE %s OR p.year_publication LIKE %s OR p.sensor_type LIKE %s OR p.sensor_principle LIKE %s OR p.encapsulation LIKE %s OR p.implementation LIKE %s OR p.category LIKE %s OR p.subcategory LIKE %s OR p.note LIKE %s OR p.key_knowledge LIKE %s OR p.applications LIKE %s OR p.doi LIKE %s OR p.authors LIKE %s)'] * len(search_terms)) + ')'
            query_filters.extend(['%' + term + '%' for term in search_terms for _ in range(14)])
        else:
            query += ' AND (' + ' OR '.join(['(p.publication_name LIKE %s OR p.journal LIKE %s OR p.year_publication LIKE %s OR p.sensor_type LIKE %s OR p.sensor_principle LIKE %s OR p.encapsulation LIKE %s OR p.implementation LIKE %s OR p.category LIKE %s OR p.subcategory LIKE %s OR p.note LIKE %s OR p.key_knowledge LIKE %s OR p.application LIKE %s OR p.doi LIKE %s  OR p.authors LIKE %s)'] * len(search_terms)) + ')'
            query_filters.extend(['%' + term + '%' for term in search_terms for _ in range(14)])

    # Přidání filtrů
    # Přidání filtrů
    if filters.get('filter_Casopis'):
        query += ' AND p.journal = %s'
        query_filters.append(filters['filter_Casopis'])
    
    if filters.get('filter_RokVydani'):
        query += ' AND p.year_publication = %s'
        query_filters.append(filters['filter_RokVydani'])

    if filters.get('filter_TypSenzoru'):
        query += ' AND p.sensor_type LIKE %s'
        query_filters.append('%' + filters['filter_TypSenzoru'] + '%')
    
    if filters.get('filter_PrincipSenzoru'):
        query += ' AND p.sensor_principle = %s'
        query_filters.append(filters['filter_PrincipSenzoru'])

    if filters.get('filter_Velicina'):
        query += ' AND p.measured_value LIKE %s'
        query_filters.append('%' + filters['filter_Velicina'] + '%')
    
    if filters.get('filter_ZpusobZapouzdreni'):
        query += ' AND p.encapsulation = %s'
        query_filters.append(filters['filter_ZpusobZapouzdreni'])

    if filters.get('filter_ZpusobImplementace'):
        query += ' AND p.implementation = %s'
        query_filters.append(filters['filter_ZpusobImplementace'])
    
    if filters.get('filter_Kategorie'):
        query += ' AND p.category = %s'
        query_filters.append(filters['filter_Kategorie'])
    
    if filters.get('filter_Podkategorie'):
        query += ' AND p.subcategory = %s'
        query_filters.append(filters['filter_Podkategorie'])

    # Filtrování na základě stavu `usedinreview`
    if filters.get('filter_UsedInReview'):
        query += ' AND ur.used_in_review = %s'
        query_filters.append(filters['filter_UsedInReview'])

    # Filtrování podle toho, zda je článek přiřazen k projektu
    # Filtrování podle toho, zda je článek přiřazen k projektu
    if filters.get('filter_UsedInProject') == 'ANO':
        query += ' AND pp.project_id = %s'
        query_filters.append(selected_project)
    elif filters.get('filter_UsedInProject') == 'NE':
        query += '''
        AND p.publication_id NOT IN (
            SELECT publication_id
            FROM publicationproject
            WHERE project_id = %s
        )
        '''
        query_filters.append(selected_project)

    query += "GROUP BY p.publication_id"
    
    # Přidání řazení
    if sort.get('sort_column_name') and sort.get('sort_order'):
        query += f" ORDER BY {sort['sort_column_name']} {sort['sort_order']}"
    else:
        # defaultni razeni od nejnovejsiho
        query += f" ORDER BY publication_id DESC"

    print(query)
    # Vykonání dotazu
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, query_filters)
    publications = cursor.fetchall()
    cursor.close()

def sql_get_all_publications_without_filters():
    """
    Načte všechny publikace z databáze.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT publication_id, publication_name 
        FROM publication
        WHERE scopus = 0
    ''')

    publications = cursor.fetchall()
    cursor.close()
    return publications


def sql_get_unique_values(project_id, column_name):
    """
    Načte unikátní hodnoty pro daný sloupec v tabulce Publikace.
    Pokud se jedná o sloupec s hodnotami oddělenými středníkem, provede rozdělení a odstranění duplikátů.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if project_id is not None:
        query = f'''
            SELECT DISTINCT {column_name} 
            FROM publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
            WHERE pp.project_id = %s
        '''
        cursor.execute(query, (project_id,))
    else:
        query = f'''
            SELECT DISTINCT {column_name} 
            FROM publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
        '''
        cursor.execute(query)
    
    values_raw = cursor.fetchall()
    unique_values_set = set()
    
    # Sloupce, které vyžadují rozdělení hodnot se středníkem
    split_columns = ['measured_value', 'sensor_type']  # Přidat další sloupce, pokud je třeba
    
    if column_name in split_columns:
        # Rozdělení hodnot oddělených středníkem a odstranění duplikátů
        for row in values_raw:
            if row[column_name]:
                column_data = row[column_name].split(';')  # Rozdělit hodnoty podle středníku
                for value in column_data:
                    unique_values_set.add(value.strip())  # Ořezat mezery a přidat do setu
    else:
        # Pokud není potřeba rozdělit hodnoty, přidá se je přímo
        for row in values_raw:
            if row[column_name]:
                unique_values_set.add(row[column_name])
    
    # Vrácení ve formátu [{'column_name': 'value'}, ...]
    unique_values = [{column_name: value} for value in sorted(list(unique_values_set))]
    
    cursor.close()
    return unique_values




def sql_get_unique_values_backup(project_id, column_name):
    """
    Načte unikátní hodnoty pro daný sloupec v tabulce Publikace.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if(project_id is not None):
        query = f'''
            SELECT DISTINCT {column_name} 
            FROM publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
            WHERE pp.project_id = %s
        '''
        cursor.execute(query, (project_id,))
    else:
        query = f'''
            SELECT DISTINCT {column_name} 
            FROM publication p
            JOIN publicationproject pp ON p.publication_id = pp.publication_id
        '''
        cursor.execute(query)
    
    values = cursor.fetchall()
    cursor.close()
    return values

def sql_update_publication(clanek_id, nazev_clanku, abstract, casopis, rok_vydani, typ_senzoru, princip_senzoru, konstrukce_senzoru,
                           typ_optickeho_vlakna, zpusob_zapouzdreni, zpusob_implementace, kategorie,
                           podkategorie, merena_velicina, rozsah_merani, citlivost, presnost,
                           frekvencni_rozsah, vyhody, nevyhody, aplikace_studie, klicove_poznatky, summary, 
                           poznamky, obrazky, autori, doi, citaceBib, stav, projekt_id, pdf_name_new, pub_type, rating):
    """
    Aktualizuje publikaci v databázi.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        UPDATE publication
        SET publication_name = %s, abstract = %s, journal = %s, year_publication = %s, sensor_type = %s,
            sensor_principle = %s, construction_principle = %s, optical_fiber = %s, encapsulation = %s,
            implementation = %s, category = %s, subcategory = %s, measured_value = %s,
            measuring_range = %s, sensitivity = %s, accuracy = %s, frequency_range = %s, advantages = %s,
            disadvantages = %s, application = %s, key_knowledge = %s, summary = %s, note = %s, figure = %s, authors = %s, 
            doi = %s, citation = %s, pdf_name = %s, pub_type = %s, rating = %s
        WHERE publication_id = %s
    ''', (nazev_clanku, abstract, casopis, rok_vydani, typ_senzoru, princip_senzoru, konstrukce_senzoru, 
          typ_optickeho_vlakna, zpusob_zapouzdreni, zpusob_implementace, 
          kategorie, podkategorie, merena_velicina, rozsah_merani, 
          citlivost, presnost, frekvencni_rozsah, vyhody, nevyhody, 
          aplikace_studie, klicove_poznatky, summary, poznamky, obrazky, autori, doi, citaceBib,
          pdf_name_new, pub_type, rating, clanek_id))
    conn.commit()
    cursor.close()

def sql_update_publication_rating(article_id, rating):
    """
    Aktualizuje hodnocení publikace v databázi.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        UPDATE publication
        SET rating = %s
        WHERE publication_id = %s
    ''', (rating, article_id))
    conn.commit()
    cursor.close()




def sql_get_number_of_publications_in_system():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
            SELECT COUNT(publication_id) as pocetClankuCelkem
            FROM publication

        ''')
    result = cursor.fetchone()
    cursor.close()
    return result

def sql_get_number_of_publications_in_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
            SELECT COUNT(publication_id) as pocetClankuCelkem
            FROM publicationproject
            WHERE project_id = %s
        ''', (project_id, ))
    result = cursor.fetchone()
    cursor.close()
    return result

# nove
def sql_publication_update_UsedInReview(article_id, project_id, used_in_review):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    #cursor.execute('''
    #        INSERT INTO usedinreview (publication_id, project_id, used_in_review) 
    #        VALUES (%s, %s, %s)
    #    ''', (article_id, project_id, used_in_review))
        
    if(used_in_review == "ANO"):
        cursor.execute('''
            INSERT INTO usedinreview (publication_id, project_id, used_in_review) 
            VALUES (%s, %s, %s)
        ''', (article_id, project_id, used_in_review))
    elif(used_in_review == "NE"):
        cursor.execute('''
            DELETE FROM usedinreview 
            WHERE publication_id = %s AND project_id = %s
        ''', (article_id, project_id))

    conn.commit()
    cursor.close()

def sql_check_publication_in_review(article_id, project_id, useed_in_review):
    '''
    Kontrola, zda clanek je jiz v review pouzit.     
    '''
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT COUNT(*) AS count FROM usedinreview
        WHERE publication_id = %s AND project_id = %s AND used_in_review = %s
    ''', (article_id, project_id, useed_in_review))        
    result = cursor.fetchone()
    cursor.close()

    if result['count'] > 0:
        return True
    else:
        return False

def sql_update_publications_scopus_data(publication_id, title, authors, journal_or_conference, year, doi, bibtex_citation):
    """
    Aktualizuje článek v databázi pomocí dat ze Scopus API.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
        UPDATE publication
        SET 
            publication_name = %s,
            authors = %s,
            journal = %s,
            year_publication = %s,
            doi = %s,
            citation = %s,
            scopus = %s
        WHERE publication_id = %s
    ''', (title, authors, journal_or_conference, year, doi, bibtex_citation, 1, publication_id)) 
    
    conn.commit()
    cursor.close()



# ***********************************************************************************************************************
#      PROJECT
# ***********************************************************************************************************************
def sql_get_projects():
    """
    Získá všechny projekty z databáze (pouze pro administrátory).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM project')
    projects = cursor.fetchall()
    cursor.close()
    return projects

def sql_get_projects_by_user(user_id):
    """
    Získá projekty, které jsou přiřazeny konkrétnímu uživateli.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT p.* FROM project p JOIN userproject up ON p.project_id = up.project_id WHERE up.user_id = %s', (user_id,))
    projects = cursor.fetchall()
    cursor.close()
    return projects


def sql_get_project(project_id):
    """
    Získá projekty, které jsou přiřazeny konkrétnímu uživateli.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM project WHERE project_id = %s', (project_id,))
    project = cursor.fetchone()
    cursor.close()

    return project

def sql_get_project_name(project_id):
    """
    Získá projekty, které jsou přiřazeny konkrétnímu uživateli.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT project_name FROM project WHERE project_id = %s', (project_id,))
    project = cursor.fetchone()
    project_name = project['project_name']
    cursor.close()
    
    # Vracíme pouze název projektu, pokud byl nalezen
    return project_name

def sql_insert_project_into_db(form_data):
    """
    Funkce pro vložení projektu do databáze.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('INSERT INTO project (project_name, project_description, project_structure) VALUES (%s, %s, %s)', (form_data['project_name'], form_data['project_description'], form_data['project_structure']))
    conn.commit()
    cursor.close() 

def sql_update_project(project_id, form_data):
    """
    Aktualizuje projekt v databázi.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('UPDATE project SET project_name = %s, project_description = %s, project_structure = %s WHERE project_id = %s', (form_data['project_name'], form_data['project_description'], form_data['project_structure'], project_id))
    conn.commit()
    cursor.close()
    

def sql_delete_users_from_project(project_id):
    """
    Vymaže všechny uživatele přiřazené k projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('DELETE FROM userproject WHERE project_id = %s', (project_id,))
    conn.commit()
    cursor.close()

def sql_insert_user_into_project(project_id, user_id):
    """
    Přiřadí uživatele k projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('INSERT INTO userproject (user_id, project_id) VALUES (%s, %s)', (user_id, project_id))
    conn.commit()
    cursor.close()


def sql_get_users_in_project(project_id):
    """
    Získá ID uživatelů přiřazených k projektu.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT user_id FROM userproject WHERE project_id = %s', (project_id,))
    assigned_users = {row['user_id'] for row in cursor.fetchall()}
    cursor.close()
    return assigned_users




def sql_delete_project(project_id):
    """
    Vymaže projekt z databáze podle jeho ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('DELETE FROM project WHERE project_id = %s', (project_id,))
    conn.commit()
    cursor.close()



# ***********************************************************************************************************************
#      USER
# ***********************************************************************************************************************
def sql_insert_user_into_db(form_data, heslo_HASH):
    """
    Funkce pro vložení uživatele do databáze.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('INSERT INTO user (name, surname, login, password, role) VALUES (%s, %s, %s, %s, %s)', 
                   (form_data['jmeno'], form_data['prijmeni'], form_data['login'], heslo_HASH, form_data['role']))
    conn.commit()
    cursor.close()

def sql_get_user_password(user_id):
    """
    Získá hash hesla uživatele z databáze podle user_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT password FROM user WHERE user_id = %s', (user_id,))
    password_in_db = cursor.fetchone()['password']
    cursor.close()
    return password_in_db

def sql_update_user_password(user_id, new_password_hash):
    """
    Aktualizuje heslo uživatele v databázi podle user_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('UPDATE user SET password = %s WHERE user_id = %s', (new_password_hash, user_id))
    conn.commit()
    rowcount = cursor.rowcount
    cursor.close()
    return rowcount

def sql_get_user_by_id(user_id):
    """
    Získá informace o uživateli podle user_id z databáze.
    Vrací jeden řádek se slovníkem obsahujícím informace o uživateli.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT user_id, name, surname, login, role FROM user WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user

def sql_get_users():
    """
    Získá seznam uzivatelu v databáze.
    Vrací nekolik řádeků se slovníkem obsahujícím informace všech uživatelích.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT user_id, name, surname, login, role FROM user')
    user = cursor.fetchall()
    cursor.close()
    return user

def sql_update_user(user_id, form_data):
    """
    Aktualizuje informace o uživateli v databázi.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('UPDATE user SET name = %s, surname = %s, login = %s, role = %s WHERE user_id = %s',
                   (form_data['jmeno'], form_data['prijmeni'], form_data['login'], form_data['role'], user_id))
    conn.commit()
    rowcount = cursor.rowcount
    cursor.close()
    return rowcount


