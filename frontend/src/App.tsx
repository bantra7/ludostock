import { FormEvent, useDeferredValue, useEffect, useState } from "react";
import { getErrorMessage, joinNames, request } from "./api";
import { navItems, referenceEndpoints, referenceNavItems, referenceTitles } from "./types";
import type {
  Game,
  GamePage,
  NamedEntity,
  NavKey,
  ReferenceCollection,
  ReferenceDrafts,
  ReferenceKey,
} from "./types";

const DEFAULT_GAME_PAGE_SIZE = 50;
const REFERENCE_PAGE_SIZE = 25;
const GAME_PAGE_SIZE_OPTIONS = [50, 100, 200] as const;
const GAME_SORT_OPTIONS = [
  { value: "name:asc", label: "Nom (A-Z)", sortBy: "name", sortDir: "asc" },
  { value: "name:desc", label: "Nom (Z-A)", sortBy: "name", sortDir: "desc" },
  { value: "type:asc", label: "Type (A-Z)", sortBy: "type", sortDir: "asc" },
  { value: "type:desc", label: "Type (Z-A)", sortBy: "type", sortDir: "desc" },
  { value: "creation_year:asc", label: "Annee (croissante)", sortBy: "creation_year", sortDir: "asc" },
  { value: "creation_year:desc", label: "Annee (decroissante)", sortBy: "creation_year", sortDir: "desc" },
  { value: "players:asc", label: "Joueurs (croissant)", sortBy: "players", sortDir: "asc" },
  { value: "players:desc", label: "Joueurs (decroissant)", sortBy: "players", sortDir: "desc" },
  { value: "duration_minutes:asc", label: "Duree (croissante)", sortBy: "duration_minutes", sortDir: "asc" },
  { value: "duration_minutes:desc", label: "Duree (decroissante)", sortBy: "duration_minutes", sortDir: "desc" },
  { value: "authors:asc", label: "Auteurs (A-Z)", sortBy: "authors", sortDir: "asc" },
  { value: "authors:desc", label: "Auteurs (Z-A)", sortBy: "authors", sortDir: "desc" },
  { value: "editors:asc", label: "Editeurs (A-Z)", sortBy: "editors", sortDir: "asc" },
  { value: "editors:desc", label: "Editeurs (Z-A)", sortBy: "editors", sortDir: "desc" },
] as const;

type GameSortValue = (typeof GAME_SORT_OPTIONS)[number]["value"];

function createReferenceNumberMap(initialValue: number) {
  return {
    authors: initialValue,
    artists: initialValue,
    editors: initialValue,
    distributors: initialValue,
  };
}

function createReferenceBooleanMap(initialValue: boolean) {
  return {
    authors: initialValue,
    artists: initialValue,
    editors: initialValue,
    distributors: initialValue,
  };
}

