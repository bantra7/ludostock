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
