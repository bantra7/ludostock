# Backend

Ce backend FastAPI utilise SQLite en local et s'appuie sur un service Better Auth externe pour valider les sessions Google.

## Configuration

Les variables utiles sont :

- `SQLITE_PATH` : chemin du fichier SQLite
- `SQLITE_GCS_BUCKET` : bucket GCS utilise pour synchroniser le snapshot SQLite
- `SQLITE_GCS_OBJECT` : objet GCS cible du snapshot SQLite
- `ENV_PATH` : fichier `.env` a charger
- `ALLOW_ORIGINS` : liste CORS, en CSV ou JSON
- `AUTH_SERVICE_URL` : URL du service Better Auth
- `AUTH_INTERNAL_SECRET` : secret partage entre FastAPI et le service auth
- `AUTH_SERVICE_TIMEOUT_SECONDS` : timeout des validations de session

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
Si `SQLITE_GCS_BUCKET` et `SQLITE_GCS_OBJECT` sont renseignes, le backend telecharge d'abord le snapshot distant puis republie un snapshot apres chaque commit d'ecriture.

## Importer un CSV de jeux

```powershell
.\.venv\Scripts\python.exe import_data.py --csv-path data/raw/trictac_data_games.csv --db-path backend/app/ludostock.db --force
```

Le script :

- convertit les colonnes du CSV ;
- cree les jeux et les relations auteurs/artistes/editeurs/distributeurs ;
- tente de relier les extensions a leur jeu parent quand cela peut etre deduit proprement ;
- ecrit dans la base SQLite cible.

Le CSV enrichi `data/raw/trictac_data_games.csv` contient deja les colonnes `Auteurs`, `Artistes`, `Editeurs` et `Distributeurs`, donc il peut etre importe directement.
Le CSV historique `data/raw/trictac_data.csv` ne contient pas ces colonnes ; si tu l'utilises, il faudra completer ces relations par un autre moyen avant d'obtenir une base complete.

## Exemple d'environnement

```text
ENVIRONMENT=local
SQLITE_PATH=backend/app/ludostock.db
SQLITE_GCS_BUCKET=
SQLITE_GCS_OBJECT=
ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost,http://127.0.0.1
AUTH_SERVICE_URL=http://localhost:3001
AUTH_INTERNAL_SECRET=replace-with-your-internal-shared-secret
```

## Tests backend

```powershell
python -m pip install -r backend/requirements-test.txt
.\.venv\Scripts\python.exe -m pytest backend/tests
```
