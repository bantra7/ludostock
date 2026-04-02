import { FormEvent, useEffect, useState } from "react";
import {
  emptyToNull,
  getErrorMessage,
  joinNames,
  parseList,
  request,
  toNumberOrNull,
} from "./api";
import {
  defaultGameForm,
  navItems,
  referenceEndpoints,
  referenceTitles,
} from "./types";
import type {
  Game,
  GameFormState,
  NamedEntity,
  NavKey,
  ReferenceCollection,
  ReferenceDrafts,
  ReferenceKey,
} from "./types";

function App() {
  const [activeNav, setActiveNav] = useState<NavKey>("overview");
  const [games, setGames] = useState<Game[]>([]);
  const [references, setReferences] = useState<ReferenceCollection>({
    authors: [],
    artists: [],
    editors: [],
    distributors: [],
  });
  const [referenceDrafts, setReferenceDrafts] = useState<ReferenceDrafts>({
    authors: "",
    artists: "",
    editors: "",
    distributors: "",
  });
  const [gameForm, setGameForm] = useState<GameFormState>(defaultGameForm);
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingGame, setIsSavingGame] = useState(false);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    void loadAllData();
  }, []);

  useEffect(() => {
    if (selectedGameId === null && games.length > 0) {
      setSelectedGameId(games[0].id);
      return;
    }

    if (selectedGameId !== null && !games.some((game) => game.id === selectedGameId)) {
      setSelectedGameId(games[0]?.id ?? null);
    }
  }, [games, selectedGameId]);

  async function loadAllData() {
    setIsLoading(true);
    try {
      const [gamesData, authorsData, artistsData, editorsData, distributorsData] = await Promise.all([
        request<Game[]>("/games/"),
        request<NamedEntity[]>("/authors/"),
        request<NamedEntity[]>("/artists/"),
        request<NamedEntity[]>("/editors/"),
        request<NamedEntity[]>("/distributors/"),
      ]);

      setGames(gamesData);
      setReferences({
        authors: authorsData,
        artists: artistsData,
        editors: editorsData,
        distributors: distributorsData,
      });
      setMessage(null);
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshReferences() {
    const [authorsData, artistsData, editorsData, distributorsData] = await Promise.all([
      request<NamedEntity[]>("/authors/"),
      request<NamedEntity[]>("/artists/"),
      request<NamedEntity[]>("/editors/"),
      request<NamedEntity[]>("/distributors/"),
    ]);

    setReferences({
      authors: authorsData,
      artists: artistsData,
      editors: editorsData,
      distributors: distributorsData,
    });
  }

  async function createReference(kind: ReferenceKey, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = referenceDrafts[kind].trim();
    if (!name) {
      setMessage({ tone: "error", text: `Le nom pour ${referenceTitles[kind].toLowerCase()} est requis.` });
      return;
    }

    try {
      const created = await request<NamedEntity>(`/${referenceEndpoints[kind]}/`, {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      setReferences((current) => ({
        ...current,
        [kind]: [...current[kind], created].sort((left, right) => left.name.localeCompare(right.name)),
      }));
      setReferenceDrafts((current) => ({ ...current, [kind]: "" }));
      setMessage({ tone: "success", text: `${referenceTitles[kind].slice(0, -1)} cree avec succes.` });
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function deleteReference(kind: ReferenceKey, id: number) {
    const item = references[kind].find((entry) => entry.id === id);
    if (!item) {
      return;
    }

    if (!window.confirm(`Supprimer ${item.name} du referentiel ${referenceTitles[kind].toLowerCase()} ?`)) {
      return;
    }

    try {
      await request(`/${referenceEndpoints[kind]}/${id}`, { method: "DELETE" });
      setReferences((current) => ({
        ...current,
        [kind]: current[kind].filter((entry) => entry.id !== id),
      }));
      setGames((current) =>
        current.map((game) => ({
          ...game,
          [kind]: game[kind].filter((entry) => entry.id !== id),
        })),
      );
      setMessage({ tone: "success", text: `${item.name} a ete supprime.` });
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function createGame(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSavingGame(true);

    try {
      const payload = {
        name: gameForm.name.trim(),
        type: gameForm.type.trim(),
        extension_of_id: toNumberOrNull(gameForm.extension_of_id),
        creation_year: toNumberOrNull(gameForm.creation_year),
        min_players: toNumberOrNull(gameForm.min_players),
        max_players: toNumberOrNull(gameForm.max_players),
        min_age: toNumberOrNull(gameForm.min_age),
        duration_minutes: toNumberOrNull(gameForm.duration_minutes),
        url: emptyToNull(gameForm.url),
        image_url: emptyToNull(gameForm.image_url),
        authors: parseList(gameForm.authors),
        artists: parseList(gameForm.artists),
        editors: parseList(gameForm.editors),
        distributors: parseList(gameForm.distributors),
      };

      if (!payload.name || !payload.type) {
        throw new Error("Le nom et le type du jeu sont obligatoires.");
      }

      const createdGame = await request<Game>("/games/", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setGames((current) => [createdGame, ...current]);
      setSelectedGameId(createdGame.id);
      setGameForm(defaultGameForm);
      await refreshReferences();
      setMessage({ tone: "success", text: `${createdGame.name} a ete ajoute au referentiel.` });
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsSavingGame(false);
    }
  }

  async function deleteGame(gameId: number) {
    const game = games.find((entry) => entry.id === gameId);
    if (!game) {
      return;
    }

    if (!window.confirm(`Supprimer le jeu ${game.name} ?`)) {
      return;
    }

    try {
      await request(`/games/${gameId}`, { method: "DELETE" });
      setGames((current) => current.filter((entry) => entry.id !== gameId));
      setMessage({ tone: "success", text: `${game.name} a ete supprime.` });
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    }
  }

  const selectedGame = games.find((game) => game.id === selectedGameId) ?? null;
  const filteredGames = games.filter((game) => {
    const loweredSearch = search.trim().toLowerCase();
    const matchesSearch =
      loweredSearch.length === 0 ||
      game.name.toLowerCase().includes(loweredSearch) ||
      game.authors.some((author) => author.name.toLowerCase().includes(loweredSearch)) ||
      game.editors.some((editor) => editor.name.toLowerCase().includes(loweredSearch));
    const matchesType = typeFilter.length === 0 || game.type === typeFilter;
    const matchesYear =
      yearFilter.length === 0 || String(game.creation_year ?? "").includes(yearFilter.trim());
    return matchesSearch && matchesType && matchesYear;
  });
  const availableTypes = Array.from(new Set(games.map((game) => game.type))).sort();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <p className="brand-title">Ludostock</p>
            <p className="brand-subtitle">Referentiel metier</p>
          </div>
        </div>

        <nav className="nav-list" aria-label="Navigation principale">
          {navItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`nav-item ${activeNav === item.key ? "active" : ""}`}
              onClick={() => setActiveNav(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <h1>Ludostock</h1>
        </header>

        {message ? <section className={`flash flash-${message.tone}`}>{message.text}</section> : null}

        {isLoading ? (
          <section className="loading-card">
            <h2>Chargement du referentiel</h2>
            <p>Recuperation des jeux, auteurs, editeurs et distributeurs depuis FastAPI.</p>
          </section>
        ) : null}

        {!isLoading && activeNav === "overview" ? (
          <OverviewSection
            gameCount={games.length}
            authorCount={references.authors.length}
            artistCount={references.artists.length}
            editorCount={references.editors.length}
            distributorCount={references.distributors.length}
            onOpenSection={setActiveNav}
          />
        ) : null}

        {!isLoading && activeNav === "games" ? (
          <GamesSection
            availableTypes={availableTypes}
            filteredGames={filteredGames}
            gameForm={gameForm}
            isSavingGame={isSavingGame}
            search={search}
            selectedGame={selectedGame}
            typeFilter={typeFilter}
            yearFilter={yearFilter}
            onCreateGame={createGame}
            onDeleteGame={deleteGame}
            onResetGameForm={() => setGameForm(defaultGameForm)}
            onSearchChange={setSearch}
            onSelectGame={setSelectedGameId}
            onTypeFilterChange={setTypeFilter}
            onUpdateGameForm={setGameForm}
            onYearFilterChange={setYearFilter}
          />
        ) : null}

        {!isLoading && ["authors", "artists", "editors", "distributors"].includes(activeNav) ? (
          <EntitiesSection
            activeNav={activeNav as ReferenceKey}
            drafts={referenceDrafts}
            references={references}
            onCreateReference={createReference}
            onDeleteReference={deleteReference}
            onDraftChange={setReferenceDrafts}
          />
        ) : null}
      </main>
    </div>
  );
}

function OverviewSection({
  gameCount,
  authorCount,
  artistCount,
  editorCount,
  distributorCount,
  onOpenSection,
}: {
  gameCount: number;
  authorCount: number;
  artistCount: number;
  editorCount: number;
  distributorCount: number;
  onOpenSection: (nav: NavKey) => void;
}) {
  return (
    <section className="overview-layout">
      <div className="overview-cards">
        <button type="button" className="overview-card accent-coral" onClick={() => onOpenSection("games")}>
          <h3>Jeux</h3>
          <strong>{gameCount} elements</strong>
        </button>
        <button type="button" className="overview-card accent-sage" onClick={() => onOpenSection("authors")}>
          <h3>Auteurs</h3>
          <strong>{authorCount} elements</strong>
        </button>
        <button type="button" className="overview-card accent-rose" onClick={() => onOpenSection("artists")}>
          <h3>Artistes</h3>
          <strong>{artistCount} elements</strong>
        </button>
        <button type="button" className="overview-card accent-sky" onClick={() => onOpenSection("editors")}>
          <h3>Editeurs</h3>
          <strong>{editorCount} elements</strong>
        </button>
        <button type="button" className="overview-card accent-wheat" onClick={() => onOpenSection("distributors")}>
          <h3>Distributeurs</h3>
          <strong>{distributorCount} elements</strong>
        </button>
      </div>
    </section>
  );
}

function GamesSection(props: {
  availableTypes: string[];
  filteredGames: Game[];
  gameForm: GameFormState;
  isSavingGame: boolean;
  search: string;
  selectedGame: Game | null;
  typeFilter: string;
  yearFilter: string;
  onCreateGame: (event: FormEvent<HTMLFormElement>) => void;
  onDeleteGame: (gameId: number) => void;
  onResetGameForm: () => void;
  onSearchChange: (value: string) => void;
  onSelectGame: (gameId: number) => void;
  onTypeFilterChange: (value: string) => void;
  onUpdateGameForm: (updater: (current: GameFormState) => GameFormState) => void;
  onYearFilterChange: (value: string) => void;
}) {
  const {
    availableTypes,
    filteredGames,
    gameForm,
    isSavingGame,
    search,
    selectedGame,
    typeFilter,
    yearFilter,
    onCreateGame,
    onDeleteGame,
    onResetGameForm,
    onSearchChange,
    onSelectGame,
    onTypeFilterChange,
    onUpdateGameForm,
    onYearFilterChange,
  } = props;

  return (
    <section className="games-layout">
      <div className="games-main">
        <section className="section-intro">
          <p className="eyebrow">Gestion des jeux</p>
          <h2>Liste, detail et creation</h2>
          <p>Le formulaire suit le payload GameCreate du backend, avec contributeurs par noms.</p>
        </section>

        <section className="filter-bar">
          <label className="field">
            <span>Recherche locale</span>
            <input value={search} onChange={(event) => onSearchChange(event.target.value)} placeholder="Nom, auteur ou editeur" />
          </label>

          <label className="field">
            <span>Type</span>
            <select value={typeFilter} onChange={(event) => onTypeFilterChange(event.target.value)}>
              <option value="">Tous</option>
              {availableTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>

          <label className="field field-small">
            <span>Annee</span>
            <input value={yearFilter} onChange={(event) => onYearFilterChange(event.target.value)} placeholder="1995" />
          </label>
        </section>

        <section className="panel panel-table">
          <div className="table-head">
            <div>Nom</div>
            <div>Type</div>
            <div>Auteurs</div>
            <div>Editeurs</div>
            <div>Actions</div>
          </div>

          <div className="table-body">
            {filteredGames.length === 0 ? (
              <div className="empty-state">
                <h3>Aucun jeu visible</h3>
                <p>Affinez moins les filtres ou creez un nouveau jeu depuis le formulaire.</p>
              </div>
            ) : (
              filteredGames.map((game) => (
                <div key={game.id} className="table-row">
                  <button type="button" className="table-link" onClick={() => onSelectGame(game.id)}>
                    {game.name}
                  </button>
                  <div>{game.type}</div>
                  <div>{joinNames(game.authors)}</div>
                  <div>{joinNames(game.editors)}</div>
                  <div className="row-actions">
                    <button type="button" className="link-button" onClick={() => onSelectGame(game.id)}>
                      Voir
                    </button>
                    <button type="button" className="link-button danger" onClick={() => onDeleteGame(game.id)}>
                      Supprimer
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="panel panel-form">
          <div className="section-intro compact">
            <p className="eyebrow">Creation d'un jeu</p>
            <h2>Nouveau jeu</h2>
            <p>Les listes de contributeurs acceptent des noms separes par des virgules.</p>
          </div>

          <form className="game-form" onSubmit={onCreateGame}>
            <div className="form-grid">
              <Field label="Nom du jeu" wide>
                <input
                  value={gameForm.name}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="Terraforming Mars"
                />
              </Field>

              <Field label="Type">
                <select
                  value={gameForm.type}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, type: event.target.value }))}
                >
                  <option value="Jeu de base">Jeu de base</option>
                  <option value="Extension">Extension</option>
                  <option value="Accessoire">Accessoire</option>
                </select>
              </Field>

              <Field label="Extension de (id)">
                <input
                  value={gameForm.extension_of_id}
                  onChange={(event) =>
                    onUpdateGameForm((current) => ({ ...current, extension_of_id: event.target.value }))
                  }
                  placeholder="Laisser vide"
                />
              </Field>

              <Field label="Annee">
                <input
                  value={gameForm.creation_year}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, creation_year: event.target.value }))}
                  placeholder="2016"
                />
              </Field>

              <Field label="Joueurs min">
                <input
                  value={gameForm.min_players}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, min_players: event.target.value }))}
                  placeholder="1"
                />
              </Field>

              <Field label="Joueurs max">
                <input
                  value={gameForm.max_players}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, max_players: event.target.value }))}
                  placeholder="5"
                />
              </Field>

              <Field label="Age min">
                <input
                  value={gameForm.min_age}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, min_age: event.target.value }))}
                  placeholder="12"
                />
              </Field>

              <Field label="Duree (minutes)">
                <input
                  value={gameForm.duration_minutes}
                  onChange={(event) =>
                    onUpdateGameForm((current) => ({ ...current, duration_minutes: event.target.value }))
                  }
                  placeholder="120"
                />
              </Field>

              <Field label="URL fiche" wide>
                <input
                  value={gameForm.url}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, url: event.target.value }))}
                  placeholder="https://..."
                />
              </Field>

              <Field label="URL image" wide>
                <input
                  value={gameForm.image_url}
                  onChange={(event) =>
                    onUpdateGameForm((current) => ({ ...current, image_url: event.target.value }))
                  }
                  placeholder="https://..."
                />
              </Field>

              <Field label="Auteurs" wide>
                <input
                  value={gameForm.authors}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, authors: event.target.value }))}
                  placeholder="Bruno Cathala, Antoine Bauza"
                />
              </Field>

              <Field label="Artistes" wide>
                <input
                  value={gameForm.artists}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, artists: event.target.value }))}
                  placeholder="Optionnel"
                />
              </Field>

              <Field label="Editeurs" wide>
                <input
                  value={gameForm.editors}
                  onChange={(event) => onUpdateGameForm((current) => ({ ...current, editors: event.target.value }))}
                  placeholder="Repos Production, Space Cowboys"
                />
              </Field>

              <Field label="Distributeurs" wide>
                <input
                  value={gameForm.distributors}
                  onChange={(event) =>
                    onUpdateGameForm((current) => ({ ...current, distributors: event.target.value }))
                  }
                  placeholder="Asmodee"
                />
              </Field>
            </div>

            <div className="form-actions">
              <button type="button" className="secondary-button" onClick={onResetGameForm}>
                Reinitialiser
              </button>
              <button type="submit" className="primary-button" disabled={isSavingGame}>
                {isSavingGame ? "Creation..." : "Creer le jeu"}
              </button>
            </div>
          </form>
        </section>
      </div>

      <aside className="detail-panel">
        <div className="section-intro compact">
          <p className="eyebrow">Detail</p>
          <h2>{selectedGame ? selectedGame.name : "Selectionner un jeu"}</h2>
          <p>{selectedGame ? "GET /api/games/{id}" : "Choisissez une ligne dans la liste."}</p>
        </div>

        {selectedGame ? (
          <div className="detail-content">
            <DetailField label="Type" value={selectedGame.type} />
            <DetailField label="Annee" value={selectedGame.creation_year ?? "-"} />
            <DetailField
              label="Joueurs"
              value={
                selectedGame.min_players && selectedGame.max_players
                  ? `${selectedGame.min_players} - ${selectedGame.max_players}`
                  : "-"
              }
            />
            <DetailField label="Age minimum" value={selectedGame.min_age ?? "-"} />
            <DetailField label="Duree" value={selectedGame.duration_minutes ? `${selectedGame.duration_minutes} min` : "-"} />

            <ChipsSection label="Auteurs" items={selectedGame.authors} emptyLabel="Aucun auteur" />
            <ChipsSection label="Artistes" items={selectedGame.artists} emptyLabel="Aucun artiste" />
            <ChipsSection label="Editeurs" items={selectedGame.editors} emptyLabel="Aucun editeur" />
            <ChipsSection label="Distributeurs" items={selectedGame.distributors} emptyLabel="Aucun distributeur" />

            <div className="detail-links">
              {selectedGame.url ? (
                <a href={selectedGame.url} target="_blank" rel="noreferrer">
                  Ouvrir la fiche
                </a>
              ) : null}
              {selectedGame.image_url ? (
                <a href={selectedGame.image_url} target="_blank" rel="noreferrer">
                  Ouvrir l'image
                </a>
              ) : null}
            </div>

            <button type="button" className="danger-button" onClick={() => onDeleteGame(selectedGame.id)}>
              Supprimer le jeu
            </button>
          </div>
        ) : (
          <div className="empty-state">
            <h3>Aucun jeu selectionne</h3>
            <p>La vue detail s'aligne sur le endpoint de lecture unitaire du backend.</p>
          </div>
        )}
      </aside>
    </section>
  );
}

