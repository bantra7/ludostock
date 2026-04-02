# LudoStock

## 1. Vue utilisateur

### Positionnement du produit

LudoStock est une application de gestion de collection de jeux de societe. Son objectif est d'aider un utilisateur a centraliser les informations sur ses jeux, structurer ses collections personnelles et, a terme, faciliter le partage de ces collections avec d'autres personnes.

Le produit se situe a la croisee de deux besoins :

- disposer d'un catalogue de jeux de reference, avec leurs informations principales ;
- organiser sa propre ludotheque de maniere pratique, avec une logique de possession, d'emplacement et de partage.

Dans le code actuel, cette intention produit est bien visible et assez coherente : le backend porte deja un modele metier complet autour du catalogue, des utilisateurs, des collections, des emplacements et du partage. Le frontend, lui, montre une experience partiellement aboutie, avec une authentification fonctionnelle et des elements d'interface qui affichent clairement la promesse du produit, mais sans exposer encore toute la richesse du modele metier.

### Besoins couverts

L'application cherche a repondre a plusieurs usages concrets pour un collectionneur de jeux de societe :

- recenser les jeux dans un catalogue commun, avec leur type, leurs caracteristiques et leurs contributeurs ;
- creer une ou plusieurs collections rattachees a un utilisateur ;
- associer des jeux a une collection avec une quantite ;
- organiser physiquement ses jeux grace a des emplacements nommes ;
- preparer le partage d'une collection avec d'autres utilisateurs, avec des droits de lecture ou d'ecriture.

Autrement dit, LudoStock ne se limite pas a une simple liste de jeux. Le produit vise une gestion plus operationnelle d'une ludotheque, avec une distinction entre :

- le jeu comme objet de catalogue ;
- le jeu possede dans une collection donnee ;
- le lieu ou cet exemplaire est range ;
- les personnes autorisees a consulter ou modifier une collection.

### Parcours utilisateur visible aujourd'hui

#### Authentification

Le parcours d'entree le plus clair dans le frontend est l'authentification. L'utilisateur arrive sur une page de connexion / inscription qui s'appuie sur Supabase Auth. Le systeme permet :

- l'inscription par email et mot de passe ;
- la connexion par email et mot de passe ;
- l'authentification sociale via Google et GitHub.

Une fois authentifie, l'utilisateur est redirige vers la page principale. Cette partie est la plus directement visible et la mieux structuree du frontend actuel.

#### Page d'accueil connectee

Apres connexion, l'application affiche une page d'accueil simple qui presente LudoStock comme un gestionnaire personnel de collection de jeux de societe. Trois promesses produit y sont mises en avant :

- **My Collection** : gerer sa collection de jeux ;
- **Game Lists** : creer et partager des listes ;
- **Locations** : suivre l'endroit ou les jeux sont stockes.

Cette page sert surtout de vitrine fonctionnelle. Elle exprime clairement la direction produit, mais elle ne donne pas encore acces, dans l'etat actuel du code, a tous les parcours detailes correspondants.

#### Gestion des jeux

Le repo contient aussi une page dediee a la gestion des jeux, `BoardgamesPage`, avec les briques attendues pour :

- afficher une liste de jeux ;
- ouvrir un formulaire de creation ou de modification ;
- supprimer un jeu ;
- appeler le backend avec un token d'authentification.

D'un point de vue produit, cette zone represente la partie la plus proche d'une gestion concrete du catalogue. Elle suggere une interface d'administration ou de saisie de jeux.

Cependant, cette partie apparait comme une zone en transition :

- elle cohabite avec un frontend plus recent en TypeScript et composants UI modernes ;
- elle utilise des composants et conventions differents ;
- certaines integrations semblent inachevees ou incoherentes, ce qui laisse penser qu'il s'agit d'un reliquat d'une ancienne implementation ou d'un chantier de migration.

Il faut donc la considerer comme un indicateur fiable de l'intention fonctionnelle, mais pas comme une experience entierement stabilisee.

### Ce qui semble operationnel vs ce qui reste partiel

#### Ce qui ressort comme solide

- l'existence d'un systeme d'authentification utilisateur via Supabase ;
- la presence d'un backend structure autour des objets metier principaux ;
- la possibilite de gerer un catalogue de jeux via des endpoints API dedies ;
- la prise en charge des collections, des emplacements et du partage au niveau du modele metier et des routes backend.

#### Ce qui ressemble encore a une promesse produit ou a une integration incomplete

- l'exposition complete des collections dans l'interface utilisateur ;
- la gestion visuelle des emplacements de stockage ;
- l'interface de partage de collection entre utilisateurs ;
- l'unification du frontend autour d'une seule experience coherente.

En resume, du point de vue utilisateur, LudoStock est deja pense comme un gestionnaire de ludotheque collaborative ou semi-collaborative. Le socle fonctionnel est bien defini. En revanche, l'interface actuellement visible ne semble pas encore couvrir de bout en bout l'ensemble de cette promesse.

## 2. Vue technique

### Architecture generale

Le projet est organise autour de quatre briques principales :

