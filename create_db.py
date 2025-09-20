import mysql.connector
from utils.utils import *
import config

mode = 'test'   # test | production

    
if(mode == 'test'):
    print('Verze test')
    print(config.MYSQL_DB_test)
    # Připojení k MySQL serveru
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB_test
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS reviewhub")
    cursor.execute("USE reviewhub_test")    
elif(mode == 'production'):
    print('Verze production')
    print(config.MYSQL_DB)
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS reviewhub_test")
    cursor.execute("USE reviewhub")
else:
    print('Vyber verzi databaze: test nebo production')


# Vytvoření kurzoru




cursor.execute("DROP TABLE IF EXISTS PublicationTracking")
cursor.execute("DROP TABLE IF EXISTS PublicationProject")
cursor.execute("DROP TABLE IF EXISTS UsedInReview")
cursor.execute("DROP TABLE IF EXISTS UserProject")
cursor.execute("DROP TABLE IF EXISTS User")
cursor.execute("DROP TABLE IF EXISTS Project")
cursor.execute("DROP TABLE IF EXISTS Publication")

# Vytvoření tabulky Users
cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        surname VARCHAR(255) NOT NULL,
        login VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'autor') NOT NULL
    )
''')

# Vytvoření tabulky Projekt
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Project (
        project_id INT AUTO_INCREMENT PRIMARY KEY,
        project_name VARCHAR(255) NOT NULL,
        project_description TEXT,
        project_structure TEXT
    )
''')

# Vytvoření tabulky Publikace
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Publication (
        publication_id INT AUTO_INCREMENT PRIMARY KEY,
        publication_name VARCHAR(2000) NOT NULL,
        abstract TEXT,
        journal VARCHAR(255),
        year_publication YEAR,
        sensor_type VARCHAR(255),
        sensor_principle VARCHAR(255),
        construction_principle TEXT,
        optical_fiber VARCHAR(255),
        encapsulation VARCHAR(255),
        implementation VARCHAR(255),
        category VARCHAR(255),
        subcategory VARCHAR(255),
        measured_value VARCHAR(255),
        measuring_range VARCHAR(255),
        sensitivity VARCHAR(255),
        accuracy VARCHAR(255),
        frequency_range VARCHAR(255),
        advantages TEXT,
        disadvantages TEXT,
        application TEXT,
        key_knowledge TEXT,
        note TEXT,
        pdf_name VARCHAR(255),
        figure TEXT,
        authors VARCHAR(500),
        doi VARCHAR(500),
        citation TEXT,
        scopus INT
    )
''')

cursor.execute("ALTER TABLE Publication ADD FULLTEXT(publication_name)")

cursor.execute('''
    CREATE TABLE PublicationTracking (
        id INT AUTO_INCREMENT PRIMARY KEY,
        project_id INT NOT NULL,
        publication_id INT NOT NULL,
        user_id_added INT NOT NULL,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id_last_modified INT,
        last_modified_at DATETIME,
        user_id_completed INT,
        completed_at DATETIME,
        FOREIGN KEY (project_id) REFERENCES Project(project_id),
        FOREIGN KEY (publication_id) REFERENCES Publication(publication_id),
        FOREIGN KEY (user_id_added) REFERENCES User(user_id),
        FOREIGN KEY (user_id_last_modified) REFERENCES User(user_id),
        FOREIGN KEY (user_id_completed) REFERENCES User(user_id)
    )
''')

cursor.execute('''
    CREATE TABLE UserProject (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        project_id INT,
        FOREIGN KEY (user_id) REFERENCES User(user_id),
        FOREIGN KEY (project_id) REFERENCES Project(project_id)
    )
