# Standardní knihovny Pythonu
import os
from werkzeug.utils import secure_filename  # Zajištění bezpečných názvů souborů
from functools import wraps
import json

# Knihovny třetích stran (nainstalované přes pip)
from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from flask_mysqldb import MySQL

# Vlastní moduly (část tvé aplikace)
import config  # Konfigurace aplikace
from utils.utils import *
from utils.decorators import *
from db.sql_query import *

# Definice blueprintu pro uživatele
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
@project_required
def dashboard():
    """
    Statisticka data pro dasboard
    """        
    # ID vybraného projektu
    selected_project = session['selected_project']
    print("DASHBOARD check, session keys:", list(session.keys()))
    print("Cookie PATH effective:", current_app.config.get("SESSION_COOKIE_PATH"))

    # Načtení statistik
    total_articles = sql_get_total_articles_by_project(selected_project)
    total_entered = sql_get_total_articles_by_status(selected_project, "zavedeno") or 0
    total_processed = sql_get_total_articles_by_status(selected_project, "zpracovano") or 0
    
    articles_in_review = sql_get_articles_in_review(selected_project)
    articles_by_year_in_review = sql_get_articles_grouped_by_year_in_review(selected_project)
    articles_by_category_in_review = sql_get_articles_grouped_by_category_in_review(selected_project)
    articles_by_subcategory_in_review = sql_get_articles_grouped_by_subcategory_in_review(selected_project)
    articles_by_sensor_type_in_review = sql_get_articles_grouped_by_sensor_type_in_review(selected_project)

    articles_by_year = sql_get_articles_grouped_by_year(selected_project)
    articles_by_category = sql_get_articles_grouped_by_category(selected_project)
    articles_by_subcategory = sql_get_articles_grouped_by_subcategory(selected_project)
    articles_by_sensor_type = sql_get_articles_grouped_by_sensor_type(selected_project)
    processed_articles = sql_get_processed_articles_by_author(selected_project)
    non_processed_articles = sql_get_non_processed_articles_by_author(selected_project)

    processed_articles_by_day = sql_get_processed_articles_by_day(selected_project)


    # Statistika clanku v systemu
    stat_data = sql_statistics_for_project(selected_project)
    # Vytvoření slovníku 'stat' a zpracování JSON dat
    stat = {}
    stat['total_articles'] = stat_data['total_articles']
    stat['articles_with_pdf'] = stat_data['articles_with_pdf']
    stat['articles_by_year'] = json.loads(stat_data['articles_by_year']) if stat_data['articles_by_year'] else {}
    stat['articles_by_category'] = json.loads(stat_data['articles_by_category']) if stat_data['articles_by_category'] else {}
    stat['articles_by_subcategory'] = json.loads(stat_data['articles_by_subcategory']) if stat_data['articles_by_subcategory'] else {}
    stat['articles_by_sensor_type'] = json.loads(stat_data['articles_by_sensor_type']) if stat_data['articles_by_sensor_type'] else {}

    NazevProjektu = sql_get_project_name(selected_project)

    return render_template('dashboard.html',
                            NazevProjektu=NazevProjektu,
                            total_articles=total_articles,
                            total_entered=total_entered,
                            total_processed=total_processed,
                            articles_in_review=articles_in_review,
                            articles_by_year_in_review=articles_by_year_in_review,
                            articles_by_category_in_review=articles_by_category_in_review,
                            articles_by_subcategory_in_review=articles_by_subcategory_in_review,
                            articles_by_sensor_type_in_review=articles_by_sensor_type_in_review,
                            articles_by_year=articles_by_year,
                            articles_by_category=articles_by_category,
                            articles_by_subcategory=articles_by_subcategory,
                            articles_by_sensor_type=articles_by_sensor_type,
                            processed_articles=processed_articles,
                            non_processed_articles=non_processed_articles,
                            processed_articles_by_day=processed_articles_by_day,
                            stat=stat,                            
                            site_name="Dashboard")

