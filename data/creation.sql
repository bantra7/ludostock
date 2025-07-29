-- ============================
-- TABLE PRINCIPALE : GAMES (Catalogue global)
-- ============================
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('game', 'extension')),
    extension_of_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
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
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE artists (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE editors (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE distributors (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- ============================
-- RELATIONS N-N
-- ============================
CREATE TABLE game_authors (
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, author_id)
);

CREATE TABLE game_artists (
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    artist_id INTEGER REFERENCES artists(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, artist_id)
);

CREATE TABLE game_editors (
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    editor_id INTEGER REFERENCES editors(id) ON DELETE CASCADE,
    PRIMARY KEY (game_id, editor_id)
);

CREATE TABLE game_distributors (
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    distributor_id INTEGER REFERENCES distributors(id) ON DELETE CASCADE,
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
    id SERIAL PRIMARY KEY,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT
);

-- ============================
-- PARTAGE DE COLLECTIONS
-- ============================
CREATE TABLE collection_shares (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    shared_with UUID REFERENCES users(id) ON DELETE CASCADE,
    permission TEXT NOT NULL CHECK (permission IN ('read', 'write')),
    UNIQUE (collection_id, shared_with)
);

-- ============================
-- LIEUX (propres à chaque utilisateur)
-- ============================
CREATE TABLE user_locations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    UNIQUE (user_id, name)
);

-- ============================
-- JEUX DANS UNE COLLECTION
-- ============================
CREATE TABLE collection_games (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES user_locations(id) ON DELETE SET NULL,
    quantity INTEGER DEFAULT 1,
    UNIQUE (collection_id, game_id, location_id)
);