- un **frontend web** en React ;
- un **backend API** en FastAPI ;
- une **base de donnees** externe via Supabase ;
- un **service d'authentification** externe via Supabase.

Le frontend et le backend sont separes. Le frontend gere l'experience utilisateur, la session et les appels reseau. Le backend porte les regles metier, l'exposition des donnees et la persistence.

Le projet contient aussi des scripts et ressources de donnees, ce qui montre une intention d'alimentation initiale du catalogue a partir de sources externes.

### Frontend

Le frontend repose principalement sur React avec Vite, TypeScript, React Router et une bibliotheque de composants UI moderne. Il comprend :

- un provider d'authentification connecte a Supabase ;
- une page d'authentification ;
- une page d'accueil protegee ;
- une route supplementaire pour la gestion de jeux.

Le frontend montre toutefois une cohabitation entre deux couches :

- une couche recente, en TypeScript, avec une structure moderne et une authentification bien integree ;
- une couche plus ancienne ou plus experimentale, basee sur d'autres composants, autour de `BoardgamesPage`, `BoardgameList` et `BoardgameForm`.

Cette coexistence est importante pour comprendre l'etat du repo : le produit a une direction technique claire, mais le chantier frontend n'est pas totalement homogene.

### Backend

Le backend est une application FastAPI exposee sous forme d'API REST. Il s'appuie sur SQLAlchemy pour le mapping objet-relationnel et sur une base PostgreSQL hebergee via Supabase.

Le point d'entree charge l'environnement, configure le CORS, initialise le schema si necessaire, puis expose les endpoints metier.

L'authentification se fait par verification du token d'acces Supabase :

- le frontend obtient un token via Supabase Auth ;
- le backend appelle l'endpoint utilisateur de Supabase pour verifier ce token ;
- l'identifiant utilisateur issu du token est ensuite reutilise dans les regles metier, notamment pour les collections et les emplacements.

Une option de desactivation de l'authentification est prevue par configuration, ce qui facilite les environnements de developpement ou de test.

### Objets metier principaux

#### Catalogue global de jeux

Le coeur du domaine est la table `games`. Elle represente un catalogue global de jeux, independant d'un utilisateur. Chaque jeu peut porter des informations comme :

- son nom ;
- son type ;
- son annee de creation ;
- le nombre minimum et maximum de joueurs ;
- l'age minimum ;
- la duree ;
- une URL et une image ;
- une reference vers un jeu parent dans le cas d'une extension.

Le schema SQL precise que le type vise notamment les valeurs `game` et `extension`. Le modele SQLAlchemy et les schemas Pydantic traduisent cette meme intention.

#### Entites liees au jeu

Le catalogue peut etre enrichi par plusieurs relations many-to-many :

- `authors` ;
- `artists` ;
- `editors` ;
- `distributors`.

Lors de la creation d'un jeu, le backend peut rattacher ces entites par leur nom. Si une entite existe deja, elle est reutilisee ; sinon elle est creee. Cette logique evite la duplication des fiches de contributeurs ou d'acteurs de la chaine editoriale.

Le backend inclut egalement une verification pour empecher la repetition d'un meme nom dans une meme requete de creation.

#### Utilisateurs

Les utilisateurs sont stockes dans `users`. Leur identifiant principal est un UUID, coherent avec un usage Supabase Auth. La table conserve aussi l'email et un nom d'utilisateur optionnel.

Le backend permet de creer, lister, consulter et supprimer des utilisateurs. Lors de la creation, l'identifiant peut venir du contexte d'authentification ; sinon un UUID est genere.

#### Collections

Les collections sont modelisees dans `collections`. Chaque collection appartient a un utilisateur via `owner_id` et contient :

- un nom ;
- une description optionnelle.

Le modele permet a un meme utilisateur de posseder plusieurs collections. Cette structure ouvre la voie a plusieurs cas d'usage : separation par foyer, par lieu, par type de jeux ou par usage.

#### Partage de collections

Le partage est porte par `collection_shares`. Cette table relie une collection a un autre utilisateur avec un niveau de permission.

Deux permissions sont prevues :

- `read` ;
- `write`.

Une regle metier importante est deja implemente dans l'API : seul le proprietaire de la collection peut creer un partage. Cela montre que le produit ne vise pas seulement le stockage des donnees, mais aussi une gouvernance minimale des droits d'acces.

#### Emplacements utilisateur

Les emplacements sont modelises par `user_locations`. Ils sont propres a chaque utilisateur et identifies par un nom unique dans le perimetre de cet utilisateur.

Cette brique est importante sur le plan produit : elle transforme LudoStock en outil d'organisation physique de la ludotheque, pas seulement en catalogue numerique. Un utilisateur peut par exemple distinguer une ludotheque principale, un placard, une cave, une salle de jeu ou un lieu de pret.

#### Jeux dans une collection

La table `collection_games` fait le lien entre :

- une collection ;
- un jeu du catalogue ;
- un emplacement eventuel ;
- une quantite.

