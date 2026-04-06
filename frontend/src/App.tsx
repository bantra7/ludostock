import { FormEvent, useDeferredValue, useEffect, useState } from "react";
import { getErrorMessage, joinNames, request, requestAllPages } from "./api";
import { navItems, referenceEndpoints, referenceTitles } from "./types";
import type {
  Game,
  GamePage,
  NamedEntity,
  NavKey,
  ReferenceCollection,
  ReferenceDrafts,
  ReferenceKey,
} from "./types";

const GAME_PAGE_SIZE = 50;

function App() {
  const [activeNav, setActiveNav] = useState<NavKey>("overview");
  const [games, setGames] = useState<Game[]>([]);
  const [catalogGameCount, setCatalogGameCount] = useState(0);
  const [totalGames, setTotalGames] = useState(0);
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
  const [isGamesLoading, setIsGamesLoading] = useState(true);
  const [areReferencesLoading, setAreReferencesLoading] = useState(true);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");
  const [playerFilter, setPlayerFilter] = useState("all");
  const [durationFilter, setDurationFilter] = useState("all");
  const [authorFilter, setAuthorFilter] = useState("");
  const [artistFilter, setArtistFilter] = useState("");
  const [editorFilter, setEditorFilter] = useState("");
  const [distributorFilter, setDistributorFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [gamesRefreshToken, setGamesRefreshToken] = useState(0);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const deferredSearch = useDeferredValue(search);
  const deferredYearFilter = useDeferredValue(yearFilter);

  useEffect(() => {
    void loadReferenceData();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [deferredSearch, typeFilter, deferredYearFilter]);

  useEffect(() => {
    void loadGamesPage(currentPage);
  }, [currentPage, deferredSearch, typeFilter, deferredYearFilter, gamesRefreshToken]);

  useEffect(() => {
    if (!hasLoadedOnce && !isGamesLoading && !areReferencesLoading) {
      setHasLoadedOnce(true);
    }
  }, [areReferencesLoading, hasLoadedOnce, isGamesLoading]);

  async function loadReferenceData() {
    setAreReferencesLoading(true);
    try {
      const [authorsData, artistsData, editorsData, distributorsData] = await Promise.all([
        requestAllPages<NamedEntity>("/authors/"),
        requestAllPages<NamedEntity>("/artists/"),
        requestAllPages<NamedEntity>("/editors/"),
        requestAllPages<NamedEntity>("/distributors/"),
      ]);

      setReferences({
        authors: authorsData,
        artists: artistsData,
        editors: editorsData,
        distributors: distributorsData,
      });
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setAreReferencesLoading(false);
    }
  }

  async function loadGamesPage(pageNumber: number) {
    setIsGamesLoading(true);
    try {
      const params = new URLSearchParams({
        skip: String((pageNumber - 1) * GAME_PAGE_SIZE),
        limit: String(GAME_PAGE_SIZE),
      });

      if (deferredSearch.trim()) {
        params.set("search", deferredSearch.trim());
      }

      if (typeFilter.trim()) {
        params.set("type", typeFilter.trim());
      }

      if (deferredYearFilter.trim()) {
        params.set("year", deferredYearFilter.trim());
      }

      const page = await request<GamePage>(`/games/?${params.toString()}`);
      if (page.items.length === 0 && page.total > 0 && page.skip >= page.total) {
        setCurrentPage(Math.max(1, Math.ceil(page.total / GAME_PAGE_SIZE)));
        return;
      }

      setGames(page.items);
      setTotalGames(page.total);
      if (!deferredSearch.trim() && !typeFilter.trim() && !deferredYearFilter.trim()) {
        setCatalogGameCount(page.total);
      }
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsGamesLoading(false);
    }
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
      setGamesRefreshToken((current) => current + 1);
      setMessage({ tone: "success", text: `${game.name} a ete supprime.` });
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    }
  }

  const availableTypes = Array.from(new Set([...games.map((game) => game.type), typeFilter].filter(Boolean))).sort();
  const totalPages = Math.max(1, Math.ceil(totalGames / GAME_PAGE_SIZE));
  const pageStart = totalGames === 0 ? 0 : (currentPage - 1) * GAME_PAGE_SIZE + 1;
  const pageEnd = totalGames === 0 ? 0 : Math.min(currentPage * GAME_PAGE_SIZE, totalGames);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <p className="brand-title">Ludostock</p>
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

        {!hasLoadedOnce ? (
          <section className="loading-card">
            <h2>Chargement du referentiel</h2>
            <p>Recuperation des jeux, auteurs, editeurs et distributeurs depuis FastAPI.</p>
          </section>
        ) : null}

        {hasLoadedOnce && activeNav === "overview" ? (
          <OverviewSection
            gameCount={catalogGameCount || totalGames}
            authorCount={references.authors.length}
            artistCount={references.artists.length}
            editorCount={references.editors.length}
            distributorCount={references.distributors.length}
            onOpenSection={setActiveNav}
          />
        ) : null}

        {hasLoadedOnce && activeNav === "games" ? (
          <GamesSection
            availableTypes={availableTypes}
            artistFilter={artistFilter}
            authorFilter={authorFilter}
            currentPage={currentPage}
            distributorFilter={distributorFilter}
            durationFilter={durationFilter}
            editorFilter={editorFilter}
            games={games}
            isGamesLoading={isGamesLoading}
            pageEnd={pageEnd}
            pageStart={pageStart}
            playerFilter={playerFilter}
            search={search}
            totalGames={totalGames}
            totalPages={totalPages}
            typeFilter={typeFilter}
            yearFilter={yearFilter}
            onArtistFilterChange={setArtistFilter}
            onAuthorFilterChange={setAuthorFilter}
            onDeleteGame={deleteGame}
            onDistributorFilterChange={setDistributorFilter}
            onPageChange={setCurrentPage}
            onDurationFilterChange={setDurationFilter}
            onEditorFilterChange={setEditorFilter}
            onSearchChange={setSearch}
            onPlayerFilterChange={setPlayerFilter}
            onResetFilters={() => {
              setSearch("");
              setTypeFilter("");
              setYearFilter("");
              setPlayerFilter("all");
              setDurationFilter("all");
              setAuthorFilter("");
              setArtistFilter("");
              setEditorFilter("");
              setDistributorFilter("");
              setCurrentPage(1);
            }}
            onTypeFilterChange={setTypeFilter}
            onYearFilterChange={setYearFilter}
          />
        ) : null}

        {hasLoadedOnce && ["authors", "artists", "editors", "distributors"].includes(activeNav) ? (
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
  artistFilter: string;
  authorFilter: string;
  currentPage: number;
  distributorFilter: string;
  durationFilter: string;
  editorFilter: string;
  games: Game[];
  isGamesLoading: boolean;
  pageEnd: number;
  pageStart: number;
  playerFilter: string;
  search: string;
  totalGames: number;
  totalPages: number;
  typeFilter: string;
  yearFilter: string;
  onArtistFilterChange: (value: string) => void;
  onAuthorFilterChange: (value: string) => void;
  onDeleteGame: (gameId: number) => void;
  onDistributorFilterChange: (value: string) => void;
  onDurationFilterChange: (value: string) => void;
  onEditorFilterChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onPlayerFilterChange: (value: string) => void;
  onResetFilters: () => void;
  onSearchChange: (value: string) => void;
  onTypeFilterChange: (value: string) => void;
  onYearFilterChange: (value: string) => void;
}) {
  const [hoveredGameId, setHoveredGameId] = useState<number | null>(null);
  const {
    availableTypes,
    artistFilter,
    authorFilter,
    currentPage,
    distributorFilter,
    durationFilter,
    editorFilter,
    games,
    isGamesLoading,
    pageEnd,
    pageStart,
    playerFilter,
    search,
    totalGames,
    totalPages,
    typeFilter,
    yearFilter,
    onArtistFilterChange,
    onAuthorFilterChange,
    onDeleteGame,
    onDistributorFilterChange,
    onDurationFilterChange,
    onEditorFilterChange,
    onPageChange,
    onPlayerFilterChange,
    onResetFilters,
    onSearchChange,
    onTypeFilterChange,
    onYearFilterChange,
  } = props;
  const filteredGames = games.filter((game) => {
    if (!matchesPlayerFilter(game, playerFilter)) {
      return false;
    }
    if (!matchesDurationFilter(game, durationFilter)) {
      return false;
    }
    if (!matchesOccurrenceFilter(game.authors, authorFilter)) {
      return false;
    }
    if (!matchesOccurrenceFilter(game.artists, artistFilter)) {
      return false;
    }
    if (!matchesOccurrenceFilter(game.editors, editorFilter)) {
      return false;
    }
    if (!matchesOccurrenceFilter(game.distributors, distributorFilter)) {
      return false;
    }
    return true;
  });
  const visibleCount = filteredGames.length;
  const loadedCount = games.length;
  const hasAdvancedFilters =
    playerFilter !== "all" ||
    durationFilter !== "all" ||
    Boolean(authorFilter.trim()) ||
    Boolean(artistFilter.trim()) ||
    Boolean(editorFilter.trim()) ||
    Boolean(distributorFilter.trim());

  return (
    <section className="games-layout">
      <section className="games-main">
        <section className="games-toolbar panel">
          <div className="section-intro">
            <h2>Jeux</h2>
            <p>Liste paginee du catalogue avec filtres serveur puis filtres rapides sur la page chargee.</p>
          </div>

          <div className="games-summary">
            <div className="summary-pill">
              <strong>{visibleCount}</strong>
              <span>visibles</span>
            </div>
            <div className="summary-pill">
              <strong>{loadedCount}</strong>
              <span>charges</span>
            </div>
            <div className="summary-pill">
              <strong>{totalGames}</strong>
              <span>resultats</span>
            </div>
          </div>
        </section>

        <section className="filter-bar panel">
          <label className="field">
            <span>Recherche serveur</span>
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

          <label className="field">
            <span>Joueurs</span>
            <select value={playerFilter} onChange={(event) => onPlayerFilterChange(event.target.value)}>
              <option value="all">Tous</option>
              <option value="solo">Solo possible</option>
              <option value="duo">Jouable a 2</option>
              <option value="group">Jouable a 4+</option>
              <option value="party">Grand groupe 6+</option>
            </select>
          </label>

          <label className="field">
            <span>Duree</span>
            <select value={durationFilter} onChange={(event) => onDurationFilterChange(event.target.value)}>
              <option value="all">Toutes</option>
              <option value="short">30 min ou moins</option>
              <option value="medium">31 a 60 min</option>
              <option value="long">61 a 120 min</option>
              <option value="epic">Plus de 120 min</option>
              <option value="unknown">Non renseignee</option>
            </select>
          </label>

          <label className="field">
            <span>Auteur contient</span>
            <input
              value={authorFilter}
              onChange={(event) => onAuthorFilterChange(event.target.value)}
              placeholder="Knizia"
            />
          </label>

          <label className="field">
            <span>Artiste contient</span>
            <input
              value={artistFilter}
              onChange={(event) => onArtistFilterChange(event.target.value)}
              placeholder="Mujunsha"
            />
          </label>

          <label className="field">
            <span>Editeur contient</span>
            <input
              value={editorFilter}
              onChange={(event) => onEditorFilterChange(event.target.value)}
              placeholder="Asmodee"
            />
          </label>

          <label className="field">
            <span>Distributeur contient</span>
            <input
              value={distributorFilter}
              onChange={(event) => onDistributorFilterChange(event.target.value)}
              placeholder="Pixie"
            />
          </label>

          <div className="filter-actions">
            <button type="button" className="secondary-button" onClick={onResetFilters}>
              Reinitialiser
            </button>
          </div>
        </section>

        <section className="panel panel-form">
          <div className="section-intro compact">
            <h2>
              {totalGames === 0
                ? "Aucun resultat"
                : `${pageStart}-${pageEnd} sur ${totalGames}`}
            </h2>
            <p>
              {hasAdvancedFilters
                ? `${visibleCount} jeux correspondent aux filtres rapides sur cette page.`
                : "Tous les jeux charges sur cette page sont affiches."}
            </p>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="secondary-button"
              disabled={currentPage <= 1 || isGamesLoading}
              onClick={() => onPageChange(currentPage - 1)}
            >
              Page precedente
            </button>
            <span>
              Page {currentPage} / {totalPages}
            </span>
            <button
              type="button"
              className="secondary-button"
              disabled={currentPage >= totalPages || isGamesLoading}
              onClick={() => onPageChange(currentPage + 1)}
            >
              Page suivante
            </button>
          </div>
        </section>

        <section className="panel panel-table">
          <div className="table-head">
            <div>Nom</div>
            <div>Type</div>
            <div>Annee</div>
            <div>Joueurs</div>
            <div>Duree</div>
            <div>Auteurs</div>
            <div>Editeurs</div>
            <div>Actions</div>
          </div>

          <div className="table-body">
            {isGamesLoading ? (
              <div className="empty-state">
                <h3>Chargement</h3>
              </div>
            ) : games.length === 0 ? (
              <div className="empty-state">
                <h3>Aucun jeu</h3>
              </div>
            ) : filteredGames.length === 0 ? (
              <div className="empty-state">
                <h3>Aucun jeu ne correspond aux filtres rapides</h3>
              </div>
            ) : (
              filteredGames.map((game) => (
                <div key={game.id} className="table-row">
                  <div
                    className="table-name-cell"
                    onMouseEnter={() => setHoveredGameId(game.id)}
                    onMouseLeave={() => setHoveredGameId((current) => (current === game.id ? null : current))}
                  >
                    {game.url ? (
                      <a
                        href={game.url}
                        target="_blank"
                        rel="noreferrer"
                        className="table-link"
                        onFocus={() => setHoveredGameId(game.id)}
                        onBlur={() => setHoveredGameId((current) => (current === game.id ? null : current))}
                      >
                        {game.name}
                      </a>
                    ) : (
                      <span className="table-link table-link-static">{game.name}</span>
                    )}
                    <GameHoverCard game={game} isVisible={hoveredGameId === game.id} />
                  </div>
                  <div>{game.type}</div>
                  <div>{game.creation_year ?? "-"}</div>
                  <div>{formatPlayers(game)}</div>
                  <div>{formatDuration(game.duration_minutes)}</div>
                  <div>{joinNames(game.authors)}</div>
                  <div>{joinNames(game.editors)}</div>
                  <div className="row-actions">
                    <button type="button" className="link-button danger" onClick={() => onDeleteGame(game.id)}>
                      Supprimer
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </section>
    </section>
  );
}

function GameHoverCard({ game, isVisible }: { game: Game; isVisible: boolean }) {
  const playerCount =
    game.min_players !== null && game.max_players !== null
      ? `${game.min_players}-${game.max_players} joueurs`
      : null;
  const meta = [game.creation_year ?? null, playerCount, game.duration_minutes ? `${game.duration_minutes} min` : null]
    .filter(Boolean)
    .join(" / ");

  return (
    <div className={`game-hover-card ${isVisible ? "is-visible" : ""}`} aria-hidden={!isVisible}>
      <div className="game-hover-media">
        {game.image_url ? (
          <img src={game.image_url} alt={game.name} loading="lazy" />
        ) : (
          <div className="game-hover-fallback">{game.name.slice(0, 1).toUpperCase()}</div>
        )}
      </div>
      <div className="game-hover-body">
        <p className="game-hover-type">{game.type}</p>
        <h3>{game.name}</h3>
        {meta ? <p className="game-hover-meta">{meta}</p> : null}
      </div>
    </div>
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

function formatPlayers(game: Game) {
  if (game.min_players !== null && game.max_players !== null) {
    return `${game.min_players}-${game.max_players}`;
  }
  if (game.min_players !== null) {
    return `${game.min_players}+`;
  }
  if (game.max_players !== null) {
    return `jusqu'a ${game.max_players}`;
  }
  return "-";
}

function formatDuration(duration: number | null) {
  return duration ? `${duration} min` : "-";
}

function matchesPlayerFilter(game: Game, filter: string) {
  if (filter === "all") {
    return true;
  }

  if (filter === "solo") {
    return game.min_players !== null && game.min_players <= 1;
  }

  if (filter === "duo") {
    return game.min_players !== null && game.max_players !== null && game.min_players <= 2 && game.max_players >= 2;
  }

  if (filter === "group") {
    return game.max_players !== null && game.max_players >= 4;
  }

  if (filter === "party") {
    return game.max_players !== null && game.max_players >= 6;
  }

  return true;
}

function matchesDurationFilter(game: Game, filter: string) {
  if (filter === "all") {
    return true;
  }

  if (filter === "unknown") {
    return game.duration_minutes === null;
  }

  if (game.duration_minutes === null) {
    return false;
  }

  if (filter === "short") {
    return game.duration_minutes <= 30;
  }

  if (filter === "medium") {
    return game.duration_minutes >= 31 && game.duration_minutes <= 60;
  }

  if (filter === "long") {
    return game.duration_minutes >= 61 && game.duration_minutes <= 120;
  }

  if (filter === "epic") {
    return game.duration_minutes > 120;
  }

  return true;
}

function matchesOccurrenceFilter(items: NamedEntity[], filter: string) {
  const query = filter.trim().toLocaleLowerCase();
  if (!query) {
    return true;
  }
  return items.some((item) => item.name.toLocaleLowerCase().includes(query));
}

export default App;