function EntitiesSection(props: {
  activeNav: ReferenceKey;
  drafts: ReferenceDrafts;
  references: ReferenceCollection;
  onCreateReference: (kind: ReferenceKey, event: FormEvent<HTMLFormElement>) => Promise<void>;
  onDeleteReference: (kind: ReferenceKey, id: number) => Promise<void>;
  onDraftChange: (updater: (current: ReferenceDrafts) => ReferenceDrafts) => void;
}) {
  const { activeNav, drafts, references, onCreateReference, onDeleteReference, onDraftChange } = props;

  return (
    <section className="entities-layout">
      <section className="section-intro">
        <h2>Referentiels</h2>
      </section>

      <div className="entity-grid">
        {(["authors", "artists", "editors", "distributors"] as ReferenceKey[]).map((kind) => (
          <section key={kind} className={`panel entity-panel ${activeNav === kind ? "entity-panel-active" : ""}`}>
            <div className="section-intro compact">
              <p className="eyebrow">{referenceEndpoints[kind].toUpperCase()}</p>
              <h2>{referenceTitles[kind]}</h2>
              <p>POST / GET / DELETE</p>
            </div>

            <form className="entity-form" onSubmit={(event) => void onCreateReference(kind, event)}>
              <Field label="Nouveau nom">
                <input
                  value={drafts[kind]}
                  onChange={(event) => onDraftChange((current) => ({ ...current, [kind]: event.target.value }))}
                  placeholder={`Ajouter un ${referenceTitles[kind].slice(0, -1).toLowerCase()}`}
                />
              </Field>
              <button type="submit" className="primary-button">
                Ajouter
              </button>
            </form>

            <div className="simple-table">
              <div className="simple-head">
                <span>ID</span>
                <span>Nom</span>
                <span>Action</span>
              </div>

              {references[kind].length === 0 ? (
                <div className="empty-state compact">
                  <h3>Referentiel vide</h3>
                  <p>Le backend renverra ici la liste paginee par defaut.</p>
                </div>
              ) : (
                references[kind].map((item) => (
                  <div key={item.id} className="simple-row">
                    <span>{item.id}</span>
                    <span>{item.name}</span>
                    <button type="button" className="link-button danger" onClick={() => void onDeleteReference(kind, item.id)}>
                      Supprimer
                    </button>
                  </div>
                ))
              )}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}

function Field({
  children,
  label,
  wide = false,
}: {
  children: React.ReactNode;
  label: string;
  wide?: boolean;
}) {
  return (
    <label className={`field ${wide ? "field-wide" : ""}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function DetailField({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="detail-field">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ChipsSection({
  emptyLabel,
  items,
  label,
}: {
  emptyLabel: string;
  items: NamedEntity[];
  label: string;
}) {
  return (
    <div className="chips-group">
      <p className="chips-title">{label}</p>
      {items.length === 0 ? (
        <p className="empty-inline">{emptyLabel}</p>
      ) : (
        <div className="chips-wrap">
          {items.map((item) => (
            <span key={item.id} className="chip">
              {item.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
