import requests


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
                print("\n")
                print("     Clanek >", title.lower(), "<")
                print("     Clanek >", article_title.lower(), "<")
                if title.lower() == article_title.lower():
                    
                    # Extrakce autorů - kontrola existence křestního jména a příjmení
                    authors_list = []
                    print(article_data.get('author', []))
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
                    print(journal_or_conference)
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

                    print("-- ", type_publication)
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


# Příklad použití
# "Optical sensor networks for high-speed railway applications (Invited Paper)" pridat invited
# "Design of Fiber Bragg Grating Ultrasonic Sensor with Dual-Slant Cone Structure"  nevim
# "Fiber Bragg Grating Accelerometer and Its Application to Measure Wheel‐Rail Excitation" ykopirovat takto, chyba v pomlcce
# "FEM Analysis of Railway Brake Disc for Safety of Train"          nenajde
# "Field trials of optical fiber sensors for train tracking and wheel flat detection"
article_title = "FEM Analysis of Railway Brake Disc for Safety of Train"
                 
info = get_article_info_from_SCOPUS(article_title, 1)

print("\n", info)
if 'error' in info:
    print(info['error'])
else:
    print(info['bibtex_citation'])
