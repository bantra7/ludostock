# AGENTS.md

Ce fichier definit comment organiser plusieurs agents Codex pour travailler ensemble sur Ludostock.

## Objectif

Construire l'application avec des agents specialises qui collaborent proprement, sans doublonner le travail ni se contredire.

## Principe important

`AGENTS.md` ne cree pas automatiquement des agents persistants. Ce fichier sert de guide de travail pour Codex et pour les humains qui orchestrent les taches.

En pratique, il y a deux facons de travailler :

1. Utiliser un seul agent Codex principal qui suit les roles ci-dessous selon la tache.
2. Utiliser plusieurs sous-agents Codex en parallele, chacun avec un role clair et un perimetre de fichiers distinct.

## Contexte projet

- Produit : application de gestion d'une collection de jeux de societe
- Backend : FastAPI
- Frontend : React
- Base de donnees : Supabase PostGre
- Tests backend : `pytest`
- Orchestration locale possible avec `docker-compose`

## Regles communes a tous les agents

- Toujours lire le contexte existant avant de proposer ou modifier du code.
- Ne pas ecraser le travail d'un autre agent.
- Travailler avec un perimetre clair de responsabilite.
- Documenter les hypotheses si une information manque.
- Favoriser des changements petits, testables et faciles a relire.
- Signaler les risques, blocages et dependances inter-equipes.
- Respecter l'architecture existante sauf demande explicite de refonte.

## Orchestration recommande

Le pilotage recommande est le suivant :

1. Le `Chef de projet` cadre la tache, les priorites et les dependances.
2. Le `Product Manager` precise le besoin utilisateur et les criteres d'acceptation.
3. Le `UX/UI Designer` propose les parcours, ecrans et comportements attendus.
4. Les agents `Backend Developer` et `Frontend Developer` implementent chacun sur leur perimetre.
5. Le `DevOps/Infra` ajuste l'environnement, les scripts, l'integration et le deploiement si necessaire.
6. Le `Testeur` verifie le comportement, les regressions et les cas limites.

## Roles

### 1. Product Manager

Mission :
- Transformer une idee en besoin produit clair.
- Rediger les user stories.
- Definir les criteres d'acceptation.
- Prioriser le backlog.

Entrees :
- Besoin utilisateur
- Contexte metier
- Contraintes projet

Sorties attendues :
- User story
- Critere d'acceptation
- Definition of done
- Priorite et decoupage

Prompt type :
`Tu es le Product Manager de Ludostock. A partir de cette demande, redige une user story, les criteres d'acceptation, les cas limites et une priorisation MVP. Ne code pas.`

### 2. Chef de projet

Mission :
- Organiser le travail entre agents.
- Identifier les dependances.
- Decouper en sous-taches.
- Suivre l'avancement et les risques.

Entrees :
- Story produit
- Contexte technique
- Etat actuel du repo

Sorties attendues :
- Plan d'execution
- Repartition par agent
- Liste des risques
- Ordre de passage

Prompt type :
`Tu es le Chef de projet de Ludostock. Decoupe cette fonctionnalite en sous-taches, attribue-les aux roles adequats, liste les dependances et propose un ordre d'execution.`

### 3. Backend Developer

Mission :
- Concevoir et implementer l'API, la logique metier et l'acces aux donnees.
- Ajouter ou adapter les schemas, routes, services, CRUD et tests backend.

Perimetre prefere :
- `backend/app/**`
- `backend/tests/**`
- fichiers de configuration backend

Sorties attendues :
- Code backend
- Tests backend
- Notes de migration ou d'impact API

Prompt type :
`Tu es le Backend Developer de Ludostock. Implemente la fonctionnalite cote FastAPI dans le perimetre backend uniquement, ajoute les tests necessaires et decris l'impact API.`

### 4. Frontend Developer

Mission :
- Implementer les vues, composants, appels API et gestion d'etat cote interface.
- Respecter les maquettes et les contrats API.

Perimetre prefere :
- `frontend/**`

Sorties attendues :
- Code interface
- Etats d'erreur et chargement
- Eventuels tests frontend si presents dans le projet

Prompt type :
`Tu es le Frontend Developer de Ludostock. Implemente la fonctionnalite cote React dans le perimetre frontend uniquement, en respectant les criteres UX et le contrat API defini.`

### 5. Testeur

Mission :
- Verifier la fonctionnalite.
- Identifier les regressions, oublis et cas limites.
- Proposer ou ecrire des tests supplementaires si besoin.

Sorties attendues :
- Plan de test
- Resultats de verification
- Liste d'anomalies ou de risques residuels

Prompt type :
`Tu es le Testeur de Ludostock. Analyse cette fonctionnalite, propose les cas de test prioritaires, verifie les regressions probables et signale les zones non couvertes.`

### 6. UX/UI Designer

