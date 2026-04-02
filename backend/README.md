# Backend

Ce backend FastAPI utilise maintenant SQLite en local, sans Supabase ni mecanisme d'authentification.

## Configuration

Les variables utiles sont :

- `SQLITE_PATH` : chemin du fichier SQLite
- `ENV_PATH` : fichier `.env` a charger
- `ALLOW_ORIGINS` : liste CORS, en CSV ou JSON

Un exemple est fourni dans [backend/app/.env.example](/c:/Users/renau/projects/ludostock/backend/app/.env.example).

## Installation

Depuis la racine du projet :

```powershell
python -m pip install -r backend/requirements.txt
```

## Lancer le backend en local

```powershell
$env:ENV_PATH="backend/app/.env"
uvicorn backend.app.main:app --host 0.0.0.0 --port 8081 --reload
```

Au demarrage, l'application cree automatiquement le fichier SQLite et ses tables si besoin.

## Importer un CSV de jeux

```powershell
$env:ENV_PATH="backend/app/.env"
python -m backend.app.import_games --csv-path data/raw/trictac_data_games.csv
```

Le script :

- convertit les colonnes du CSV ;
- cree les jeux et les relations auteurs/artistes/editeurs/distributeurs ;
- ecrit dans la base SQLite configuree.

## Exemple d'environnement

```text
ENVIRONMENT=local
SQLITE_PATH=backend/app/ludostock.db
ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Tests backend

```powershell
python -m pip install -r backend/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest backend/tests
```
