import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Configuration de la base de données
DB_CONFIG = {
    "host": "34.32.44.163",
    "port": 5432,
    "dbname": "ludostock",
    "user": "ludostock",
    "password": "8RX1YBK~/?%5X0}E"
}

# Lecture du CSV
df = pd.read_csv("tous_les_jeux_trictrac.csv")

# Normalisation des colonnes attendues
df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

# Colonnes multiples à splitter (ex: auteurs, artistes...)
def split_and_strip(s):
    if pd.isna(s):
        return []
    return [part.strip() for part in str(s).split(",") if part.strip()]

# Connexion à PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Fonction pour insérer ou récupérer l'ID d'une entité liée
def get_or_create(table, name):
    cur.execute(f"SELECT id FROM {table} WHERE name = %s", (name,))
    result = cur.fetchone()
    if result:
        return result[0]
    cur.execute(f"INSERT INTO {table}(name) VALUES (%s) RETURNING id", (name,))
    return cur.fetchone()[0]

# Insertion principale des jeux
for i, row in df.iterrows():
    print(f"Insertion du jeu {i+1}/{len(df)}: {row.get('name')}")

    # Insertion dans `games`
    cur.execute("""
        INSERT INTO games (name, type, year, min_players, max_players, min_age, duration_minutes, language, url, image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        row.get('name'),
        row.get('type') if row.get('type') in ('game', 'extension') else 'game',
        row.get('year'),
        row.get('min_players'),
        row.get('max_players'),
        row.get('min_age'),
        row.get('duration_minutes'),
        row.get('language'),
        row.get('url'),
        row.get('image_url')
    ))
    game_id = cur.fetchone()[0]

    # Ajout des relations N-N
    for table, col_name, rel_table in [
        ("authors", "authors", "game_authors"),
        ("artists", "artists", "game_artists"),
        ("editors", "editors", "game_editors"),
        ("distributors", "distributors", "game_distributors")
    ]:
        names = split_and_strip(row.get(col_name))
        for name in names:
            entity_id = get_or_create(table, name)
            cur.execute(
                f"INSERT INTO {rel_table} (game_id, {table[:-1]}_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (game_id, entity_id)
            )

# Validation et fermeture
conn.commit()
cur.close()
conn.close()
print("✅ Import terminé avec succès.")