''')
cursor.execute('''CREATE TABLE PublicationProject (
    id INT AUTO_INCREMENT PRIMARY KEY,      
    publication_id INT NOT NULL,
    project_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (publication_id, project_id),
    FOREIGN KEY (publication_id) REFERENCES Publication(publication_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES Project(project_id) ON DELETE CASCADE
)
''')
cursor.execute('''
    CREATE TABLE UsedInReview (
    id INT AUTO_INCREMENT PRIMARY KEY,
    publication_id INT NOT NULL,
    project_id INT NOT NULL,
    used_in_review ENUM('ANO', 'NE') DEFAULT 'NE',
    FOREIGN KEY (publication_id) REFERENCES Publication(publication_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES Project(project_id) ON DELETE CASCADE
)
''')



# Pridani uzivatele
password = 'marcel'
password_hash = hash_password(password)        
cursor.execute('INSERT INTO User (name, surname, login, password, role) VALUES (%s, %s, %s, %s, %s)', 
                   ('Marcel', 'Fajkus', 'marcel', password_hash, 'admin'))

# Pridani testovaciho projektu
cursor.execute('INSERT INTO Project (project_name, project_description) VALUES (%s, %s)', ('default', ''))

# Prirazeni uzivatele do projektu
cursor.execute('INSERT INTO UserProject (user_id, project_id) VALUES (%s, %s)', (1, 1))

if(mode == 'test'):
    # uzivatele
    password = 'test'
    password_hash = hash_password(password)        
    cursor.execute('INSERT INTO User (name, surname, login, password, role) VALUES (%s, %s, %s, %s, %s)', 
                    ('test', 'autor', 'test', password_hash, 'autor'))
    password = 'test'
    password_hash = hash_password(password)        
    cursor.execute('INSERT INTO User (name, surname, login, password, role) VALUES (%s, %s, %s, %s, %s)', 
                    ('test', 'administrator', 'testAdmin', password_hash, 'admin'))
    
    # projekty
    cursor.execute('INSERT INTO Project (project_name, project_description) VALUES (%s, %s)', ('Projekt 1', ''))
    cursor.execute('INSERT INTO Project (project_name, project_description) VALUES (%s, %s)', ('Projekt 2', ''))
    cursor.execute('INSERT INTO Project (project_name, project_description) VALUES (%s, %s)', ('Projekt 3', ''))

    # clanky
    cursor.execute('''INSERT INTO `Publication` (`publication_id`, `publication_name`, `abstract`, `journal`, `year_publication`, 
                   `sensor_type`, `sensor_principle`, `construction_principle`, `optical_fiber`, 
                   `encapsulation`, `implementation`, `category`, `subcategory`, 
                   `measured_value`, `measuring_range`, `sensitivity`, `accuracy`, `frequency_range`, 
                   `advantages`, `disadvantages`, `application`, `key_knowledge`, `note`, `pdf_name`, `figure`, `authors`, `doi`, `citation`, `scopus`) 
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',    
                    (1, 'Clanek 1', '', '', 2021, 'FBG', '', '', '', '', '', 'Doprava', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''))

    cursor.execute('''INSERT INTO `Publication` (`publication_id`, `publication_name`, `abstract`, `journal`, `year_publication`, 
                   `sensor_type`, `sensor_principle`, `construction_principle`, `optical_fiber`, 
                   `encapsulation`, `implementation`, `category`, `subcategory`, 
                   `measured_value`, `measuring_range`, `sensitivity`, `accuracy`, `frequency_range`, 
                   `advantages`, `disadvantages`, `application`, `key_knowledge`, `note`, `pdf_name`, `figure`, `authors`, `doi`, `citation`, `scopus`) 
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (2, 'Clanek 1', '', '', 2021, 'FBG', '', '', '', '', '', 'Doprava', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''))
    
    cursor.execute('''INSERT INTO `Publication` (`publication_id`, `publication_name`, `abstract`, `journal`, `year_publication`, 
                   `sensor_type`, `sensor_principle`, `construction_principle`, `optical_fiber`, 
                   `encapsulation`, `implementation`, `category`, `subcategory`, 
                   `measured_value`, `measuring_range`, `sensitivity`, `accuracy`, `frequency_range`, 
                   `advantages`, `disadvantages`, `application`, `key_knowledge`, `note`, `pdf_name`, `figure`, `authors`, `doi`, `citation`, `scopus`) 
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (3, 'Clanek 3', '', '', 2022, 'FBG', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''))
    
    cursor.execute('''INSERT INTO `Publication` (`publication_id`, `publication_name`, `abstract`, `journal`, `year_publication`, 
                   `sensor_type`, `sensor_principle`, `construction_principle`, `optical_fiber`, 
                   `encapsulation`, `implementation`, `category`, `subcategory`, 
                   `measured_value`, `measuring_range`, `sensitivity`, `accuracy`, `frequency_range`, 
                   `advantages`, `disadvantages`, `application`, `key_knowledge`, `note`, `pdf_name`, `figure`, `authors`, `doi`, `citation`, `scopus`) 
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (4, 'Clanek 10', '', '', 2022, 'DTS', '', '', '', '', '', 'BIO', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''))
    
    cursor.execute('''INSERT INTO `Publication` (`publication_id`, `publication_name`, `abstract`, `journal`, `year_publication`, 
                   `sensor_type`, `sensor_principle`, `construction_principle`, `optical_fiber`, 
                   `encapsulation`, `implementation`, `category`, `subcategory`, 
                   `measured_value`, `measuring_range`, `sensitivity`, `accuracy`, `frequency_range`, 
                   `advantages`, `disadvantages`, `application`, `key_knowledge`, `note`, `pdf_name`, `figure`, `authors`, `doi`, `citation`, `scopus`) 
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (5, 'Clanek 11', '', '', 2023, 'DTS', '', '', '', '', '', 'Stavebnictvi', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''))
    
    # PublicationProject
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (1, 1, 1, '2024-09-30 19:02:38'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (2, 2, 1, '2024-09-30 19:02:55'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (3, 3, 1, '2024-09-30 19:03:27'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (4, 1, 2, '2024-09-30 19:09:22'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (5, 2, 2, '2024-09-30 19:09:24'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (6, 3, 2, '2024-09-30 19:25:46'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (7, 1, 3, '2024-09-30 19:34:23'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (8, 2, 3, '2024-09-30 19:34:25'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (9, 3, 3, '2024-09-30 19:34:28'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (10, 4, 2, '2024-10-01 08:54:34'))
    cursor.execute('''INSERT INTO `publicationproject` (`id`, `publication_id`, `project_id`, `assigned_at`) VALUES(%s, %s, %s, %s)''',
                   (11, 5, 2, '2024-10-01 08:54:46'))
    
    # PublicationTracking
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (1, 1, 1, 1, '2024-09-30 21:02:38', 1, '2024-09-30 21:02:38', None, None))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (2, 1, 2, 1, '2024-09-30 21:02:55', 1, '2024-09-30 21:02:55', 1, '2024-09-30 21:02:55'))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (3, 1, 3, 1, '2024-09-30 21:03:27', 1, '2024-09-30 21:03:27', None, None))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (4, 2, 1, 1, '2024-09-30 21:09:22', 1, '2024-10-01 11:07:10', None, None))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (5, 2, 2, 1, '2024-09-30 21:09:24', 1, '2024-10-01 11:07:16', 1, '2024-10-01 11:07:16'))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (6, 2, 3, 1, '2024-09-30 21:25:46', 1, '2024-10-01 11:07:22', 1, '2024-10-01 11:07:22'))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (7, 3, 1, 1, '2024-09-30 21:34:23', 1, '2024-09-30 21:34:23', None, None))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (8, 3, 2, 1, '2024-09-30 21:34:25', 1, '2024-09-30 21:34:25', None, None))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (9, 3, 3, 1, '2024-09-30 21:34:28', 1, '2024-09-30 21:34:28', None, None))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (10, 2, 4, 2, '2024-10-01 10:54:34', 1, '2024-10-01 11:07:42', None, None))
    cursor.execute('''INSERT INTO `publicationtracking` (`id`, `project_id`, `publication_id`, `user_id_added`, `added_at`, `user_id_last_modified`, `last_modified_at`, `user_id_completed`, `completed_at`) 
                   VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (11, 2, 5, 2, '2024-10-01 10:54:46', 1, '2024-10-01 11:07:36', 1, '2024-10-01 11:07:36'))
    
    #UserInreview
    cursor.execute('''INSERT INTO `usedinreview` (`id`, `publication_id`, `project_id`, `used_in_review`)
                   VALUES(%s, %s, %s, %s)''',
                   (1, 1, 2, 'ANO'))
    cursor.execute('''INSERT INTO `usedinreview` (`id`, `publication_id`, `project_id`, `used_in_review`)
                   VALUES(%s, %s, %s, %s)''',
                   (2, 3, 2, 'ANO'))
    cursor.execute('''INSERT INTO `usedinreview` (`id`, `publication_id`, `project_id`, `used_in_review`)
                   VALUES(%s, %s, %s, %s)''',
                   (3, 2, 2, 'ANO'))
    cursor.execute('''INSERT INTO `usedinreview` (`id`, `publication_id`, `project_id`, `used_in_review`)
                   VALUES(%s, %s, %s, %s)''',
                   (4, 4, 2, 'ANO'))
    cursor.execute('''INSERT INTO `usedinreview` (`id`, `publication_id`, `project_id`, `used_in_review`)
                   VALUES(%s, %s, %s, %s)''',
                   (5, 5, 2, 'ANO'))
    
    #UserProject
    cursor.execute('''INSERT INTO `userproject` (`id`, `user_id`, `project_id`)
                   VALUES(%s, %s, %s)''',
                   (3, 1, 2))
    cursor.execute('''INSERT INTO `userproject` (`id`, `user_id`, `project_id`)
                   VALUES(%s, %s, %s)''',
                   (4, 2, 2))


# Potvrzení změn a uzavření připojení
conn.commit()
cursor.close()
conn.close()

print("Databáze a tabulky byly úspěšně vytvořeny.")

