-- ============================
-- TABLE PRINCIPALE : GAMES
-- ============================
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('game', 'extension')),
    extension_of_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
    year INTEGER,
    min_players INTEGER,
    max_players INTEGER,
    min_age INTEGER,
    duration_minutes INTEGER,
    language TEXT,
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
-- UTILISATEURS & LOCALISATIONS
-- ============================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL
);

CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- ============================
-- COLLECTION DES UTILISATEURS
-- ============================
CREATE TABLE collections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    UNIQUE (user_id, game_id)
);