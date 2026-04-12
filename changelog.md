### 1.5.1 (2026-04-12)

* Correction des accents et des libelles francais dans l'interface React.
* Mise a jour de la documentation utilisateur pour harmoniser les textes visibles.

### 1.5.0 (2026-04-12)

* Ajout du partage de collection via lien d'invitation activable depuis `Parametres`, avec copie du lien, regeneration et desactivation.
* Ajout de l'onglet `Mes amis` pour lister les collections partagees avec l'utilisateur et consulter leur rangement en lecture seule.
* Ajout de l'administration des droits de vue de la collection personnelle, avec liste des abonnes et retrait d'acces individuel.
* Ajout du desabonnement a une collection partagee depuis l'onglet `Mes amis`.
* Extension du backend FastAPI/SQLite et des tests pour couvrir le jeton de partage, l'abonnement, la revocation et l'acces aux collections amies.
* Correction du comportement de la collection personnelle sur Cloud Run en remplaçant le simple seeding SQLite depuis GCS par une vraie synchronisation du snapshot SQLite avec Google Cloud Storage.
* Ajout de logs backend cibles pour diagnostiquer les ajouts en collection, le chargement du board personnel, le contexte d'instance Cloud Run et les problemes de session.
* Mise a jour du deploiement et de la documentation pour utiliser `SQLITE_GCS_BUCKET` et `SQLITE_GCS_OBJECT`, avec droits d'ecriture GCS pour le backend.

### 1.4.2 (2026-04-11)

* Correction de la recherche rapide en barre superieure pour que le bouton `+` declenche bien l'ajout en collection sans fermer le panneau trop tot.
* Renforcement des actions de `Ma collection` avec resynchronisation de l'etat depuis le backend apres ajout, retrait, deplacement et mise a jour des lieux.
* Uniformisation du libelle `Retirer` dans les vues de collection.
* Ajustement de l'affichage des images pour des miniatures moins imposantes et mieux cadrees dans la recherche rapide, les derniers ajouts et les cartes de collection.

### 1.4.1 (2026-04-09)

* Separation de `Ma collection` et `Catalogue`, avec compteur du catalogue dans le titre et tri par defaut sur les annees decroissantes.
* Reorganisation de `Ma collection` en zones simples `Mes lieux`, `Mes jeux` et `Rangement par lieu`, avec cartes de rangement allegees et survol complet sur l'image.
* Ajout d'une recherche rapide dans la barre superieure pour trouver un jeu du catalogue et l'ajouter directement a la collection.
* Ajout du renommage et de la suppression des lieux personnels, avec suppression qui conserve les jeux dans la collection en `Sans lieu`.
* Simplification de l'accueil avec trois compteurs collection, derniers ajouts avec nom du lieu, et retrait des actions rapides redondantes.

### 1.4.0 (2026-04-09)

* Ajout d'un parcours catalogue -> collection avec action `Ajouter`, badge `Dans ma collection` et rafraichissement du board personnel.
* Ajout de la creation de lieux depuis `Ma collection` et d'un menu `Deplacer vers` en complement du drag-and-drop.
* Remplacement des confirmations navigateur par une modale Ludostock pour les suppressions.
* Amelioration des etats vides et de recherche avec actions de retour au catalogue ou de remise a zero.
* Refonte responsive du catalogue sur mobile : lignes transformees en cartes, controles pleine largeur et board collection en colonne.
* Restriction de l'administration du catalogue et des referentiels a `renault.jbapt@gmail.com`, avec garde backend, masquage frontend et tests dedies.

### 1.3.0 (2026-04-08)

* Refonte de l'onglet `Ma collection` pour afficher une vue par lieux avec colonnes dediees.
* Ajout de la gestion des lieux personnels dans la collection, avec endpoints backend pour creer un lieu, recuperer le board personnel et deplacer un jeu entre lieux.
* Ajout du drag-and-drop des jeux entre lieux dans l'interface.
* Mise en avant de la vignette et du nom des jeux dans les cartes de collection, avec simplification de l'en-tete pour ne conserver que la recherche.
* Extension des tests backend pour couvrir le board personnel, la creation de lieux et le deplacement des jeux.

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
