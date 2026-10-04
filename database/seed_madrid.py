"""Add a small, sourced Madrid catalog without changing personal saved places.

Run with: python -m database.seed_madrid
Names, cuisines, and addresses come from the linked Madrid tourism listings.
"""

from contextlib import closing

from . import connect_database, database_path, initialize_database


# (name, cuisine, street, postcode, Madrid tourism source)
RESTAURANTS = (
    ("Botín", "Madrilenian", "Calle de Cuchilleros, 17", "28005", "https://www.esmadrid.com/en/restaurants/botin"),
    ("Casa Lucio", "Madrilenian", "Calle de la Cava Baja, 35", "28005", "https://www.esmadrid.com/en/restaurants/casa-lucio"),
    ("La Bola", "Madrilenian", "Calle de la Bola, 5", "28013", "https://www.esmadrid.com/en/restaurants/bola"),
    ("La Trainera", "Seafood", "Calle de Lagasca, 60", "28001", "https://www.esmadrid.com/en/restaurants/la-trainera"),
    ("Sala de Despiece", "Tapas", "Calle de Alonso Cano, 28", "28010", "https://www.esmadrid.com/en/restaurants/sala-de-despiece"),
    ("Estimar", "Seafood", "Calle del Marqués de Cubas, 18", "28014", "https://www.esmadrid.com/en/restaurants/estimar"),
    ("Lhardy", "Madrilenian", "Carrera de San Jerónimo, 8", "28014", "https://www.esmadrid.com/en/restaurants/lhardy"),
    ("Sacha", "Spanish", "Calle de Juan Hurtado de Mendoza, 11", "28036", "https://www.esmadrid.com/en/restaurants/sacha"),
    ("Le Bistroman Atelier", "French", "Calle de la Amnistía, 10", "28013", "https://www.esmadrid.com/en/restaurants/bistroman-atelier"),
    ("La Casa del Abuelo", "Tapas", "Calle de la Victoria, 12", "28012", "https://www.esmadrid.com/en/restaurants/casa-abuelo"),
    ("Casa de Comidas", "Spanish", "Calle del Padre Damián, 23", "28036", "https://www.esmadrid.com/en/restaurants/casa-comidas"),
    ("Kabuki Madrid", "Japanese", "Calle de Lagasca, 38", "28001", "https://www.esmadrid.com/en/restaurants/kabuki-madrid"),
    ("Mestizo", "Mexican", "Calle de Recoletos, 13", "28001", "https://www.esmadrid.com/en/restaurants/mestizo"),
    ("NOI", "Italian", "Calle de Recoletos, 6", "28001", "https://www.esmadrid.com/en/restaurants/noi"),
)


def seed_madrid(database_file):
    """Insert missing catalog entries and return how many were added."""
    initialize_database(database_file)
    added = 0
    with closing(connect_database(database_file)) as connection, connection:
        for title, cuisine, street, postal_code, _source in RESTAURANTS:
            exists = connection.execute(
                """SELECT 1 FROM restaurants
                   WHERE lower(trim(title)) = lower(?)
                     AND lower(trim(city)) = 'madrid'""",
                (title,),
            ).fetchone()
            if exists:
                continue
            connection.execute(
                """INSERT INTO restaurants
                   (title, category_name, address, street, city, postal_code, country_code)
                   VALUES (?, ?, ?, ?, 'Madrid', ?, 'ES')""",
                (title, cuisine, f"{street}, {postal_code} Madrid, Spain", street, postal_code),
            )
            added += 1
    return added


if __name__ == "__main__":
    print(f"Added {seed_madrid(database_path())} Madrid restaurants to the catalog.")
