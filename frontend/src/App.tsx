import { FormEvent, useDeferredValue, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { getErrorMessage, joinNames, request } from "./api";
import { authClient } from "./auth-client";
import { navItems, referenceEndpoints, referenceNavItems, referenceTitles } from "./types";
import type {
  CollectionBoard,
  CollectionItem,
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
const FRONTEND_VERSION = __APP_VERSION__;
const AUTH_SESSION_TIMEOUT_MS = 8000;
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
type FlashMessage = { tone: "success" | "error"; text: string };
type AuthenticatedUser = {
  email?: string | null;
  image?: string | null;
  name?: string | null;
};

function buildGamePagePath(
  basePath: string,
  pageNumber: number,
  pageSize: number,
  sortValue: GameSortValue,
  searchValue: string,
) {
  const activeSort = getGameSortOption(sortValue);
  const params = new URLSearchParams({
    skip: String((pageNumber - 1) * pageSize),
    limit: String(pageSize),
    sort_by: activeSort.sortBy,
    sort_dir: activeSort.sortDir,
  });

  if (searchValue.trim()) {
    params.set("search", searchValue.trim());
  }

  return `${basePath}?${params.toString()}`;
}

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
  const { data: session, error, isPending } = authClient.useSession();
  const [authMessage, setAuthMessage] = useState<FlashMessage | null>(null);
  const [isSessionCheckStalled, setIsSessionCheckStalled] = useState(false);

  useEffect(() => {
    if (!isPending) {
      setIsSessionCheckStalled(false);
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setIsSessionCheckStalled(true);
    }, AUTH_SESSION_TIMEOUT_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [isPending]);

  async function signInWithGoogle() {
    setAuthMessage(null);
    const { error: signInError } = await authClient.signIn.social({
      provider: "google",
      callbackURL: "/",
    });

    if (signInError) {
      setAuthMessage({ tone: "error", text: signInError.message ?? "Connexion Google impossible." });
    }
  }

  async function signOut() {
    const { error: signOutError } = await authClient.signOut();

    if (signOutError) {
      setAuthMessage({ tone: "error", text: signOutError.message ?? "Deconnexion impossible." });
      return;
    }

    setAuthMessage(null);
  }

  function reloadApplication() {
    window.location.reload();
  }

  if (isPending && isSessionCheckStalled) {
    return (
      <AuthenticationShell
        actionLabel="Recharger l'application"
        description="La verification de session prend plus de temps que prevu. Le proxy /api/auth ou le service d'authentification ne repond peut-etre pas encore."
        message={{
          tone: "error",
          text: "Si vous utilisez Docker Compose, verifiez que les services frontend et auth sont bien demarres, puis rechargez la page.",
        }}
        onAction={reloadApplication}
        title="Authentification en attente"
      />
    );
  }

  if (isPending) {
    return (
      <AuthenticationShell
        description="Verification de votre session en cours."
        message={authMessage}
        title="Connexion en cours"
      />
    );
  }

  if (error) {
    return (
      <AuthenticationShell
        actionLabel="Continuer avec Google"
        description="Le service d'authentification ne repond pas correctement pour le moment."
        message={{ tone: "error", text: getErrorMessage(error) }}
        onAction={() => void signInWithGoogle()}
        title="Authentification indisponible"
      />
    );
  }

  if (!session?.user) {
    return (
      <AuthenticationShell
        actionLabel="Continuer avec Google"
        description="Connectez-vous avec votre compte Google pour acceder a votre catalogue Ludostock."
        message={authMessage}
        onAction={() => void signInWithGoogle()}
        title="Bienvenue dans Ludostock"
      />
    );
  }

  return <AuthenticatedApp authMessage={authMessage} onSignOut={() => void signOut()} user={session.user} />;
}

function AuthenticatedApp(props: { authMessage: FlashMessage | null; onSignOut: () => void; user: AuthenticatedUser }) {
  const { authMessage, onSignOut, user } = props;
  const [activeNav, setActiveNav] = useState<NavKey>("games");
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
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
  const [message, setMessage] = useState<FlashMessage | null>(null);
  const deferredSearch = useDeferredValue(search);
  const [collectionBoard, setCollectionBoard] = useState<CollectionBoard | null>(null);
  const [isCollectionLoading, setIsCollectionLoading] = useState(false);
  const [hasLoadedCollectionOnce, setHasLoadedCollectionOnce] = useState(false);
  const [collectionSearch, setCollectionSearch] = useState("");
  const profileMenuRef = useRef<HTMLDivElement | null>(null);
  const activeNavItem = navItems.find((item) => item.key === activeNav) ?? navItems[0];
  const sectionDescriptions: Record<NavKey, string> = {
    games: "Parcourez et filtrez le catalogue Ludostock.",
    collection: "Consultez et enrichissez votre collection personnelle.",
    references: "Administrez les auteurs, artistes, editeurs et distributeurs.",
  };

  useEffect(() => {
    setCurrentPage(1);
  }, [deferredSearch, gamePageSize, gameSort]);

  useEffect(() => {
    void loadGamesPage(currentPage);
  }, [currentPage, deferredSearch, gamePageSize, gameSort, gamesRefreshToken]);

  useEffect(() => {
    if (activeNav !== "collection") {
      return;
    }
    void loadCollectionBoard();
  }, [activeNav]);

  useEffect(() => {
    if (!hasLoadedOnce && !isGamesLoading) {
      setHasLoadedOnce(true);
    }
  }, [hasLoadedOnce, isGamesLoading]);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!profileMenuRef.current?.contains(event.target as Node)) {
        setIsProfileMenuOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsProfileMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  useEffect(() => {
    setIsProfileMenuOpen(false);
  }, [activeNav]);

  async function loadGamesPage(pageNumber: number) {
    setIsGamesLoading(true);
    try {
      const page = await request<GamePage>(buildGamePagePath("/games/", pageNumber, gamePageSize, gameSort, deferredSearch));
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

  async function loadCollectionBoard() {
    setIsCollectionLoading(true);
    try {
      const board = await request<CollectionBoard>("/me/collection/board/");
      setCollectionBoard(board);
    } catch (error) {
      setMessage({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsCollectionLoading(false);
      setHasLoadedCollectionOnce(true);
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

  async function moveCollectionGame(collectionGameId: number, locationId: number | null) {
    try {
      await request(`/me/collection/games/${collectionGameId}`, {
        method: "PATCH",
        body: JSON.stringify({ location_id: locationId }),
      });
      setCollectionBoard((current) =>
        current
          ? {
              ...current,
              items: current.items.map((item) =>
                item.id === collectionGameId ? { ...item, location_id: locationId } : item,
              ),
            }
          : current,
      );
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
          <img className="brand-mark" src="/ludostock-logo.svg" alt="" aria-hidden="true" />
          <div>
            <p className="brand-title">Ludostock</p>
            <p className="brand-subtitle">Catalogue prive</p>
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
          <div className="section-intro">
            <h1>{activeNavItem.label}</h1>
            <p>{sectionDescriptions[activeNavItem.key]}</p>
          </div>

          <div className={`profile-menu ${isProfileMenuOpen ? "open" : ""}`} ref={profileMenuRef}>
            <button
              type="button"
              className="profile-trigger"
              aria-expanded={isProfileMenuOpen}
              aria-haspopup="menu"
              aria-label="Ouvrir le menu profil"
              onClick={() => setIsProfileMenuOpen((current) => !current)}
            >
              <ProfileIcon />
              <div className="profile-trigger-avatar" aria-hidden="true">
                {user.image ? <img src={user.image} alt="" /> : <span>{getUserInitial(user)}</span>}
              </div>
            </button>

            {isProfileMenuOpen ? (
              <div className="profile-dropdown" role="menu" aria-label="Menu profil">
                <div className="profile-dropdown-header">
                  <div className="profile-dropdown-avatar" aria-hidden="true">
                    {user.image ? <img src={user.image} alt="" /> : <span>{getUserInitial(user)}</span>}
                  </div>
                  <div className="profile-dropdown-copy">
                    <strong>{user.name || "Utilisateur Google"}</strong>
                    <span>{user.email || "Adresse e-mail indisponible"}</span>
                  </div>
                </div>

                <button
                  type="button"
                  className="secondary-button profile-signout"
                  role="menuitem"
                  onClick={() => {
                    setIsProfileMenuOpen(false);
                    onSignOut();
                  }}
                >
                  Se deconnecter
                </button>
              </div>
            ) : null}
          </div>
        </header>

        {authMessage ? <section className={`flash flash-${authMessage.tone}`}>{authMessage.text}</section> : null}
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

        {activeNav === "collection" ? (
          <CollectionSection
            board={collectionBoard}
            hasLoadedOnce={hasLoadedCollectionOnce}
            isCollectionLoading={isCollectionLoading}
            search={collectionSearch}
            onMoveGame={moveCollectionGame}
            onSearchChange={setCollectionSearch}
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

        <footer className="app-footer panel" aria-label="Version de l'application">
          <span>Version {FRONTEND_VERSION}</span>
        </footer>
      </main>
    </div>
  );
}

function AuthenticationShell(props: {
  actionLabel?: string;
  description: string;
  message: FlashMessage | null;
  onAction?: () => void;
  title: string;
}) {
  const { actionLabel, description, message, onAction, title } = props;

  return (
    <div className="auth-shell">
      <section className="auth-card">
        <div className="brand auth-brand">
          <img className="brand-mark" src="/ludostock-logo.svg" alt="" aria-hidden="true" />
          <div>
            <p className="brand-title">Ludostock</p>
          </div>
        </div>

        <div className="section-intro">
          <h2>{title}</h2>
          <p>{description}</p>
        </div>

        {message ? <section className={`flash flash-${message.tone}`}>{message.text}</section> : null}

        {actionLabel && onAction ? (
          <button type="button" className="primary-button auth-action" onClick={onAction}>
            {actionLabel}
          </button>
        ) : null}
      </section>
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
          <span>Recherche</span>
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
          <div className="table-head games-table-head">
            <div>Nom</div>
            <div>Annee</div>
            <div>Joueurs</div>
            <div>Duree</div>
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
                <div key={game.id} className="table-row games-table-row">
                  <GameNameCell
                    game={game}
                    isVisible={hoveredGameId === game.id}
                    onHoverEnd={() => setHoveredGameId((current) => (current === game.id ? null : current))}
                    onHoverStart={() => setHoveredGameId(game.id)}
                  />
                  <div>
                    <CompactGameFact kind="year" label="Annee de publication" value={String(game.creation_year ?? "-")} />
                  </div>
                  <div>
                    <CompactGameFact kind="players" label="Nombre de joueurs" value={formatPlayers(game)} />
                  </div>
                  <div>
                    <CompactGameFact kind="duration" label="Duree" value={formatDuration(game.duration_minutes)} />
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
        </div>

        <div className="games-pagination" aria-label="Pagination des jeux">
          <button
            type="button"
            className="secondary-button"
            disabled={currentPage <= 1 || isGamesLoading}
            onClick={() => onPageChange(currentPage - 1)}
          >
            Precedent
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
            Suivant
          </button>
        </div>

        <label className="games-inline-control games-inline-control-compact">
          <select
            aria-label="Nombre d'elements par page"
            value={String(pageSize)}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
          >
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

function CollectionSection(props: {
  board: CollectionBoard | null;
  hasLoadedOnce: boolean;
  isCollectionLoading: boolean;
  search: string;
  onMoveGame: (collectionGameId: number, locationId: number | null) => void;
  onSearchChange: (value: string) => void;
}) {
  const {
    board,
    hasLoadedOnce,
    isCollectionLoading,
    search,
    onMoveGame,
    onSearchChange,
  } = props;
  const normalizedSearch = search.trim().toLowerCase();
  const locations = [{ id: null, name: "Sans lieu" }, ...(board?.locations ?? [])];
  const items = (board?.items ?? []).filter((item) =>
    normalizedSearch ? item.game.name.toLowerCase().includes(normalizedSearch) : true,
  );
  const totalGames = items.length;
  const hasBoardStructure = (board?.items.length ?? 0) > 0 || (board?.locations.length ?? 0) > 0;

  return (
    <section className="games-layout">
      <section className="panel games-search">
        <label className="games-search-field">
          <span>Recherche</span>
          <input
            aria-label="Rechercher un jeu dans ma collection"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Nom du jeu dans ma collection"
          />
        </label>
      </section>

      <section className="panel games-content">
        <div className="games-controls">
          <div className="games-results-copy" aria-live="polite">
            <strong>{totalGames}</strong>
            <span>{totalGames > 1 ? "jeux visibles dans la collection" : "jeu visible dans la collection"}</span>
          </div>
        </div>

        <div className="collection-board">
          {!hasLoadedOnce ? (
            <div className="empty-state">
              <h3>Chargement</h3>
              <p>Recuperation de votre collection en cours.</p>
            </div>
          ) : isCollectionLoading ? (
            <div className="empty-state">
              <h3>Chargement</h3>
              <p>Mise a jour de votre collection en cours.</p>
            </div>
          ) : !hasBoardStructure ? (
            <div className="empty-state">
              <h3>Collection vide</h3>
              <p>Ajoutez un jeu du catalogue pour commencer votre collection.</p>
            </div>
          ) : (
            <>
              {items.length === 0 && search.trim() ? (
                <p className="empty-inline">Aucun jeu ne correspond a votre recherche dans les lieux affiches.</p>
              ) : null}
              {locations.map((location) => (
                <CollectionLocationColumn
                  key={location.id ?? "unassigned"}
                  items={items.filter((item) => item.location_id === location.id)}
                  locationName={location.name}
                  onMoveGame={onMoveGame}
                  targetLocationId={location.id}
                />
              ))}
            </>
          )}
        </div>
      </section>
    </section>
  );
}

function CollectionLocationColumn(props: {
  items: CollectionItem[];
  locationName: string;
  onMoveGame: (collectionGameId: number, locationId: number | null) => void;
  targetLocationId: number | null;
}) {
  const [hoveredGameId, setHoveredGameId] = useState<number | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const { items, locationName, onMoveGame, targetLocationId } = props;

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragOver(false);
    const rawId = event.dataTransfer.getData("text/plain");
    const collectionGameId = Number(rawId);

    if (!collectionGameId) {
      return;
    }

    void onMoveGame(collectionGameId, targetLocationId);
  }

  return (
    <section
      className={`collection-location-column ${isDragOver ? "collection-location-column-active" : ""}`}
      onDragEnter={(event) => {
        event.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
          setIsDragOver(false);
        }
      }}
      onDragOver={(event) => event.preventDefault()}
      onDrop={handleDrop}
    >
      <div className="collection-location-header">
        <div>
          <h3>{locationName}</h3>
          <p>{items.length > 1 ? `${items.length} jeux` : `${items.length} jeu`}</p>
        </div>
      </div>

      <div className="collection-location-body">
        {items.length === 0 ? (
          <div className="empty-state compact">
            <h3>Vide</h3>
            <p>Deposez un jeu ici.</p>
          </div>
        ) : (
          items
            .slice()
            .sort((left, right) => left.game.name.localeCompare(right.game.name, "fr"))
            .map((item) => (
              <article
                key={item.id}
                className="collection-card"
                draggable
                onDragStart={(event) => {
                  event.dataTransfer.effectAllowed = "move";
                  event.dataTransfer.setData("text/plain", String(item.id));
                }}
              >
                <div className="collection-card-media">
                  {item.game.image_url ? (
                    <img src={item.game.image_url} alt={item.game.name} loading="lazy" />
                  ) : (
                    <div className="collection-card-fallback" aria-hidden="true">
                      {item.game.name.slice(0, 1).toUpperCase()}
                    </div>
                  )}
                </div>
                <div className="collection-card-title">
                  <GameNameCell
                    game={item.game}
                    isVisible={hoveredGameId === item.id}
                    onHoverEnd={() => setHoveredGameId((current) => (current === item.id ? null : current))}
                    onHoverStart={() => setHoveredGameId(item.id)}
                  />
                </div>
                <div className="collection-card-meta">
                  <span>{item.game.type || "-"}</span>
                  <span>{item.game.creation_year ?? "-"}</span>
                </div>
                <div className="collection-card-facts">
                  <CompactGameFact kind="players" label="Nombre de joueurs" value={formatPlayers(item.game)} />
                  <CompactGameFact kind="duration" label="Duree" value={formatDuration(item.game.duration_minutes)} />
                </div>
                <p className="collection-card-copy">Auteurs : {joinNames(item.game.authors)}</p>
                <p className="collection-card-copy">Editeurs : {joinNames(item.game.editors)}</p>
              </article>
            ))
        )}
      </div>
    </section>
  );
}

function CompactGameFact({
  kind,
  label,
  value,
}: {
  kind: "year" | "players" | "duration";
  label: string;
  value: string;
}) {
  return (
    <div className="compact-game-fact" aria-label={`${label} : ${value}`}>
      <GameFactIcon kind={kind} />
      <span>{value}</span>
    </div>
  );
}

function ProfileIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="profile-trigger-icon">
      <path
        d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Z"
        fill="currentColor"
      />
    </svg>
  );
}

function GameNameCell(props: {
  game: Game;
  isVisible: boolean;
  onHoverEnd: () => void;
  onHoverStart: () => void;
}) {
  const { game, isVisible, onHoverEnd, onHoverStart } = props;
  const anchorRef = useRef<HTMLDivElement | null>(null);

  return (
    <div className="table-name-cell" ref={anchorRef} onMouseEnter={onHoverStart} onMouseLeave={onHoverEnd}>
      {game.url ? (
        <a
          href={game.url}
          target="_blank"
          rel="noreferrer"
          className="table-link"
          onFocus={onHoverStart}
          onBlur={onHoverEnd}
        >
          {game.name}
        </a>
      ) : (
        <span className="table-link table-link-static">{game.name}</span>
      )}
      <GameHoverCard anchorElement={anchorRef.current} game={game} isVisible={isVisible} />
    </div>
  );
}

function GameFactIcon({ kind }: { kind: "year" | "players" | "duration" }) {
  if (kind === "year") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="game-fact-icon">
        <path
          d="M7 2v3M17 2v3M4 8h16M5 5h14a1 1 0 0 1 1 1v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a1 1 0 0 1 1-1Z"
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.75"
        />
      </svg>
    );
  }

  if (kind === "players") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true" className="game-fact-icon">
        <path
          d="M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm6 1a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM4 19a5 5 0 0 1 10 0M13 19a4 4 0 0 1 7 0"
          fill="none"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.75"
        />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="game-fact-icon">
      <path
        d="M12 6v6l4 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.75"
      />
    </svg>
  );
}

function GameHoverCard({
  anchorElement,
  game,
  isVisible,
}: {
  anchorElement: HTMLDivElement | null;
  game: Game;
  isVisible: boolean;
}) {
  const [position, setPosition] = useState<{ left: number; top: number; width: number } | null>(null);
  const hoverFacts = [
    { kind: "year" as const, label: "Annee de publication", value: String(game.creation_year ?? "-") },
    { kind: "players" as const, label: "Nombre de joueurs", value: formatPlayers(game) },
    { kind: "duration" as const, label: "Duree", value: formatDuration(game.duration_minutes) },
  ];
  const details = [
    { label: "Type", value: game.type || "-" },
    { label: "Age minimum", value: game.min_age !== null ? `${game.min_age}+` : "-" },
    { label: "Auteurs", value: joinNames(game.authors) },
    { label: "Artistes", value: joinNames(game.artists) },
    { label: "Editeurs", value: joinNames(game.editors) },
    { label: "Distributeurs", value: joinNames(game.distributors) },
  ];

  useLayoutEffect(() => {
    if (!isVisible || !anchorElement) {
      setPosition(null);
      return;
    }

    const element = anchorElement;

    function updatePosition() {
      const rect = element.getBoundingClientRect();
      const margin = 12;
      const width = Math.min(430, window.innerWidth - margin * 2);
      const estimatedHeight = 360;
      const left = Math.min(Math.max(rect.left, margin), window.innerWidth - width - margin);
      const canRenderBelow = rect.bottom + estimatedHeight + margin <= window.innerHeight;
      const top = canRenderBelow
        ? rect.bottom + 10
        : Math.max(margin, rect.top - estimatedHeight - 10);

      setPosition({ left, top, width });
    }

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);

    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [anchorElement, isVisible]);

  if (!isVisible || !anchorElement || !position) {
    return null;
  }

  return createPortal(
    <div
      className="game-hover-card is-visible"
      style={{ left: `${position.left}px`, top: `${position.top}px`, width: `${position.width}px` }}
      aria-hidden={!isVisible}
    >
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
        <div className="game-hover-facts">
          {hoverFacts.map((fact) => (
            <CompactGameFact key={fact.label} kind={fact.kind} label={fact.label} value={fact.value} />
          ))}
        </div>
        <dl className="game-hover-details">
          {details.map((detail) => (
            <div key={detail.label} className="game-hover-detail">
              <dt>{detail.label}</dt>
              <dd>{detail.value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>,
    document.body,
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

function getUserInitial(user: AuthenticatedUser) {
  const label = user.name?.trim() || user.email?.trim() || "L";
  return label.slice(0, 1).toUpperCase();
}

export default App;