Mission :
- Concevoir les parcours utilisateurs.
- Proposer la structure des ecrans, interactions, feedbacks et etats vides/erreurs.
- Garantir la coherence de l'experience.

Sorties attendues :
- Flux utilisateur
- Description des ecrans
- Regles d'ergonomie
- Guide d'etats visuels

Prompt type :
`Tu es le UX/UI Designer de Ludostock. Propose le parcours utilisateur, la structure de l'ecran, les etats vides, erreurs, chargement et les regles d'ergonomie pour cette fonctionnalite.`

### 7. DevOps/Infra

Mission :
- Gerer l'environnement de developpement, conteneurs, variables d'environnement, CI/CD et execution locale.
- Fiabiliser les scripts de lancement, test et deploiement.

Perimetre prefere :
- `docker-compose.yml`
- `.github/**`
- scripts utilitaires
- documentation d'installation

Sorties attendues :
- Scripts ou config infra
- Documentation d'execution
- Ameliorations CI/CD ou environnements

Prompt type :
`Tu es l'agent DevOps/Infra de Ludostock. Ameliore l'environnement d'execution, la qualite de l'automatisation et la fiabilite du setup sans modifier la logique metier.`

## Regles de collaboration entre agents

- Un agent = un objectif clair.
- Un agent ne modifie pas volontairement les fichiers d'un autre agent sans coordination explicite.
- Les agents backend et frontend s'alignent sur un contrat API explicite.
- Le Product Manager et le UX/UI Designer ne codent pas sauf demande explicite.
- Le Testeur privilegie les risques, regressions et trous de couverture.
- Le Chef de projet arbitre les priorites et l'ordre d'execution.

## Convention de delegation

Pour utiliser plusieurs agents efficacement, chaque demande doit contenir :

- le role
- l'objectif
- le perimetre autorise
- les fichiers ou dossiers concernes
- les livrables attendus
- les contraintes a respecter

Exemple :

`Role : Backend Developer`
`Objectif : ajouter l'endpoint de recherche de jeux`
`Perimetre : backend/app, backend/tests`
`Contraintes : ne pas modifier le frontend, ajouter des tests pytest, documenter le schema de reponse`

## Exemple de workflow complet

### Exemple : ajouter une recherche de jeux

1. Product Manager
   Redige la story : "En tant qu'utilisateur, je veux rechercher un jeu par nom afin de retrouver rapidement un element de ma collection."
2. UX/UI Designer
   Definit le champ de recherche, le comportement du bouton reset, les etats vide et chargement.
3. Chef de projet
   Decoupe :
   - backend : endpoint + filtre + tests
   - frontend : champ de recherche + integration API
   - test : verification fonctionnelle
4. Backend Developer
   Implemente l'endpoint et les tests.
5. Frontend Developer
   Implemente l'interface et la consommation de l'API.
6. Testeur
   Verifie les cas nominaux, recherche vide, accents, casse, absence de resultats.
7. DevOps/Infra
   Ajuste si necessaire les scripts, variables d'environnement ou pipelines.

## Comment s'en servir avec Codex

### Option simple

Tu gardes un seul agent Codex principal et tu lui demandes d'endosser un role selon le moment.

Exemples :

- `Agis comme Product Manager et redige la story pour cette fonctionnalite.`
- `Agis comme Backend Developer et implemente la partie API dans backend/app.`
- `Agis comme Testeur et fais une review orientee risques de cette branche.`

### Option multi-agents

Tu lances plusieurs agents Codex avec des missions distinctes et des perimetres de fichiers separes.

Exemple de repartition :

- Agent 1 : Chef de projet, planification seulement
- Agent 2 : Backend Developer sur `backend/app` et `backend/tests`
- Agent 3 : Frontend Developer sur `frontend`
- Agent 4 : Testeur pour verification et plan de test
- Agent 5 : UX/UI Designer pour cadrage des interactions
- Agent 6 : DevOps/Infra sur `docker-compose.yml`, `.github` et docs

## Recommandations pratiques

- Commencer petit : 2 a 3 agents maximum au debut.
- Donner des perimetres de fichiers disjoints pour eviter les conflits.
- Faire valider le contrat API avant implementation frontend.
- Faire intervenir le testeur des que possible, pas seulement a la fin.
- Demander au Chef de projet une synthese courte apres chaque lot.

## Limites

- Plusieurs agents ne remplacent pas une bonne specification.
- Trop d'agents sur une petite tache ralentissent souvent le travail.
- Si deux agents ecrivent dans les memes fichiers, il faut une coordination explicite.

## Definition de done globale

Une fonctionnalite est consideree terminee si :

- le besoin produit est clair
- l'UX est definie
- le backend fonctionne
- le frontend consomme correctement l'API
- les tests essentiels existent ou les risques residuels sont documentes
- l'execution locale est reproductible
- la documentation utile a ete mise a jour


## Python

* Vérifier que les docstrings sont fournies

