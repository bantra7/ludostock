# Backend

Cette application backend est développée avec FastAPI et fournit une API pour gérer une collection de jeux de société. Elle utilise SQLAlchemy pour l'ORM, Alembic pour les migrations de base de données, et DuckDB comme base de données.

## Configuration et Exécution

### Prérequis

- Python 3.11+
- pip (gestionnaire de paquets Python)

### Installation des dépendances

1. Naviguez vers le répertoire `backend` :
   ```bash
   cd backend
   ```
2. Installez les dépendances Python :
   ```bash
   python -m pip install -r requirements.txt
   ```

### Exécution de l'application en mode développement

Pour démarrer le serveur de développement, exécutez le script suivant depuis le répertoire `backend` :

```bash
./start-dev.sh
```

Ou exécutez directement la commande uvicorn :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

L'application sera alors accessible à l'adresse `http://localhost:8080`.

### Base de données

L'application utilise DuckDB. Les migrations de base de données sont gérées avec Alembic.
(Des instructions supplémentaires sur l'initialisation de la base de données ou l'exécution des migrations pourraient être ajoutées ici si nécessaire).
