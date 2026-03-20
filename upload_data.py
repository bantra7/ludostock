import pandas as pd
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================
# 🔧 CONFIGURATION
# ==========================
BASE_URL = "https://ludostock-backend-1015299081216.europe-west1.run.app/api"
MAX_WORKERS = 5  # ⚡️ Nombre de threads utilisés pour l'upload
# ==========================

df = pd.read_csv("trictac_data_games.csv")

# Cache en mémoire
created_entities = {
    "authors": {},
    "editors": {},
    "artists": {},
    "distributors": {},
    "games": {}
}

def clean_value(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    return str(val).strip()

def entity_exists(entity_type, name):
    resp = requests.get(f"{BASE_URL}/{entity_type}/?limit=1000")
    resp.raise_for_status()
    for entity in resp.json():
        if entity["name"].strip().lower() == name.strip().lower():
            return entity["id"]
    return None

def create_entity(entity_type, name):
    if not name:
        return None

    if name in created_entities[entity_type]:
        return created_entities[entity_type][name]
    
    entity_id = entity_exists(entity_type, name)
    if entity_id:
        created_entities[entity_type][name] = entity_id
        return entity_id
    
    resp = requests.post(f"{BASE_URL}/{entity_type}/", json={"name": name})
    resp.raise_for_status()
    entity_id = resp.json()["id"]
    created_entities[entity_type][name] = entity_id
    return entity_id

def parse_players(value):
    if pd.isna(value):
        return None, None
    match = re.match(r"(\d+)\D+(\d+)", str(value))
    if match:
        return int(match.group(1)), int(match.group(2))
    num_match = re.search(r"(\d+)", str(value))
    return (int(num_match.group(1)), int(num_match.group(1))) if num_match else (None, None)

def parse_age(value):
    if pd.isna(value):
        return None
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else None

def parse_duration(value):
    if pd.isna(value):
        return None
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else None

def parse_year(value):
    if pd.isna(value):
        return None
    match = re.search(r"(19|20)\d{2}", str(value))
    return int(match.group(0)) if match else None

def map_game_type(value):
    if pd.isna(value):
        return "game"
    value = str(value).strip().lower()
    if value in ["jeu", "jeux", "game"]:
        return "game"
    if value in ["extension", "ext"]:
        return "extension"
    return "game"

def split_and_clean(value):
    if pd.isna(value):
        return []
    names = re.split(r"/|,", str(value))
    return [n.strip().replace('"', "'") for n in names if n.strip()]

def game_exists(name):
    resp = requests.get(f"{BASE_URL}/games/?limit=1000")
    resp.raise_for_status()
    for game in resp.json():
        if game["name"].strip().lower() == name.strip().lower():
            return game["id"]
    return None

def process_row(row):
    game_name = clean_value(row["Nom"])
    if not game_name:
        return f"Skipped empty name row."

    existing_game_id = game_exists(game_name)
    if existing_game_id:
        return f"Skipping existing game: {game_name} (ID {existing_game_id})"

    authors = split_and_clean(row["Auteurs"])
    editors = split_and_clean(row["Editeurs"])
    artists = split_and_clean(row["Artistes"])
    distributors = split_and_clean(row["Distributeurs"])

    for name in authors:
        create_entity("authors", name)
    for name in editors:
        create_entity("editors", name)
    for name in artists:
        create_entity("artists", name)
    for name in distributors:
        create_entity("distributors", name)

    min_players, max_players = parse_players(row["Nombre de joueurs"])
    min_age = parse_age(row["Age"])
    duration = parse_duration(row["Durée de partie"])
    year = parse_year(row["Année de sortie"])
    game_type = map_game_type(row["Type"])

    game_payload = {
        "name": game_name,
        "type": game_type,
        "creation_year": year,
        "min_players": min_players,
        "max_players": max_players,
        "min_age": min_age,
        "duration_minutes": duration,
        "url": clean_value(row["Url"]),
        "image_url": clean_value(row["Url Image"]),
        "authors": authors,
        "artists": artists,
        "editors": editors,
        "distributors": distributors
    }

    game_payload = {k: v for k, v in game_payload.items() if v is not None}

    resp = requests.post(f"{BASE_URL}/games/", json=game_payload)
    resp.raise_for_status()
    return f"Created game: {game_name} (ID {resp.json()['id']})"

results = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(process_row, row) for _, row in df.iterrows()]
    for future in as_completed(futures):
        try:
            results.append(future.result())
        except Exception as e:
            results.append(f"Error: {e}")

for r in results:
    print(r)

print("Upload completed.")
