-- ============================
-- SEQUENCES POUR AUTO-INCREMENT
-- ============================
CREATE SEQUENCE games_seq;
CREATE SEQUENCE authors_seq;
CREATE SEQUENCE artists_seq;
CREATE SEQUENCE editors_seq;
CREATE SEQUENCE distributors_seq;
CREATE SEQUENCE users_seq;
CREATE SEQUENCE collections_seq;
CREATE SEQUENCE collection_shares_seq;
CREATE SEQUENCE user_locations_seq;
CREATE SEQUENCE collection_games_seq;

-- ============================
-- TABLE PRINCIPALE : GAMES (Catalogue global)
-- ============================
CREATE TABLE games (
    id INTEGER PRIMARY KEY DEFAULT nextval('games_seq'),
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('game', 'extension')),
    extension_of_id INTEGER REFERENCES games(id),
    creation_year INTEGER,
    min_players INTEGER,
    max_players INTEGER,
    min_age INTEGER,
    duration_minutes INTEGER,
    url TEXT,
    image_url TEXT
);

-- ============================
-- TABLES LIÉES : AUTEURS, ARTISTES, ÉDITEURS, DISTRIBUTEURS
-- ============================
CREATE TABLE authors (
    id INTEGER PRIMARY KEY DEFAULT nextval('authors_seq'),
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE artists (
    id INTEGER PRIMARY KEY DEFAULT nextval('artists_seq'),
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE editors (
    id INTEGER PRIMARY KEY DEFAULT nextval('editors_seq'),
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE distributors (
    id INTEGER PRIMARY KEY DEFAULT nextval('distributors_seq'),
    name TEXT UNIQUE NOT NULL
);

-- ============================
-- RELATIONS N-N
-- ============================
CREATE TABLE game_authors (
    game_id INTEGER REFERENCES games(id),
    author_id INTEGER REFERENCES authors(id),
    PRIMARY KEY (game_id, author_id)
);

CREATE TABLE game_artists (
    game_id INTEGER REFERENCES games(id),
    artist_id INTEGER REFERENCES artists(id),
    PRIMARY KEY (game_id, artist_id)
);

CREATE TABLE game_editors (
    game_id INTEGER REFERENCES games(id),
    editor_id INTEGER REFERENCES editors(id),
    PRIMARY KEY (game_id, editor_id)
);

CREATE TABLE game_distributors (
    game_id INTEGER REFERENCES games(id),
    distributor_id INTEGER REFERENCES distributors(id),
    PRIMARY KEY (game_id, distributor_id)
);

-- ============================
-- UTILISATEURS (Google Auth via Supabase)
-- ============================
CREATE TABLE users (
    id UUID PRIMARY KEY, -- ID fourni par Supabase Auth
    email TEXT UNIQUE NOT NULL,
    username TEXT
);

-- ============================
-- COLLECTIONS DES UTILISATEURS
-- ============================
CREATE TABLE collections (
    id INTEGER PRIMARY KEY DEFAULT nextval('collections_seq'),
    owner_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT
);

-- ============================
-- PARTAGE DE COLLECTIONS
-- ============================
CREATE TABLE collection_shares (
    id INTEGER PRIMARY KEY DEFAULT nextval('collection_shares_seq'),
    collection_id INTEGER REFERENCES collections(id),
    shared_with UUID REFERENCES users(id),
    permission TEXT NOT NULL CHECK (permission IN ('read', 'write')),
    UNIQUE (collection_id, shared_with)
);

-- ============================
-- LIEUX (propres à chaque utilisateur)
-- ============================
CREATE TABLE user_locations (
    id INTEGER PRIMARY KEY DEFAULT nextval('user_locations_seq'),
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    UNIQUE (user_id, name)
);

-- ============================
-- JEUX DANS UNE COLLECTION
-- ============================
CREATE TABLE collection_games (
    id INTEGER PRIMARY KEY DEFAULT nextval('collection_games_seq'),
    collection_id INTEGER REFERENCES collections(id),
    game_id INTEGER REFERENCES games(id),
    location_id INTEGER REFERENCES user_locations(id),
    quantity INTEGER DEFAULT 1,
    UNIQUE (collection_id, game_id, location_id)
);