### 1.2.0 (2026-04-07)

* Ajout d'un pipeline `cloudbuild.yaml` pour construire, publier et deployer les services `backend`, `frontend` et `auth` sur GCP/Cloud Run.
* Rendu du build backend autonome vis-a-vis du contexte Docker, avec injection possible de la version applicative via `APP_VERSION`.
* Adaptation du frontend Nginx pour parametrer dynamiquement les upstreams API et auth selon l'environnement de deploiement.
* Mise a jour de `docker-compose.yml` et de la documentation pour aligner l'execution locale et le deploiement GCP.

### 1.1.0 (2026-04-07)

* Ajout d'un service Better Auth dedie avec connexion Google, d'un client auth React et des scripts/package associes.
* Protection des routes FastAPI via validation de session Better Auth, avec nouvelles options de configuration (`AUTH_SERVICE_URL`, `AUTH_INTERNAL_SECRET`, timeout) et dependance `httpx`.
* Synchronisation ou creation automatique de l'utilisateur authentifie cote backend, creation de sa collection personnelle si absente, et nouveaux endpoints `GET /api/me/collection/games/` et `POST /api/me/collection/games/`.
* Extension des tests backend pour couvrir la collection personnelle et le branchement des nouvelles routes FastAPI.
* Evolution du frontend avec parcours de connexion/deconnexion Google, ecran d'authentification, menu profil, nouvelle navigation `Ma collection` et ajout de jeux du catalogue vers la collection personnelle.
* Refonte de certaines interactions d'interface, notamment les cartes de survol des jeux, la pagination/libelles et les styles associes.
* Passage du frontend sur une base d'API relative `/api` avec cookies inclus, proxys Vite et Nginx pour `/api` et `/api/auth`, et mise a jour de l'image frontend pour embarquer cette configuration.
* Mise a jour de `docker-compose.yml` et de la documentation (`README.md`, `backend/README.md`) pour decrire le nouveau service auth, les variables d'environnement et les modes d'execution local/Docker.

### 1.0.3 (2026-04-06)

* Amelioration de l'exploration du catalogue avec recherche, tri et pagination cote interface.
* Ajout d'une gestion paginee des referentiels (auteurs, artistes, editeurs, distributeurs) avec creation et suppression.
* Rafraichissement de l'interface React avec nouveau logo, cartes de survol sur les jeux et navigation plus lisible.

### 1.0.2 (2026-04-06)

* Centralisation du versionning dans un fichier racine `VERSION`.
* Injection de la version partagee dans le build frontend via Vite.
* Lecture de la meme version partagee par le backend FastAPI.
* Ajustement des Dockerfiles et de `docker-compose.yml` pour conserver cette source unique en build.

### 1.0.1 (2026-04-06)

* Ajout d'un versionning simple et explicite pour le frontend et le backend.
* Ajout de l'endpoint `GET /api/meta/version/` pour exposer la version du backend.
* Affichage des versions front et back dans le footer de l'application.
* Mise a jour du changelog pour refleter cette livraison.

### 0.0.1 (2022-10-23)

* Version initiale.
