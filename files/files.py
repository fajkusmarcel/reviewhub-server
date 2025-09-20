import pdfplumber
import os

def delete_file(file_path):  
    print("Delete file 1")  
    try:
        if os.path.exists(file_path):
            print("Delete file 1")
            print(file_path)
            os.remove(file_path)
            print(f'Soubor {file_path} byl úspěšně smazán.')
        else:
            print(f'Soubor {file_path} neexistuje, žádná akce nebyla provedena.')
    except Exception as e:
        print(f'Došlo k chybě při odstraňování souboru: {e}')


def rename_file(file_path_old, file_path_new):
    try:
        if os.path.exists(file_path_old):
            os.rename(file_path_old, file_path_new)
            print(f'Soubor {file_path_old} byl úspěšně přejmennován na {file_path_new}')
        else:
            print(f'Soubor {file_path_old} se nepodarilo najit')
    except Exception as e:
        print(f'Došlo k chybě při přejmenování souoru souboru: {e}')

def save_file(file, project_dir, file_name):
    print("save file 1")
    if file and file.filename:
        print("save file 2")
        # Vytvoření adresáře, pokud neexistuje
        os.makedirs(project_dir, exist_ok=True)

        # Cesta k souboru
        file_path = os.path.join(project_dir, file_name)
        print(file_path)
        # Uložení souboru
        file.save(file_path)
        print(f'Soubor {file_path} byl úspěšně uložen.')

    else:
        print("Žádný soubor nebyl vybrán.")

def pdf2text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