Ce point est central : le modele distingue clairement l'entite "jeu" dans le catalogue global de l'entite "jeu possede" dans une collection utilisateur. C'est cette distinction qui permet d'exprimer la possession, le rangement et potentiellement, plus tard, le partage et la consultation multi-utilisateur.

### API et regles metier visibles

L'API expose des routes pour chacun des grands objets metier :

- jeux ;
- auteurs ;
- artistes ;
- editeurs ;
- distributeurs ;
- utilisateurs ;
- collections ;
- partages de collections ;
- emplacements utilisateur ;
- jeux rattaches a une collection.

Les operations exposees sont principalement de type creation, lecture, liste et suppression. Le backend couvre donc deja les besoins fondamentaux de CRUD pour la plupart des entites importantes.

Parmi les regles metier visibles dans le code :

- un jeu peut etre cree avec ses relations vers auteurs, artistes, editeurs et distributeurs ;
- les conflits d'unicite remontent sous forme de reponses `409` sur plusieurs entites ;
- une collection est automatiquement rattachee a l'utilisateur authentifie qui la cree ;
- un partage de collection est refuse si le demandeur n'est pas le proprietaire ;
- un emplacement est cree dans le contexte de l'utilisateur authentifie ;
- une combinaison collection / jeu / emplacement doit rester unique dans `collection_games`.

Ces regles montrent un backend deja pense pour porter de vraies contraintes produit, au-dela d'un simple stockage brut.

### Base de donnees et initialisation

La persistence repose sur PostgreSQL via Supabase. Le schema applicatif est decrit dans les modeles SQLAlchemy du backend, avec :

- les tables principales ;
- les tables d'association many-to-many ;
- les cles etrangeres ;
- plusieurs contraintes d'unicite ;
- certaines contraintes de verification, par exemple sur les permissions de partage.

Au demarrage, le backend peut creer les tables manquantes a partir des modeles SQLAlchemy si l'initialisation automatique est active. Cette approche reste simple pour le developpement local, tout en s'appuyant sur une vraie base PostgreSQL hebergee, plus proche d'un environnement de production.

Le choix de Supabase PostgreSQL apporte une base relationnelle robuste, un hebergement gere, une bonne compatibilite avec SQLAlchemy et une coherence naturelle avec Supabase Auth deja utilise par le frontend et le backend.

### Validation, erreurs et robustesse

Le backend utilise Pydantic pour valider les structures de donnees entrantes et SQLAlchemy pour la persistence. La couche `crud.py` centralise la logique metier de base.

Plusieurs mecanismes de robustesse sont visibles :

- gestion explicite des erreurs d'integrite ;
- rollback de transaction en cas d'echec ;
- retour d'erreurs `404` lorsqu'une ressource n'existe pas ;
- retour d'erreurs `403` pour les violations de droit sur le partage ;
- retour d'erreurs `401` ou `503` pour les problemes lies a l'authentification externe.

Les tests backend confirment une partie de ces attentes, notamment :

- la creation d'utilisateur avec UUID ;
- la gestion de conflit sur les auteurs ;
- le caractere atomique d'une creation de jeu invalide ;
- la suppression d'un jeu dans une collection ;
- le controle d'autorisation sur le partage de collection.

### Scripts de donnees et alimentation

Le repo contient un dossier `data` avec :

- des fichiers CSV bruts ;
- des scripts Python ;
- un notebook d'exploration.

Cela indique une intention d'import ou de preparation d'un catalogue initial depuis une source externe. Dans l'etat actuel du code, cette partie semble encore preparatoire ou partiellement outillee, mais elle renforce l'idee que LudoStock veut s'appuyer sur un catalogue riche plutot que sur une saisie manuelle complete par chaque utilisateur.

### Etat actuel du repo

Techniquement, le projet montre une base solide sur le backend et une vision produit deja bien modelee. La partie la plus mature semble etre :

- la modelisation metier ;
- l'API FastAPI ;
- les contraintes de donnees sur PostgreSQL/Supabase ;
- l'authentification integree a Supabase ;
- les premiers tests backend.

Le principal point de transition se situe dans le frontend. Le repo montre a la fois :

- une base recente, propre et moderne pour l'authentification et le shell applicatif ;
- une ancienne couche ou une couche intermediaire pour la gestion des jeux, qui ne semble pas encore totalement alignee avec le reste.

En consequence, LudoStock peut etre decrit comme un produit dont le coeur metier est deja clairement etabli, mais dont l'experience utilisateur complete reste encore en phase de consolidation.

### Synthese

Du point de vue produit, LudoStock ambitionne de devenir un outil complet de gestion de ludotheque personnelle et partagee.

Du point de vue technique, le projet dispose deja :

- d'un backend structure autour d'un domaine pertinent ;
- d'une authentification moderne ;
- d'un modele de donnees coherent pour le catalogue, les collections et les droits ;
- d'une base frontend active, mais encore heterogene.

La lecture du repo montre donc un produit prometteur et relativement bien pense dans son architecture metier, avec un enjeu principal de finition et d'unification cote interface.