function App() {
  const [activeNav, setActiveNav] = useState<NavKey>("games");
  const [activeReference, setActiveReference] = useState<ReferenceKey | null>(null);
  const [games, setGames] = useState<Game[]>([]);
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
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);
  const [referencePages, setReferencePages] = useState(() => createReferenceNumberMap(1));
  const [referenceHasNext, setReferenceHasNext] = useState(() => createReferenceBooleanMap(false));
  const [referenceLoading, setReferenceLoading] = useState(() => createReferenceBooleanMap(false));
  const [referenceLoaded, setReferenceLoaded] = useState(() => createReferenceBooleanMap(false));
  const [search, setSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [gamePageSize, setGamePageSize] = useState<number>(DEFAULT_GAME_PAGE_SIZE);
  const [gameSort, setGameSort] = useState<GameSortValue>("name:asc");
  const [gamesRefreshToken, setGamesRefreshToken] = useState(0);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const deferredSearch = useDeferredValue(search);

  useEffect(() => {
    setCurrentPage(1);
  }, [deferredSearch, gamePageSize, gameSort]);

  useEffect(() => {
    void loadGamesPage(currentPage);
  }, [currentPage, deferredSearch, gamePageSize, gameSort, gamesRefreshToken]);

  useEffect(() => {
    if (!hasLoadedOnce && !isGamesLoading) {
      setHasLoadedOnce(true);
    }
  }, [hasLoadedOnce, isGamesLoading]);

  async function loadGamesPage(pageNumber: number) {
    setIsGamesLoading(true);
    try {
      const activeSort = getGameSortOption(gameSort);
      const params = new URLSearchParams({
        skip: String((pageNumber - 1) * gamePageSize),
        limit: String(gamePageSize),
        sort_by: activeSort.sortBy,
        sort_dir: activeSort.sortDir,
      });

      if (deferredSearch.trim()) {
        params.set("search", deferredSearch.trim());
      }

      const page = await request<GamePage>(`/games/?${params.toString()}`);
      if (page.items.length === 0 && page.total > 0 && page.skip >= page.total) {
        setCurrentPage(Math.max(1, Math.ceil(page.total / gamePageSize)));
        return;
      }

      setGames(page.items);
      setTotalGames(page.total);
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
      await request<NamedEntity>(`/${referenceEndpoints[kind]}/`, {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      setReferenceDrafts((current) => ({ ...current, [kind]: "" }));
      if (referenceLoaded[kind]) {
        await loadReferencePage(kind, referencePages[kind]);
      }
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
      setGames((current) =>
        current.map((game) => ({
          ...game,
          [kind]: game[kind].filter((entry) => entry.id !== id),
        })),
      );
      const nextPage =
        references[kind].length === 1 && referencePages[kind] > 1 ? referencePages[kind] - 1 : referencePages[kind];
      await loadReferencePage(kind, nextPage);
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

  async function loadReferencePage(kind: ReferenceKey, pageNumber: number) {
    setReferenceLoading((current) => ({ ...current, [kind]: true }));
    try {
      const params = new URLSearchParams({
        skip: String((pageNumber - 1) * REFERENCE_PAGE_SIZE),
        limit: String(REFERENCE_PAGE_SIZE + 1),
      });
      const items = await request<NamedEntity[]>(`/${referenceEndpoints[kind]}/?${params.toString()}`);
      const hasNextPage = items.length > REFERENCE_PAGE_SIZE;

      setReferences((current) => ({
        ...current,
        [kind]: items.slice(0, REFERENCE_PAGE_SIZE),
      }));
      setReferencePages((current) => ({ ...current, [kind]: pageNumber }));
      setReferenceHasNext((current) => ({ ...current, [kind]: hasNextPage }));
      setReferenceLoaded((current) => ({ ...current, [kind]: true }));
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setReferenceLoading((current) => ({ ...current, [kind]: false }));
    }
  }

  async function toggleReference(kind: ReferenceKey) {
    if (activeReference === kind) {
      setActiveReference(null);
      return;
    }

    setActiveReference(kind);
    if (!referenceLoaded[kind]) {
      await loadReferencePage(kind, 1);
    }
  }

  const totalPages = Math.max(1, Math.ceil(totalGames / gamePageSize));
  const pageStart = totalGames === 0 ? 0 : (currentPage - 1) * gamePageSize + 1;
  const pageEnd = totalGames === 0 ? 0 : Math.min(currentPage * gamePageSize, totalGames);

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
        {message ? <section className={`flash flash-${message.tone}`}>{message.text}</section> : null}

        {!hasLoadedOnce ? (
          <section className="loading-card">
            <h2>Chargement initial</h2>
            <p>Recuperation des jeux depuis FastAPI.</p>
          </section>
        ) : null}

        {hasLoadedOnce && activeNav === "games" ? (
          <GamesSection
            currentPage={currentPage}
            games={games}
            isGamesLoading={isGamesLoading}
            pageEnd={pageEnd}
            pageSize={gamePageSize}
            pageStart={pageStart}
            search={search}
            sortValue={gameSort}
            totalGames={totalGames}
            totalPages={totalPages}
            onDeleteGame={deleteGame}
            onPageChange={setCurrentPage}
            onPageSizeChange={setGamePageSize}
            onSearchChange={setSearch}
            onSortChange={setGameSort}
          />
        ) : null}

        {hasLoadedOnce && activeNav === "references" ? (
          <EntitiesSection
            activeReference={activeReference}
            drafts={referenceDrafts}
            isReferenceLoaded={referenceLoaded}
            isReferenceLoading={referenceLoading}
            referenceHasNext={referenceHasNext}
            referencePages={referencePages}
            references={references}
            onCreateReference={createReference}
            onDeleteReference={deleteReference}
            onDraftChange={setReferenceDrafts}
            onReferencePageChange={(kind, pageNumber) => void loadReferencePage(kind, pageNumber)}
            onSelectReference={(kind) => void toggleReference(kind)}
          />
        ) : null}
      </main>
    </div>
  );
}

function GamesSection(props: {
  currentPage: number;
  games: Game[];
  isGamesLoading: boolean;
  pageEnd: number;
  pageSize: number;
  pageStart: number;
  search: string;
  sortValue: GameSortValue;
  totalGames: number;
  totalPages: number;
  onDeleteGame: (gameId: number) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (value: number) => void;
  onSearchChange: (value: string) => void;
  onSortChange: (value: GameSortValue) => void;
}) {
  const [hoveredGameId, setHoveredGameId] = useState<number | null>(null);
  const {
    currentPage,
    games,
    isGamesLoading,
    pageEnd,
    pageSize,
    pageStart,
    search,
    sortValue,
    totalGames,
    totalPages,
    onDeleteGame,
    onPageChange,
    onPageSizeChange,
    onSearchChange,
    onSortChange,
  } = props;
  const paginationItems = buildPaginationItems(currentPage, totalPages);
  const resultLabel =
    totalGames === 0 ? "Aucun resultat" : `${pageStart}-${pageEnd} sur ${totalGames}`;

  return (
    <section className="games-layout">
      <section className="panel games-search">
        <label className="games-search-field">
          <input
            aria-label="Rechercher un jeu"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Nom du jeu"
          />
        </label>
      </section>

      <section className="panel games-content">
        <div className="games-controls">
          <div className="games-results-copy" aria-live="polite">
            <strong>{totalGames}</strong>
            <span>{totalGames > 1 ? "jeux dans le catalogue" : "jeu dans le catalogue"}</span>
          </div>

          <label className="games-inline-control">
            <span>Trier la liste</span>
            <select value={sortValue} onChange={(event) => onSortChange(event.target.value as GameSortValue)}>
              {GAME_SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="table-shell">
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
                <p>Mise a jour de la page en cours.</p>
              </div>
            ) : games.length === 0 ? (
              <div className="empty-state">
                <h3>Aucun jeu</h3>
                <p>Aucun jeu ne correspond a cette recherche.</p>
              </div>
            ) : (
              games.map((game) => (
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
                  <div>{game.type || "-"}</div>
                  <div>{game.creation_year ?? "-"}</div>
                  <div>{formatPlayers(game)}</div>
                  <div>{formatDuration(game.duration_minutes)}</div>
                  <div>{joinNames(game.authors) || "-"}</div>
                  <div>{joinNames(game.editors) || "-"}</div>
                  <div className="row-actions">
                    <button type="button" className="link-button danger" onClick={() => onDeleteGame(game.id)}>
                      Supprimer
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      <section className="panel games-footer">
        <div className="games-footer-meta">
          <strong>{resultLabel}</strong>
          <span>{games.length} elements affiches sur cette page.</span>
        </div>

        <div className="games-pagination" aria-label="Pagination des jeux">
          <button
            type="button"
            className="secondary-button"
            disabled={currentPage <= 1 || isGamesLoading}
            onClick={() => onPageChange(currentPage - 1)}
          >
            Precedente
          </button>

          <div className="games-pagination-pages">
            {paginationItems.map((item) =>
              typeof item === "number" ? (
                <button
                  key={item}
                  type="button"
                  className={`game-page-button ${item === currentPage ? "active" : ""}`}
                  disabled={isGamesLoading}
                  onClick={() => onPageChange(item)}
                >
                  {item}
                </button>
              ) : (
                <span key={item} className="pagination-ellipsis" aria-hidden="true">
                  ...
                </span>
              ),
            )}
          </div>

          <button
            type="button"
            className="secondary-button"
            disabled={currentPage >= totalPages || isGamesLoading}
            onClick={() => onPageChange(currentPage + 1)}
          >
            Suivante
          </button>
        </div>

        <label className="games-inline-control games-inline-control-compact">
          <span>Par page</span>
          <select value={String(pageSize)} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
            {GAME_PAGE_SIZE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
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
  activeReference: ReferenceKey | null;
  drafts: ReferenceDrafts;
  isReferenceLoaded: Record<ReferenceKey, boolean>;
  isReferenceLoading: Record<ReferenceKey, boolean>;
  referenceHasNext: Record<ReferenceKey, boolean>;
  referencePages: Record<ReferenceKey, number>;
  references: ReferenceCollection;
  onCreateReference: (kind: ReferenceKey, event: FormEvent<HTMLFormElement>) => Promise<void>;
  onDeleteReference: (kind: ReferenceKey, id: number) => Promise<void>;
  onDraftChange: (updater: (current: ReferenceDrafts) => ReferenceDrafts) => void;
  onReferencePageChange: (kind: ReferenceKey, pageNumber: number) => void;
  onSelectReference: (kind: ReferenceKey) => void;
}) {
  const {
    activeReference,
    drafts,
    isReferenceLoaded,
    isReferenceLoading,
    referenceHasNext,
    referencePages,
    references,
    onCreateReference,
    onDeleteReference,
    onDraftChange,
    onReferencePageChange,
    onSelectReference,
  } = props;

  return (
    <section className="entities-layout">
      <section className="section-intro">
        <h2>Referentiels</h2>
      </section>

      <div className="entity-accordion">
        {referenceNavItems.map((kind) => {
          const isOpen = activeReference === kind;
          const isLoading = isReferenceLoading[kind];
          const hasLoaded = isReferenceLoaded[kind];
          const currentPage = referencePages[kind];
          const canGoBack = currentPage > 1;
          const canGoForward = referenceHasNext[kind];

          return (
            <section key={kind} className={`panel entity-panel ${isOpen ? "entity-panel-active" : ""}`}>
              <button
                type="button"
                className={`entity-toggle ${isOpen ? "entity-toggle-active" : ""}`}
                onClick={() => onSelectReference(kind)}
                aria-expanded={isOpen}
              >
                <span className="entity-toggle-title">{referenceTitles[kind]}</span>
                <span className="entity-toggle-count">{isOpen ? "Masquer" : "Afficher"}</span>
              </button>

              {isOpen ? (
                <div className="entity-panel-body">
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

                    {isLoading && !hasLoaded ? (
                      <div className="empty-state compact">
                        <h3>Chargement</h3>
                        <p>Recuperation de la page {currentPage}.</p>
                      </div>
                    ) : references[kind].length === 0 ? (
                      <div className="empty-state compact">
                        <h3>Referentiel vide</h3>
                        <p>Aucun element n'est disponible pour cette categorie.</p>
                      </div>
                    ) : (
                      references[kind].map((item) => (
                        <div key={item.id} className="simple-row">
                          <span>{item.id}</span>
                          <span>{item.name}</span>
                          <button
                            type="button"
                            className="link-button danger"
                            onClick={() => void onDeleteReference(kind, item.id)}
                          >
                            Supprimer
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="entity-pagination">
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={!canGoBack || isLoading}
                      onClick={() => onReferencePageChange(kind, currentPage - 1)}
                    >
                      Page precedente
                    </button>
                    <span>Page {currentPage}</span>
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={!canGoForward || isLoading}
                      onClick={() => onReferencePageChange(kind, currentPage + 1)}
                    >
                      Page suivante
                    </button>
                  </div>
                </div>
              ) : null}
            </section>
          );
        })}
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

function getGameSortOption(value: GameSortValue) {
  return GAME_SORT_OPTIONS.find((option) => option.value === value) ?? GAME_SORT_OPTIONS[0];
}

function buildPaginationItems(currentPage: number, totalPages: number) {
  const candidates = new Set([1, currentPage - 1, currentPage, currentPage + 1, totalPages]);
  const pages = Array.from(candidates)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((left, right) => left - right);

  const items: Array<number | string> = [];
  let previousPage = 0;

  pages.forEach((page) => {
    if (previousPage && page - previousPage > 1) {
      items.push(`ellipsis-${previousPage}-${page}`);
    }
    items.push(page);
    previousPage = page;
  });

  return items;
}

export default App;
