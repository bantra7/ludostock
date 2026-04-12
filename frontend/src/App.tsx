import { FormEvent, useCallback, useDeferredValue, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { getErrorMessage, joinNames, request } from "./api";
import { authClient } from "./auth-client";
import { navItems, referenceEndpoints, referenceNavItems, referenceTitles } from "./types";
import type {
  CollectionBoard,
  CollectionGame,
  CollectionItem,
  CollectionShareSettings,
  Game,
  GamePage,
  NamedEntity,
  NavKey,
  ReferenceCollection,
  ReferenceDrafts,
  ReferenceKey,
  SharedCollectionBoard,
  SharedCollectionSummary,
  UserLocation,
} from "./types";

const DEFAULT_GAME_PAGE_SIZE = 50;
const REFERENCE_PAGE_SIZE = 25;
const GAME_PAGE_SIZE_OPTIONS = [50, 100, 200] as const;
const FRONTEND_VERSION = __APP_VERSION__;
const AUTH_SESSION_TIMEOUT_MS = 8000;
const TOAST_DURATION_MS = 5000;
const TOAST_MAX_VISIBLE = 4;
const NOTIFICATION_LOG_LIMIT = 12;
const ADMIN_EMAIL = "renault.jbapt@gmail.com";
const GAME_SORT_OPTIONS = [
  { value: "name:asc", label: "Nom (A-Z)", sortBy: "name", sortDir: "asc" },
  { value: "name:desc", label: "Nom (Z-A)", sortBy: "name", sortDir: "desc" },
  { value: "creation_year:asc", label: "Annee (croissante)", sortBy: "creation_year", sortDir: "asc" },
  { value: "creation_year:desc", label: "Annee (decroissante)", sortBy: "creation_year", sortDir: "desc" },
  { value: "players:asc", label: "Joueurs (croissant)", sortBy: "players", sortDir: "asc" },
  { value: "players:desc", label: "Joueurs (decroissant)", sortBy: "players", sortDir: "desc" },
  { value: "duration_minutes:asc", label: "Duree (croissante)", sortBy: "duration_minutes", sortDir: "asc" },
  { value: "duration_minutes:desc", label: "Duree (decroissante)", sortBy: "duration_minutes", sortDir: "desc" },
] as const;

type GameSortValue = (typeof GAME_SORT_OPTIONS)[number]["value"];
type FlashMessage = { tone: "success" | "error"; text: string };
type ToastNotification = FlashMessage & { id: number };
type ConfirmDialog = {
  body: string;
  confirmLabel?: string;
  isDanger?: boolean;
  onConfirm: () => void;
  title: string;
};
type AuthenticatedUser = {
  email?: string | null;
  image?: string | null;
  name?: string | null;
};
type NavigationItem = (typeof navItems)[number];

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

function buildShareUrl(shareToken: string | null) {
  if (!shareToken || typeof window === "undefined") {
    return "";
  }

  const url = new URL(window.location.href);
  url.searchParams.set("share", shareToken);
  return url.toString();
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

function useToastNotifications() {
  const [toasts, setToasts] = useState<ToastNotification[]>([]);
  const [notificationLog, setNotificationLog] = useState<ToastNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const nextToastId = useRef(1);
  const toastTimeouts = useRef(new Map<number, number>());

  const dismissToast = useCallback((id: number) => {
    const timeoutId = toastTimeouts.current.get(id);
    if (timeoutId) {
      window.clearTimeout(timeoutId);
      toastTimeouts.current.delete(id);
    }

    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: FlashMessage) => {
      const id = nextToastId.current;
      nextToastId.current += 1;

      const timeoutId = window.setTimeout(() => {
        dismissToast(id);
      }, TOAST_DURATION_MS);

      toastTimeouts.current.set(id, timeoutId);
      const notification = { ...message, id };

      setNotificationLog((current) => [notification, ...current].slice(0, NOTIFICATION_LOG_LIMIT));
      setUnreadCount((current) => Math.min(current + 1, NOTIFICATION_LOG_LIMIT));

      setToasts((current) => {
        const next = [...current, notification];
        const dropped = next.slice(0, Math.max(0, next.length - TOAST_MAX_VISIBLE));

        dropped.forEach((toast) => {
          const droppedTimeoutId = toastTimeouts.current.get(toast.id);
          if (droppedTimeoutId) {
            window.clearTimeout(droppedTimeoutId);
          }
          toastTimeouts.current.delete(toast.id);
        });

        return next.slice(-TOAST_MAX_VISIBLE);
      });
    },
    [dismissToast],
  );

  const markNotificationsAsRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  useEffect(() => {
    const activeTimeouts = toastTimeouts.current;

    return () => {
      activeTimeouts.forEach((timeoutId) => {
        window.clearTimeout(timeoutId);
      });
      activeTimeouts.clear();
    };
  }, []);

  return { dismissToast, markNotificationsAsRead, notificationLog, showToast, toasts, unreadCount };
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
      callbackURL: `${window.location.pathname}${window.location.search}`,
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
  const {
    dismissToast,
    markNotificationsAsRead,
    notificationLog,
    showToast,
    toasts,
    unreadCount,
  } = useToastNotifications();
  const [activeNav, setActiveNav] = useState<NavKey>("home");
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
  const [gameSort, setGameSort] = useState<GameSortValue>("creation_year:desc");
  const [gamesRefreshToken, setGamesRefreshToken] = useState(0);
  const deferredSearch = useDeferredValue(search);
  const [collectionBoard, setCollectionBoard] = useState<CollectionBoard | null>(null);
  const [isCollectionLoading, setIsCollectionLoading] = useState(false);
  const [hasLoadedCollectionOnce, setHasLoadedCollectionOnce] = useState(false);
  const [collectionSearch, setCollectionSearch] = useState("");
  const [shareSettings, setShareSettings] = useState<CollectionShareSettings | null>(null);
  const [isShareSettingsLoading, setIsShareSettingsLoading] = useState(false);
  const [sharedCollections, setSharedCollections] = useState<SharedCollectionSummary[]>([]);
  const [isSharedCollectionsLoading, setIsSharedCollectionsLoading] = useState(false);
  const [hasLoadedSharedCollectionsOnce, setHasLoadedSharedCollectionsOnce] = useState(false);
  const [activeSharedCollectionId, setActiveSharedCollectionId] = useState<number | null>(null);
  const [sharedCollectionBoard, setSharedCollectionBoard] = useState<SharedCollectionBoard | null>(null);
  const [isSharedCollectionBoardLoading, setIsSharedCollectionBoardLoading] = useState(false);
  const hasProcessedShareLinkRef = useRef(false);
  const [quickCatalogSearch, setQuickCatalogSearch] = useState("");
  const [quickCatalogResults, setQuickCatalogResults] = useState<Game[]>([]);
  const [isQuickCatalogLoading, setIsQuickCatalogLoading] = useState(false);
  const [isQuickCatalogSearchOpen, setIsQuickCatalogSearchOpen] = useState(false);
  const deferredQuickCatalogSearch = useDeferredValue(quickCatalogSearch);
  const [locationDraft, setLocationDraft] = useState("");
  const [isCreatingLocation, setIsCreatingLocation] = useState(false);
  const [pendingCollectionGameIds, setPendingCollectionGameIds] = useState<number[]>([]);
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialog | null>(null);
  const gamesCatalogRef = useRef<HTMLElement | null>(null);
  const quickCatalogMenuRef = useRef<HTMLDivElement | null>(null);
  const isReferenceAdmin = user.email?.toLowerCase() === ADMIN_EMAIL;
  const visibleNavItems: NavigationItem[] = [
    { key: "home", label: "Accueil" },
    { key: "games", label: "Ma collection" },
    { key: "friends", label: "Mes amis" },
    { key: "catalog", label: "Catalogue" },
    { key: "settings", label: "Parametres" },
  ];
  const activeNavItem = visibleNavItems.find((item) => item.key === activeNav) ?? visibleNavItems[0];
  const sectionDescriptions: Record<NavKey, string> = {
    home: "Votre ludotheque en un coup d'oeil.",
    catalog: "Parcourez les references et ajoutez des jeux.",
    friends: "Consultez les collections partagees avec vous.",
    games: "Consultez les jeux que vous possedez.",
    locations: "",
    settings: "Profil et referentiels.",
  };

  useEffect(() => {
    setCurrentPage(1);
  }, [deferredSearch, gamePageSize, gameSort]);

  useEffect(() => {
    void loadGamesPage(currentPage);
  }, [currentPage, deferredSearch, gamePageSize, gameSort, gamesRefreshToken]);

  useEffect(() => {
    void loadCollectionBoard();
  }, []);

  useEffect(() => {
    const query = deferredQuickCatalogSearch.trim();
    if (query.length < 2) {
      setQuickCatalogResults([]);
      setIsQuickCatalogLoading(false);
      return;
    }

    let ignoreResult = false;

    async function loadQuickCatalogResults() {
      setIsQuickCatalogLoading(true);
      try {
        const page = await request<GamePage>(buildGamePagePath("/games/", 1, 8, "name:asc", query));
        if (!ignoreResult) {
          setQuickCatalogResults(page.items);
        }
      } catch (error) {
        if (!ignoreResult) {
          showToast({ tone: "error", text: getErrorMessage(error) });
        }
      } finally {
        if (!ignoreResult) {
          setIsQuickCatalogLoading(false);
        }
      }
    }

    void loadQuickCatalogResults();

    return () => {
      ignoreResult = true;
    };
  }, [deferredQuickCatalogSearch, showToast]);

  useEffect(() => {
    if (authMessage) {
      showToast(authMessage);
    }
  }, [authMessage, showToast]);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!quickCatalogMenuRef.current?.contains(event.target as Node)) {
        setIsQuickCatalogSearchOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsQuickCatalogSearchOpen(false);
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
    if (activeNav !== "games" && activeNav !== "locations") {
      return;
    }
    void loadCollectionBoard();
  }, [activeNav]);

  useEffect(() => {
    if (activeNav === "settings") {
      void loadShareSettings();
    }
  }, [activeNav]);

  useEffect(() => {
    if (activeNav === "friends") {
      void loadSharedCollections();
    }
  }, [activeNav]);

  useEffect(() => {
    if (activeNav !== "friends" || activeSharedCollectionId === null) {
      return;
    }

    void loadSharedCollectionBoard(activeSharedCollectionId);
  }, [activeNav, activeSharedCollectionId]);

  useEffect(() => {
    if (hasProcessedShareLinkRef.current) {
      return;
    }

    const shareToken = new URLSearchParams(window.location.search).get("share");
    if (!shareToken) {
      hasProcessedShareLinkRef.current = true;
      return;
    }

    hasProcessedShareLinkRef.current = true;
    void joinSharedCollectionFromLink(shareToken);
  }, []);

  useEffect(() => {
    if (!hasLoadedOnce && !isGamesLoading) {
      setHasLoadedOnce(true);
    }
  }, [hasLoadedOnce, isGamesLoading]);

  useEffect(() => {
    if (!isReferenceAdmin && activeReference !== null) {
      setActiveReference(null);
    }
  }, [activeReference, isReferenceAdmin]);

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
      showToast({ tone: "error", text: getErrorMessage(error) });
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
      showToast({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsCollectionLoading(false);
      setHasLoadedCollectionOnce(true);
    }
  }

  async function loadShareSettings() {
    setIsShareSettingsLoading(true);
    try {
      const settings = await request<CollectionShareSettings>("/me/collection/share/");
      setShareSettings(settings);
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsShareSettingsLoading(false);
    }
  }

  async function updateShareSettings(payload: { regenerate_link?: boolean; share_enabled?: boolean }) {
    setIsShareSettingsLoading(true);
    try {
      const settings = await request<CollectionShareSettings>("/me/collection/share/", {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      setShareSettings(settings);
      return settings;
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
      return null;
    } finally {
      setIsShareSettingsLoading(false);
    }
  }

  async function copyShareLink() {
    let settings = shareSettings;
    if (!settings?.share_enabled || !settings.share_token) {
      settings = await updateShareSettings({ share_enabled: true });
    }

    const shareUrl = buildShareUrl(settings?.share_token ?? null);
    if (!shareUrl) {
      showToast({ tone: "error", text: "Impossible de generer le lien de partage." });
      return;
    }

    if (!navigator.clipboard) {
      showToast({ tone: "error", text: "La copie automatique n'est pas disponible dans ce navigateur." });
      return;
    }

    try {
      await navigator.clipboard.writeText(shareUrl);
      showToast({ tone: "success", text: "Lien de partage copie dans le presse-papiers." });
    } catch {
      showToast({ tone: "error", text: "La copie automatique du lien a echoue." });
    }
  }

  async function loadSharedCollections(preferredCollectionId?: number | null) {
    setIsSharedCollectionsLoading(true);
    try {
      const collections = await request<SharedCollectionSummary[]>("/me/friends/collections/");
      setSharedCollections(collections);
      setHasLoadedSharedCollectionsOnce(true);
      setActiveSharedCollectionId((current) => {
        if (preferredCollectionId && collections.some((collection) => collection.collection_id === preferredCollectionId)) {
          return preferredCollectionId;
        }
        if (current && collections.some((collection) => collection.collection_id === current)) {
          return current;
        }
        return collections[0]?.collection_id ?? null;
      });
      if (collections.length === 0) {
        setSharedCollectionBoard(null);
      }
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsSharedCollectionsLoading(false);
    }
  }

  async function loadSharedCollectionBoard(collectionId: number) {
    setIsSharedCollectionBoardLoading(true);
    try {
      const board = await request<SharedCollectionBoard>(`/me/friends/collections/${collectionId}/board/`);
      setSharedCollectionBoard(board);
    } catch (error) {
      setSharedCollectionBoard(null);
      showToast({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsSharedCollectionBoardLoading(false);
    }
  }

  async function joinSharedCollectionFromLink(shareToken: string) {
    try {
      const joined = await request<SharedCollectionSummary>("/me/collection/share/join/", {
        method: "POST",
        body: JSON.stringify({ share_token: shareToken }),
      });
      await loadSharedCollections(joined.collection_id);
      setActiveNav("friends");
      showToast({ tone: "success", text: `${joined.name} a ete ajoutee a l'onglet Mes amis.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    } finally {
      const nextUrl = new URL(window.location.href);
      nextUrl.searchParams.delete("share");
      window.history.replaceState({}, "", `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`);
    }
  }

  function revokeCollectionSubscriber(shareId: number, label: string) {
    setConfirmDialog({
      title: `Retirer l'acces de ${label} ?`,
      body: "Cette personne ne verra plus votre collection dans son onglet Mes amis.",
      confirmLabel: "Retirer l'acces",
      isDanger: true,
      onConfirm: () => void confirmRevokeCollectionSubscriber(shareId, label),
    });
  }

  async function confirmRevokeCollectionSubscriber(shareId: number, label: string) {
    try {
      await request(`/me/collection/share/subscribers/${shareId}`, { method: "DELETE" });
      await loadShareSettings();
      showToast({ tone: "success", text: `L'acces de ${label} a ete retire.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  function unsubscribeFromSharedCollection(collection: SharedCollectionSummary) {
    const ownerName = collection.owner?.username || collection.owner?.email || "cette collection";
    setConfirmDialog({
      title: `Se desabonner de ${collection.name} ?`,
      body: `La collection de ${ownerName} disparaitra de l'onglet Mes amis jusqu'a une nouvelle invitation.`,
      confirmLabel: "Se desabonner",
      isDanger: true,
      onConfirm: () => void confirmUnsubscribeFromSharedCollection(collection),
    });
  }

  async function confirmUnsubscribeFromSharedCollection(collection: SharedCollectionSummary) {
    try {
      await request(`/me/friends/collections/${collection.collection_id}/subscription/`, { method: "DELETE" });
      await loadSharedCollections(
        activeSharedCollectionId === collection.collection_id ? null : activeSharedCollectionId,
      );
      showToast({ tone: "success", text: `Vous etes desabonne de ${collection.name}.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function createReference(kind: ReferenceKey, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isReferenceAdmin) {
      showToast({ tone: "error", text: "Seul l'administrateur peut modifier les referentiels." });
      return;
    }

    const name = referenceDrafts[kind].trim();
    if (!name) {
      showToast({ tone: "error", text: `Le nom pour ${referenceTitles[kind].toLowerCase()} est requis.` });
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
      showToast({ tone: "success", text: `${referenceTitles[kind].slice(0, -1)} cree avec succes.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function deleteReference(kind: ReferenceKey, id: number) {
    if (!isReferenceAdmin) {
      showToast({ tone: "error", text: "Seul l'administrateur peut modifier les referentiels." });
      return;
    }

    const item = references[kind].find((entry) => entry.id === id);
    if (!item) {
      return;
    }

    setConfirmDialog({
      title: `Supprimer ${item.name} ?`,
      body: `Cette entree sera retiree du referentiel ${referenceTitles[kind].toLowerCase()} et des jeux qui l'utilisent.`,
      confirmLabel: "Supprimer",
      isDanger: true,
      onConfirm: () => void confirmDeleteReference(kind, id, item.name),
    });
  }

  async function renameReference(kind: ReferenceKey, id: number, name: string) {
    if (!isReferenceAdmin) {
      showToast({ tone: "error", text: "Seul l'administrateur peut modifier les referentiels." });
      return;
    }

    try {
      const renamed = await request<NamedEntity>(`/${referenceEndpoints[kind]}/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ name }),
      });
      setReferences((current) => ({
        ...current,
        [kind]: current[kind].map((entry) => (entry.id === id ? renamed : entry)),
      }));
      setGames((current) =>
        current.map((game) => ({
          ...game,
          [kind]: game[kind].map((entry) => (entry.id === id ? renamed : entry)),
        })),
      );
      showToast({ tone: "success", text: `${renamed.name} a ete enregistre.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function deleteGame(gameId: number) {
    if (!isReferenceAdmin) {
      showToast({ tone: "error", text: "Seul l'administrateur peut supprimer un jeu du catalogue." });
      return;
    }

    const game = games.find((entry) => entry.id === gameId);
    if (!game) {
      return;
    }

    setConfirmDialog({
      title: `Supprimer ${game.name} ?`,
      body: "Le jeu sera retire du catalogue Ludostock. Cette action peut aussi modifier les listes qui l'affichent.",
      confirmLabel: "Supprimer le jeu",
      isDanger: true,
      onConfirm: () => void confirmDeleteGame(gameId, game.name),
    });
  }

  async function confirmDeleteReference(kind: ReferenceKey, id: number, name: string) {
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
      showToast({ tone: "success", text: `${name} a ete supprime.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function confirmDeleteGame(gameId: number, name: string) {
    try {
      await request(`/games/${gameId}`, { method: "DELETE" });
      setGamesRefreshToken((current) => current + 1);
      if (hasLoadedCollectionOnce) {
        await loadCollectionBoard();
      }
      showToast({ tone: "success", text: `${name} a ete supprime.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function moveCollectionGame(collectionGameId: number, locationId: number | null) {
    const currentItem = collectionBoard?.items.find((item) => item.id === collectionGameId);
    const targetLocation = collectionBoard?.locations.find((location) => location.id === locationId);

    if (currentItem?.location_id === locationId) {
      return;
    }

    try {
      await request(`/me/collection/games/${collectionGameId}`, {
        method: "PATCH",
        body: JSON.stringify({ location_id: locationId }),
      });
      await loadCollectionBoard();
      showToast({ tone: "success", text: `Jeu deplace vers ${targetLocation?.name ?? "Sans lieu"}.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function addGameToCollection(gameId: number, gameName?: string) {
    const game = games.find((entry) => entry.id === gameId);
    const toastGameName = gameName ?? game?.name ?? "Ce jeu";
    setPendingCollectionGameIds((current) => (current.includes(gameId) ? current : [...current, gameId]));

    try {
      await request<CollectionGame>("/me/collection/games/", {
        method: "POST",
        body: JSON.stringify({ game_id: gameId }),
      });
      if (activeNav === "games" || activeNav === "locations" || hasLoadedCollectionOnce) {
        await loadCollectionBoard();
      }
      showToast({ tone: "success", text: `${toastGameName} a ete ajoute a votre collection.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setPendingCollectionGameIds((current) => current.filter((id) => id !== gameId));
    }
  }

  async function addQuickCatalogGameToCollection(game: Game) {
    await addGameToCollection(game.id, game.name);
    setQuickCatalogSearch("");
    setQuickCatalogResults([]);
    setIsQuickCatalogSearchOpen(false);
  }

  function removeGameFromCollection(collectionItem: CollectionItem) {
    setConfirmDialog({
      title: `Retirer ${collectionItem.game.name} ?`,
      body: "Le jeu sera retire de votre collection personnelle. Il restera disponible dans le Catalogue.",
      confirmLabel: "Retirer",
      isDanger: true,
      onConfirm: () => void confirmRemoveGameFromCollection(collectionItem),
    });
  }

  async function confirmRemoveGameFromCollection(collectionItem: CollectionItem) {
    try {
      await request(`/me/collection/games/${collectionItem.id}`, { method: "DELETE" });
      await loadCollectionBoard();
      showToast({ tone: "success", text: `${collectionItem.game.name} a ete retire de votre collection.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  async function createCollectionLocation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = locationDraft.trim();
    if (!name) {
      showToast({ tone: "error", text: "Le nom du lieu est requis." });
      return;
    }

    setIsCreatingLocation(true);
    try {
      await request<UserLocation>("/me/collection/locations/", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      setLocationDraft("");
      await loadCollectionBoard();
      showToast({ tone: "success", text: `Le lieu ${name} a ete cree.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    } finally {
      setIsCreatingLocation(false);
    }
  }

  function renameCollectionLocation(location: UserLocation) {
    const nextName = window.prompt("Nouveau nom du lieu", location.name);
    const name = nextName?.trim();

    if (!name || name === location.name) {
      return;
    }

    void confirmRenameCollectionLocation(location, name);
  }

  async function confirmRenameCollectionLocation(location: UserLocation, name: string) {
    try {
      const renamed = await request<UserLocation>(`/me/collection/locations/${location.id}`, {
        method: "PATCH",
        body: JSON.stringify({ name }),
      });
      await loadCollectionBoard();
      showToast({ tone: "success", text: `Le lieu ${renamed.name} a ete enregistre.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
    }
  }

  function deleteCollectionLocation(location: UserLocation) {
    setConfirmDialog({
      title: `Supprimer ${location.name} ?`,
      body: "Le lieu sera supprime. Les jeux ranges dedans resteront dans votre collection et passeront dans Sans lieu.",
      confirmLabel: "Supprimer le lieu",
      isDanger: true,
      onConfirm: () => void confirmDeleteCollectionLocation(location),
    });
  }

  async function confirmDeleteCollectionLocation(location: UserLocation) {
    try {
      await request<UserLocation>(`/me/collection/locations/${location.id}`, { method: "DELETE" });
      await loadCollectionBoard();
      showToast({ tone: "success", text: `Le lieu ${location.name} a ete supprime.` });
    } catch (error) {
      showToast({ tone: "error", text: getErrorMessage(error) });
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
      showToast({ tone: "error", text: getErrorMessage(error) });
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

  function openGamesCatalog() {
    setActiveNav("catalog");
  }

  const totalPages = Math.max(1, Math.ceil(totalGames / gamePageSize));
  const pageStart = totalGames === 0 ? 0 : (currentPage - 1) * gamePageSize + 1;
  const pageEnd = totalGames === 0 ? 0 : Math.min(currentPage * gamePageSize, totalGames);
  const collectionGameIds = new Set(collectionBoard?.items.map((item) => item.game_id) ?? []);
  const shareUrl = buildShareUrl(shareSettings?.share_token ?? null);
  const activeSharedCollection =
    sharedCollections.find((collection) => collection.collection_id === activeSharedCollectionId) ?? null;
  return (
    <div className="app-shell">
      <aside className="sidebar app-nav-shell">
        <div className="brand">
          <div className="brand-copy">
            <div className="brand-title-row">
              <p className="brand-title">Ludostock</p>
            </div>
          </div>
        </div>

        <nav className="nav-list mobile-tab-list flex overflow-x-auto" aria-label="Navigation principale">
          {visibleNavItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`nav-item mobile-tab-item shrink-0 ${activeNav === item.key ? "active" : ""}`}
              onClick={() => {
                setActiveNav(item.key);
                if (item.key === "games") {
                  setCollectionSearch("");
                }
              }}
            >
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="top-nav-actions" aria-label="Actions rapides">
          <div
            ref={quickCatalogMenuRef}
            className="top-search-menu"
          >
            <label className="top-search">
              <SearchIcon />
              <input
                aria-label="Rechercher un jeu a ajouter"
                value={quickCatalogSearch}
                onChange={(event) => {
                  setQuickCatalogSearch(event.target.value);
                  setIsQuickCatalogSearchOpen(true);
                }}
                onFocus={() => setIsQuickCatalogSearchOpen(true)}
                placeholder="Ajouter un jeu..."
              />
            </label>

            {isQuickCatalogSearchOpen && quickCatalogSearch.trim().length >= 2 ? (
              <section className="quick-catalog-panel" aria-label="Resultats du catalogue">
                {isQuickCatalogLoading ? (
                  <p className="quick-catalog-message">Recherche...</p>
                ) : quickCatalogResults.length === 0 ? (
                  <p className="quick-catalog-message">Aucun jeu trouve.</p>
                ) : (
                  <div className="quick-catalog-list">
                    {quickCatalogResults.map((game) => {
                      const isInCollection = collectionGameIds.has(game.id);
                      const isPending = pendingCollectionGameIds.includes(game.id);

                      return (
                        <article key={game.id} className="quick-catalog-result">
                          <div className="quick-catalog-media">
                            {game.image_url ? (
                              <img src={game.image_url} alt="" loading="lazy" />
                            ) : (
                              <span aria-hidden="true">{game.name.slice(0, 1).toUpperCase()}</span>
                            )}
                          </div>
                          <div className="quick-catalog-copy">
                            <strong>{game.name}</strong>
                            <small>{game.creation_year ?? "Annee inconnue"}</small>
                          </div>
                          {isInCollection ? (
                            <span className="status-pill compact-status-pill">Ajoute</span>
                          ) : (
                            <button
                              type="button"
                              className="primary-button icon-button"
                              disabled={isPending}
                              onMouseDown={(event) => event.preventDefault()}
                              onClick={() => void addQuickCatalogGameToCollection(game)}
                              aria-label={`Ajouter ${game.name} a ma collection`}
                              title="Ajouter a ma collection"
                            >
                              <PlusIcon />
                            </button>
                          )}
                        </article>
                      );
                    })}
                  </div>
                )}
              </section>
            ) : null}
          </div>
          <NotificationBell
            notifications={notificationLog}
            unreadCount={unreadCount}
            onMarkRead={markNotificationsAsRead}
          />
          <button type="button" className="top-avatar-button" onClick={() => setActiveNav("settings")} aria-label="Profil">
            {user.image ? <img src={user.image} alt="" /> : <span>{getUserInitial(user)}</span>}
          </button>
        </div>
      </aside>

      <main className="main-panel">
        {activeNav === "catalog" ? null : (
          <header className="topbar">
            <div className="section-intro">
              <h1>{activeNav === "home" ? `Bonjour ${getUserFirstName(user)}` : activeNavItem.label}</h1>
            </div>
          </header>
        )}

        {!hasLoadedOnce ? (
          <section className="loading-card">
            <h2>Chargement initial</h2>
            <p>Recuperation des jeux depuis FastAPI.</p>
          </section>
        ) : null}

        {activeNav === "home" ? (
          <HomeSection
            board={collectionBoard}
            catalogTotal={totalGames}
            hasLoadedCollectionOnce={hasLoadedCollectionOnce}
            onCatalogOpen={openGamesCatalog}
            onNavigate={setActiveNav}
          />
        ) : null}

        {activeNav === "games" ? (
          <div className="games-main">
            <LocationsManagerSection
              board={collectionBoard}
              hasLoadedOnce={hasLoadedCollectionOnce}
              isCreatingLocation={isCreatingLocation}
              isCollectionLoading={isCollectionLoading}
              locationDraft={locationDraft}
              onCreateLocation={createCollectionLocation}
              onDeleteLocation={deleteCollectionLocation}
              onLocationDraftChange={setLocationDraft}
              onRenameLocation={renameCollectionLocation}
            />

            <CollectionGamesSection
              board={collectionBoard}
              hasLoadedOnce={hasLoadedCollectionOnce}
              isCollectionLoading={isCollectionLoading}
              search={collectionSearch}
              onRemoveGame={removeGameFromCollection}
              onSearchClear={() => setCollectionSearch("")}
              onSearchChange={setCollectionSearch}
            />

            <LocationsSection
              board={collectionBoard}
              hasLoadedOnce={hasLoadedCollectionOnce}
              isCollectionLoading={isCollectionLoading}
              search={collectionSearch}
              onMoveGame={moveCollectionGame}
              onNavigateToCatalog={openGamesCatalog}
              onRemoveGame={removeGameFromCollection}
              onSearchClear={() => setCollectionSearch("")}
            />
          </div>
        ) : null}

        {activeNav === "friends" ? (
          <FriendsCollectionsSection
            activeCollection={activeSharedCollection}
            activeCollectionId={activeSharedCollectionId}
            board={sharedCollectionBoard}
            collections={sharedCollections}
            hasLoadedOnce={hasLoadedSharedCollectionsOnce}
            isBoardLoading={isSharedCollectionBoardLoading}
            isCollectionsLoading={isSharedCollectionsLoading}
            onSelectCollection={setActiveSharedCollectionId}
            onUnsubscribe={unsubscribeFromSharedCollection}
          />
        ) : null}

        {activeNav === "catalog" ? (
          <section className="games-catalog-reference" ref={gamesCatalogRef}>
            <section className="section-intro panel">
              <div className="catalog-title-row">
                <h2>Catalogue des jeux</h2>
                <span className="status-pill">{totalGames > 1 ? `${totalGames} jeux` : `${totalGames} jeu`}</span>
              </div>
            </section>

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
              collectionGameIds={collectionGameIds}
              pendingCollectionGameIds={pendingCollectionGameIds}
              canAdministerCatalog={isReferenceAdmin}
              onAddGameToCollection={addGameToCollection}
              onDeleteGame={deleteGame}
              onPageChange={setCurrentPage}
              onPageSizeChange={setGamePageSize}
              onSearchClear={() => setSearch("")}
              onSearchChange={setSearch}
              onSortChange={setGameSort}
            />
          </section>
        ) : null}

        {activeNav === "settings" ? (
          <section className="settings-layout">
            <ProfileSettingsPanel onSignOut={onSignOut} user={user} />

            <CollectionSharingSection
              isLoading={isShareSettingsLoading}
              settings={shareSettings}
              shareUrl={shareUrl}
              onCopyLink={() => void copyShareLink()}
              onDisableShare={() => void updateShareSettings({ share_enabled: false })}
              onEnableShare={() => void updateShareSettings({ share_enabled: true })}
              onRegenerateLink={() => void updateShareSettings({ share_enabled: true, regenerate_link: true })}
              onRevokeSubscriber={revokeCollectionSubscriber}
            />

            {isReferenceAdmin && hasLoadedOnce ? (
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
                onRenameReference={renameReference}
                onSelectReference={(kind) => void toggleReference(kind)}
              />
            ) : null}
          </section>
        ) : null}

        <footer className="app-footer panel" aria-label="Version de l'application">
          <span>Version {FRONTEND_VERSION}</span>
        </footer>
      </main>

      <ToastViewport notifications={toasts} onDismiss={dismissToast} />

      {confirmDialog ? (
        <ConfirmModal
          dialog={confirmDialog}
          onCancel={() => setConfirmDialog(null)}
          onConfirm={() => {
            const action = confirmDialog.onConfirm;
            setConfirmDialog(null);
            action();
          }}
        />
      ) : null}
    </div>
  );
}

function HomeSection({
  board,
  catalogTotal,
  hasLoadedCollectionOnce,
  onCatalogOpen,
  onNavigate,
}: {
  board: CollectionBoard | null;
  catalogTotal: number;
  hasLoadedCollectionOnce: boolean;
  onCatalogOpen: () => void;
  onNavigate: (navKey: NavKey) => void;
}) {
  const collectionTotal = board?.items.length ?? 0;
  const locationTotal = board?.locations.length ?? 0;
  const visibleLocations = board?.locations.slice(0, 3) ?? [];
  const unassignedTotal = board?.items.filter((item) => item.location_id === null).length ?? 0;
  const latestItems = board?.items.slice(-4).reverse() ?? [];
  const locationNames = new Map((board?.locations ?? []).map((location) => [location.id, location.name]));
  const locationSummaries = visibleLocations.map((location) => ({
    ...location,
    count: board?.items.filter((item) => item.location_id === location.id).length ?? 0,
  }));

  return (
    <section className="home-layout home-dashboard">
      <section className="home-command-center">
        <div className="home-stat-stack home-stat-stack-simple" aria-label="Synthese de ma collection">
          <article className="home-stat-card">
            <span className="stat-icon-box">
              <GamesIcon />
            </span>
            <strong>{hasLoadedCollectionOnce ? collectionTotal : "..."}</strong>
            <span>Jeux de societe</span>
          </article>

          <article className="home-stat-card">
            <span className="stat-icon-box">
              <LocationIcon />
            </span>
            <strong>{hasLoadedCollectionOnce ? locationTotal : "..."}</strong>
            <span>Lieux de stockage</span>
          </article>

          <article className="home-stat-card">
            <span className="stat-icon-box">
              <LocationIcon />
            </span>
            <strong>{hasLoadedCollectionOnce ? unassignedTotal : "..."}</strong>
            <span>{unassignedTotal > 1 ? "Jeux a ranger" : "Jeu a ranger"}</span>
          </article>
        </div>
      </section>

      <section className="dashboard-section">
        <div className="section-heading-row">
          <div>
            <h2>Derniers ajouts</h2>
          </div>
          <button type="button" className="link-button" onClick={() => onNavigate("games")}>
            Tout voir +
          </button>
        </div>

        <div className="recent-game-strip">
          {latestItems.length > 0 ? (
            latestItems.map((item) => (
              <article key={item.id} className="recent-game-card">
                <div className="recent-game-media">
                  {item.game.image_url ? (
                    <img src={item.game.image_url} alt={item.game.name} loading="lazy" />
                  ) : (
                    <div className="collection-card-fallback" aria-hidden="true">
                      {item.game.name.slice(0, 1).toUpperCase()}
                    </div>
                  )}
                </div>
                <p>{item.game.type || "Jeu"}</p>
                <h3>{item.game.name}</h3>
                <span>{item.location_id ? locationNames.get(item.location_id) ?? "Lieu inconnu" : "Sans lieu"}</span>
              </article>
            ))
          ) : (
            <button type="button" className="recent-game-card recent-game-empty" onClick={onCatalogOpen}>
              <span className="stat-icon-box">
                <PlusIcon />
              </span>
              <h3>Ajouter votre premier jeu</h3>
              <p>{catalogTotal} references disponibles</p>
            </button>
          )}
        </div>
      </section>

      <section className="dashboard-section">
        <div className="section-heading-row">
          <div>
            <h2>Lieux principaux</h2>
          </div>
        </div>

        <div className="primary-location-list">
          {locationSummaries.length > 0 ? (
            locationSummaries.map((location) => (
              <button key={location.id} type="button" className="primary-location-row" onClick={() => onNavigate("games")}>
                <span className="location-row-icon">
                  <LocationIcon />
                </span>
                <span>
                  <strong>{location.name}</strong>
                  <small>{location.count > 1 ? `${location.count} jeux stockes` : `${location.count} jeu stocke`}</small>
                </span>
                <span aria-hidden="true">›</span>
              </button>
            ))
          ) : (
            <button type="button" className="primary-location-row" onClick={() => onNavigate("games")}>
              <span className="location-row-icon">
                <LocationIcon />
              </span>
              <span>
                <strong>Aucun lieu</strong>
                <small>Creez votre premier ecosysteme de rangement</small>
              </span>
              <span aria-hidden="true">›</span>
            </button>
          )}
        </div>
      </section>
    </section>
  );
}

function LocationsManagerSection(props: {
  board: CollectionBoard | null;
  hasLoadedOnce: boolean;
  isCreatingLocation: boolean;
  isCollectionLoading: boolean;
  locationDraft: string;
  onCreateLocation: (event: FormEvent<HTMLFormElement>) => void;
  onDeleteLocation: (location: UserLocation) => void;
  onLocationDraftChange: (value: string) => void;
  onRenameLocation: (location: UserLocation) => void;
}) {
  const {
    board,
    hasLoadedOnce,
    isCreatingLocation,
    isCollectionLoading,
    locationDraft,
    onCreateLocation,
    onDeleteLocation,
    onLocationDraftChange,
    onRenameLocation,
  } = props;
  const locations = board?.locations ?? [];

  return (
    <section className="panel collection-actions">
      <div className="section-intro compact">
        <h2>Mes lieux</h2>
      </div>

      <form className="entity-form location-form" onSubmit={onCreateLocation}>
        <input
          aria-label="Mes lieux"
          value={locationDraft}
          onChange={(event) => onLocationDraftChange(event.target.value)}
          placeholder="Ajouter un lieu"
        />
        <button
          type="submit"
          className="primary-button icon-button"
          disabled={isCreatingLocation}
          aria-label={isCreatingLocation ? "Creation du lieu en cours" : "Ajouter le lieu"}
          title={isCreatingLocation ? "Creation..." : "Ajouter"}
        >
          <PlusIcon />
        </button>
      </form>

      {!hasLoadedOnce || isCollectionLoading ? (
        <div className="empty-state compact">
          <h3>Chargement</h3>
          <p>Recuperation de vos lieux.</p>
        </div>
      ) : locations.length === 0 ? (
        <div className="empty-state compact">
          <h3>Aucun lieu</h3>
          <p>Les jeux sans lieu restent disponibles dans la colonne Sans lieu.</p>
        </div>
      ) : (
        <div className="managed-location-list">
          {locations.map((location) => (
            <article key={location.id} className="managed-location-row">
              <div className="managed-location-copy">
                <span className="location-row-icon" aria-hidden="true">
                  <LocationIcon />
                </span>
                <div>
                  <strong>{location.name}</strong>
                  <small>
                    {(board?.items.filter((item) => item.location_id === location.id).length ?? 0) > 1
                      ? `${board?.items.filter((item) => item.location_id === location.id).length ?? 0} jeux`
                      : `${board?.items.filter((item) => item.location_id === location.id).length ?? 0} jeu`}
                  </small>
                </div>
              </div>
              <div className="row-actions">
                <button
                  type="button"
                  className="secondary-button icon-button"
                  onClick={() => onRenameLocation(location)}
                  aria-label={`Modifier le lieu ${location.name}`}
                  title="Modifier"
                >
                  <PencilIcon />
                </button>
                <button
                  type="button"
                  className="secondary-button icon-button danger-icon"
                  onClick={() => onDeleteLocation(location)}
                  aria-label={`Supprimer le lieu ${location.name}`}
                  title="Supprimer"
                >
                  <TrashIcon />
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function CollectionGamesSection(props: {
  board: CollectionBoard | null;
  hasLoadedOnce: boolean;
  isCollectionLoading: boolean;
  search: string;
  onRemoveGame: (item: CollectionItem) => void;
  onSearchClear: () => void;
  onSearchChange: (value: string) => void;
}) {
  const {
    board,
    hasLoadedOnce,
    isCollectionLoading,
    search,
    onRemoveGame,
    onSearchClear,
    onSearchChange,
  } = props;
  const [hoveredGameId, setHoveredGameId] = useState<number | null>(null);
  const normalizedSearch = search.trim().toLowerCase();
  const items = (board?.items ?? [])
    .filter((item) => (normalizedSearch ? item.game.name.toLowerCase().includes(normalizedSearch) : true))
    .sort((left, right) => left.game.name.localeCompare(right.game.name, "fr"));
  const locationNames = new Map((board?.locations ?? []).map((location) => [location.id, location.name]));

  return (
    <section className="games-layout">
      <section className="panel games-search">
        <label className="games-search-field">
          <span>Recherche</span>
          <input
            aria-label="Rechercher dans mes jeux"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Nom du jeu"
          />
        </label>
      </section>

      <section className="panel collection-actions">
        <div className="section-intro compact">
          <h2>Mes jeux</h2>
        </div>
      </section>

      {!hasLoadedOnce || isCollectionLoading ? (
        <section className="loading-card">
          <h2>Chargement</h2>
          <p>Recuperation de votre collection.</p>
        </section>
      ) : items.length === 0 ? (
        <section className="panel empty-state">
          <h3>{search.trim() ? "Aucun jeu trouve" : "Aucun jeu dans votre collection"}</h3>
          <p>{search.trim() ? "Essayez une autre recherche." : "Votre collection est vide."}</p>
          {search.trim() ? (
            <button type="button" className="secondary-button" onClick={onSearchClear}>
              Effacer la recherche
            </button>
          ) : null}
        </section>
      ) : (
        <section className="collection-game-grid">
          {items.map((item) => (
            <article key={item.id} className="panel collection-card collection-game-tile">
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
              <div className="collection-card-facts">
                <CompactGameFact kind="players" label="Nombre de joueurs" value={formatPlayers(item.game)} />
                <CompactGameFact kind="duration" label="Duree" value={formatDuration(item.game.duration_minutes)} />
              </div>
              <p className="collection-card-copy">Lieu : {item.location_id ? locationNames.get(item.location_id) ?? "Lieu inconnu" : "Sans lieu"}</p>
              <button type="button" className="secondary-button compact-button" onClick={() => onRemoveGame(item)}>
                Retirer
              </button>
            </article>
          ))}
        </section>
      )}
    </section>
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

function ToastViewport({
  notifications,
  onDismiss,
}: {
  notifications: ToastNotification[];
  onDismiss: (id: number) => void;
}) {
  if (notifications.length === 0) {
    return null;
  }

  return createPortal(
    <section className="toast-viewport" aria-label="Notifications">
      {notifications.map((notification) => (
        <article
          key={notification.id}
          className={`toast toast-${notification.tone}`}
          role={notification.tone === "error" ? "alert" : "status"}
        >
          <div className="toast-copy">
            <p className="toast-title">{notification.tone === "error" ? "Attention" : "Notification"}</p>
            <p>{notification.text}</p>
          </div>
          <button
            type="button"
            className="toast-dismiss"
            onClick={() => onDismiss(notification.id)}
            aria-label="Fermer la notification"
          >
            x
          </button>
        </article>
      ))}
    </section>,
    document.body,
  );
}

function NotificationBell({
  notifications,
  onMarkRead,
  unreadCount,
}: {
  notifications: ToastNotification[];
  onMarkRead: () => void;
  unreadCount: number;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
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
    if (isOpen) {
      onMarkRead();
    }
  }, [isOpen, notifications.length, onMarkRead]);

  function toggleMenu() {
    setIsOpen((current) => !current);
  }

  return (
    <div className="notification-menu" ref={menuRef}>
      <button
        type="button"
        className="top-icon-button notification-trigger"
        aria-label={unreadCount > 0 ? `${unreadCount} notification(s) non lue(s)` : "Notifications"}
        aria-expanded={isOpen}
        onClick={toggleMenu}
      >
        <BellIcon />
        {unreadCount > 0 ? <span className="notification-badge">{unreadCount}</span> : null}
      </button>

      {isOpen ? (
        <section className="notification-panel" aria-label="Notifications recentes">
          <div className="notification-panel-header">
            <h2>Notifications</h2>
          </div>

          {notifications.length === 0 ? (
            <p className="notification-empty">Aucune notification pour le moment.</p>
          ) : (
            <div className="notification-list">
              {notifications.map((notification) => (
                <article key={notification.id} className={`notification-item notification-item-${notification.tone}`}>
                  <p className="notification-item-title">
                    {notification.tone === "error" ? "Attention" : "Information"}
                  </p>
                  <p>{notification.text}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}

function ConfirmModal({
  dialog,
  onCancel,
  onConfirm,
}: {
  dialog: ConfirmDialog;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return createPortal(
    <div className="modal-backdrop" role="presentation" onMouseDown={onCancel}>
      <section
        className="modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="section-intro compact">
          <p className="eyebrow">{dialog.isDanger ? "Action irreversible" : "Confirmation"}</p>
          <h2 id="confirm-dialog-title">{dialog.title}</h2>
          <p>{dialog.body}</p>
        </div>
        <div className="form-actions">
          <button type="button" className="secondary-button" onClick={onCancel}>
            Annuler
          </button>
          <button
            type="button"
            className={dialog.isDanger ? "danger-button" : "primary-button"}
            onClick={onConfirm}
          >
            {dialog.confirmLabel ?? "Confirmer"}
          </button>
        </div>
      </section>
    </div>,
    document.body,
  );
}

function GamesSection(props: {
  canAdministerCatalog: boolean;
  collectionGameIds: Set<number>;
  currentPage: number;
  games: Game[];
  isGamesLoading: boolean;
  pageEnd: number;
  pageSize: number;
  pendingCollectionGameIds: number[];
  pageStart: number;
  search: string;
  sortValue: GameSortValue;
  totalGames: number;
  totalPages: number;
  onAddGameToCollection: (gameId: number) => void;
  onDeleteGame: (gameId: number) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (value: number) => void;
  onSearchClear: () => void;
  onSearchChange: (value: string) => void;
  onSortChange: (value: GameSortValue) => void;
}) {
  const [hoveredGameId, setHoveredGameId] = useState<number | null>(null);
  const {
    canAdministerCatalog,
    collectionGameIds,
    currentPage,
    games,
    isGamesLoading,
    pageEnd,
    pageSize,
    pendingCollectionGameIds,
    pageStart,
    search,
    sortValue,
    totalGames,
    totalPages,
    onAddGameToCollection,
    onDeleteGame,
    onPageChange,
    onPageSizeChange,
    onSearchClear,
    onSearchChange,
    onSortChange,
  } = props;
  const paginationItems = buildPaginationItems(currentPage, totalPages);
  const resultLabel =
    totalGames === 0 ? "Aucun resultat" : `${pageStart}-${pageEnd} sur ${totalGames}`;

  return (
    <section className="games-layout">
      <section className="panel games-search">
        <label className="games-search-field games-search-field-icon">
          <SearchIcon />
          <input
            aria-label="Rechercher un jeu"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Rechercher un jeu..."
          />
        </label>
      </section>

      <section className="panel games-content">
        <div className="games-controls">
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
            <div>Collection</div>
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
                {search.trim() ? (
                  <button type="button" className="secondary-button" onClick={onSearchClear}>
                    Effacer la recherche
                  </button>
                ) : null}
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
                  <div className="row-actions">
                    {collectionGameIds.has(game.id) ? (
                      <span className="status-pill">Dans ma collection</span>
                    ) : (
                      <button
                        type="button"
                        className="secondary-button compact-button"
                        disabled={pendingCollectionGameIds.includes(game.id)}
                        onClick={() => onAddGameToCollection(game.id)}
                      >
                        {pendingCollectionGameIds.includes(game.id) ? "Ajout..." : "Ajouter"}
                      </button>
                    )}
                    {canAdministerCatalog ? (
                      <button type="button" className="link-button danger" onClick={() => onDeleteGame(game.id)}>
                        Supprimer
                      </button>
                    ) : null}
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

function LocationsSection(props: {
  board: CollectionBoard | null;
  hasLoadedOnce: boolean;
  isCollectionLoading: boolean;
  search: string;
  onMoveGame: (collectionGameId: number, locationId: number | null) => void;
  onNavigateToCatalog: () => void;
  onRemoveGame: (item: CollectionItem) => void;
  onSearchClear: () => void;
}) {
  const {
    board,
    hasLoadedOnce,
    isCollectionLoading,
    search,
    onMoveGame,
    onNavigateToCatalog,
    onRemoveGame,
    onSearchClear,
  } = props;
  const normalizedSearch = search.trim().toLowerCase();
  const locations = [{ id: null, name: "Sans lieu" }, ...(board?.locations ?? [])];
  const items = (board?.items ?? []).filter((item) =>
    normalizedSearch ? item.game.name.toLowerCase().includes(normalizedSearch) : true,
  );
  const hasBoardStructure = (board?.items.length ?? 0) > 0 || (board?.locations.length ?? 0) > 0;
  const locationOptions = locations.map((location) => ({ id: location.id, name: location.name }));

  return (
    <section className="games-layout">
      <section className="panel games-content">
        <div className="games-controls">
          <div className="section-intro compact">
            <h2>Rangement par lieu</h2>
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
              <button type="button" className="primary-button" onClick={onNavigateToCatalog}>
                Parcourir le catalogue
              </button>
            </div>
          ) : (
            <>
              {items.length === 0 && search.trim() ? (
                <div className="empty-inline">
                  <p>Aucun jeu ne correspond a votre recherche dans les lieux affiches.</p>
                  <button type="button" className="secondary-button compact-button" onClick={onSearchClear}>
                    Effacer la recherche
                  </button>
                </div>
              ) : null}
              {locations.map((location) => (
                <CollectionLocationColumn
                  key={location.id ?? "unassigned"}
                  items={items.filter((item) => item.location_id === location.id)}
                  locationName={location.name}
                  locationOptions={locationOptions}
                  onMoveGame={onMoveGame}
                  onRemoveGame={onRemoveGame}
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
  locationOptions: { id: number | null; name: string }[];
  onMoveGame: (collectionGameId: number, locationId: number | null) => void;
  onRemoveGame: (item: CollectionItem) => void;
  targetLocationId: number | null;
}) {
  const [hoveredGameId, setHoveredGameId] = useState<number | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const { items, locationName, locationOptions, onMoveGame, onRemoveGame, targetLocationId } = props;

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
            <p>Deposez un jeu ici ou utilisez le menu d'une carte.</p>
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
                <div
                  className="collection-card-media"
                  onMouseEnter={() => setHoveredGameId(item.id)}
                  onMouseLeave={() => setHoveredGameId((current) => (current === item.id ? null : current))}
                  onFocus={() => setHoveredGameId(item.id)}
                  onBlur={() => setHoveredGameId((current) => (current === item.id ? null : current))}
                  tabIndex={0}
                >
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
                <label className="move-control">
                  <select
                    aria-label={`Deplacer ${item.game.name}`}
                    value={String(item.location_id ?? "")}
                    onChange={(event) => {
                      const value = event.target.value;
                      onMoveGame(item.id, value ? Number(value) : null);
                    }}
                  >
                    {locationOptions.map((location) => (
                      <option key={location.id ?? "unassigned"} value={location.id ?? ""}>
                        {location.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="button" className="secondary-button compact-button" onClick={() => onRemoveGame(item)}>
                  Retirer
                </button>
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

function ProfileSettingsPanel({ onSignOut, user }: { onSignOut: () => void; user: AuthenticatedUser }) {
  return (
    <section className="panel profile-settings-panel">
      <div className="profile-dropdown-header">
        <div className="profile-dropdown-avatar" aria-hidden="true">
          {user.image ? <img src={user.image} alt="" /> : <span>{getUserInitial(user)}</span>}
        </div>
        <div className="profile-dropdown-copy">
          <p className="eyebrow">Profil</p>
          <strong>{user.name || "Utilisateur Google"}</strong>
          <span>{user.email || "Adresse e-mail indisponible"}</span>
        </div>
      </div>

      <button type="button" className="secondary-button profile-signout" onClick={onSignOut}>
        Se deconnecter
      </button>
    </section>
  );
}

function CollectionSharingSection(props: {
  isLoading: boolean;
  settings: CollectionShareSettings | null;
  shareUrl: string;
  onCopyLink: () => void;
  onDisableShare: () => void;
  onEnableShare: () => void;
  onRegenerateLink: () => void;
  onRevokeSubscriber: (shareId: number, label: string) => void;
}) {
  const {
    isLoading,
    settings,
    shareUrl,
    onCopyLink,
    onDisableShare,
    onEnableShare,
    onRegenerateLink,
    onRevokeSubscriber,
  } = props;
  const subscriberCount = settings?.subscribers.length ?? 0;

  return (
    <section className="panel sharing-settings-panel">
      <div className="section-intro compact">
        <p className="eyebrow">Partage</p>
        <h2>Partager ma collection</h2>
        <p>Activez un lien d'invitation, copiez-le, puis gerez les personnes qui peuvent encore voir votre collection.</p>
      </div>

      <div className="sharing-status-row">
        <span className="status-pill">{settings?.share_enabled ? "Lien actif" : "Lien inactif"}</span>
        <span className="sharing-status-copy">
          {subscriberCount > 1 ? `${subscriberCount} abonnes` : `${subscriberCount} abonne`}
        </span>
      </div>

      <div className="sharing-actions-row">
        <button
          type="button"
          className="primary-button"
          disabled={isLoading}
          onClick={settings?.share_enabled ? onCopyLink : onEnableShare}
        >
          {settings?.share_enabled ? "Copier le lien" : "Activer le partage"}
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={isLoading || !settings?.share_token}
          onClick={onRegenerateLink}
        >
          Regenerer le lien
        </button>
        <button
          type="button"
          className="secondary-button"
          disabled={isLoading || !settings?.share_enabled}
          onClick={onDisableShare}
        >
          Desactiver le lien
        </button>
      </div>

      <label className="field sharing-link-field">
        <span>Lien de partage</span>
        <input
          readOnly
          value={settings?.share_token ? shareUrl : "Activez le partage pour generer un lien."}
          aria-label="Lien de partage de ma collection"
        />
      </label>

      <div className="simple-table">
        <div className="simple-head">
          <span>Acces autorises</span>
          <span>Action</span>
        </div>

        {isLoading && !settings ? (
          <div className="empty-state compact">
            <h3>Chargement</h3>
            <p>Recuperation des droits de partage.</p>
          </div>
        ) : subscriberCount === 0 ? (
          <div className="empty-state compact">
            <h3>Aucun abonne</h3>
            <p>Les personnes qui utiliseront votre lien apparaitront ici.</p>
          </div>
        ) : (
          settings?.subscribers.map((subscriber) => {
            const label = subscriber.user?.username || subscriber.user?.email || "Utilisateur";
            return (
              <div key={subscriber.id} className="simple-row">
                <span className="simple-row-name">
                  <strong>{label}</strong>
                  <small>{subscriber.user?.email || "Adresse indisponible"}</small>
                </span>
                <button
                  type="button"
                  className="secondary-button compact-button"
                  onClick={() => onRevokeSubscriber(subscriber.id, label)}
                >
                  Retirer l'acces
                </button>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

function FriendsCollectionsSection(props: {
  activeCollection: SharedCollectionSummary | null;
  activeCollectionId: number | null;
  board: SharedCollectionBoard | null;
  collections: SharedCollectionSummary[];
  hasLoadedOnce: boolean;
  isBoardLoading: boolean;
  isCollectionsLoading: boolean;
  onSelectCollection: (collectionId: number) => void;
  onUnsubscribe: (collection: SharedCollectionSummary) => void;
}) {
  const {
    activeCollection,
    activeCollectionId,
    board,
    collections,
    hasLoadedOnce,
    isBoardLoading,
    isCollectionsLoading,
    onSelectCollection,
    onUnsubscribe,
  } = props;
  const [search, setSearch] = useState("");
  const ownerName = activeCollection?.owner?.username || activeCollection?.owner?.email || "Votre ami";
  const normalizedSearch = search.trim().toLowerCase();
  const items = (board?.items ?? [])
    .filter((item) => (normalizedSearch ? item.game.name.toLowerCase().includes(normalizedSearch) : true))
    .slice()
    .sort((left, right) => left.game.name.localeCompare(right.game.name, "fr"));
  const hasGames = (board?.items.length ?? 0) > 0;

  useEffect(() => {
    setSearch("");
  }, [activeCollectionId]);

  return (
    <section className="friends-layout">
      <section className="panel friends-sidebar-panel">
        <div className="section-intro compact">
          <p className="eyebrow">Mes amis</p>
          <h2>Collections partagees</h2>
          <p>Retrouvez ici les ludotheques auxquelles vous etes abonne.</p>
        </div>

        {!hasLoadedOnce && isCollectionsLoading ? (
          <div className="empty-state compact">
            <h3>Chargement</h3>
            <p>Recuperation de vos collections partagees.</p>
          </div>
        ) : collections.length === 0 ? (
          <div className="empty-state compact">
            <h3>Aucune collection</h3>
            <p>Ouvrez un lien de partage pour ajouter automatiquement une collection a cet onglet.</p>
          </div>
        ) : (
          <div className="friends-collection-list">
            {collections.map((collection) => {
              const isActive = collection.collection_id === activeCollectionId;
              const friendLabel = collection.owner?.username || collection.owner?.email || "Collection partagee";

              return (
                <button
                  key={collection.collection_id}
                  type="button"
                  className={`friends-collection-card ${isActive ? "friends-collection-card-active" : ""}`}
                  onClick={() => onSelectCollection(collection.collection_id)}
                >
                  <span className="eyebrow">Partage par {friendLabel}</span>
                  <strong>{collection.name}</strong>
                  <small>{collection.game_count > 1 ? `${collection.game_count} jeux` : `${collection.game_count} jeu`}</small>
                </button>
              );
            })}
          </div>
        )}
      </section>

      <section className="panel friends-board-panel">
        {!activeCollection ? (
          <div className="empty-state">
            <h3>Selectionnez une collection</h3>
            <p>Choisissez une collection dans la liste pour parcourir son contenu.</p>
          </div>
        ) : (
          <>
            <div className="friends-board-header">
              <div className="section-intro compact">
                <p className="eyebrow">Collection de {ownerName}</p>
                <h2>{activeCollection.name}</h2>
                <p>{activeCollection.description || "Collection partagee en lecture seule."}</p>
              </div>
              <button type="button" className="secondary-button" onClick={() => onUnsubscribe(activeCollection)}>
                Se desabonner
              </button>
            </div>

            {isBoardLoading ? (
              <div className="empty-state">
                <h3>Chargement</h3>
                <p>Recuperation de la collection de {ownerName}.</p>
              </div>
            ) : !hasGames ? (
              <div className="empty-state">
                <h3>Collection vide</h3>
                <p>Cette collection ne contient encore aucun jeu.</p>
              </div>
            ) : (
              <>
                <section className="panel games-search friends-search-panel">
                  <label className="games-search-field">
                    <span>Recherche</span>
                    <input
                      aria-label="Rechercher dans la collection de votre ami"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Nom du jeu"
                    />
                  </label>
                </section>

                {items.length === 0 ? (
                  <div className="empty-state">
                    <h3>Aucun jeu trouve</h3>
                    <p>Essayez une autre recherche.</p>
                  </div>
                ) : (
                  <section className="collection-game-grid">
                    {items.map((item) => (
                      <SharedCollectionGameCard key={item.id} item={item} />
                    ))}
                  </section>
                )}
              </>
            )}
          </>
        )}
      </section>
    </section>
  );
}

function SharedCollectionGameCard(props: { item: CollectionItem }) {
  const [hoveredGameId, setHoveredGameId] = useState<number | null>(null);
  const { item } = props;

  return (
    <article className="panel collection-card collection-game-tile collection-card-readonly">
      <div
        className="collection-card-media"
        onMouseEnter={() => setHoveredGameId(item.id)}
        onMouseLeave={() => setHoveredGameId((current) => (current === item.id ? null : current))}
        onFocus={() => setHoveredGameId(item.id)}
        onBlur={() => setHoveredGameId((current) => (current === item.id ? null : current))}
        tabIndex={0}
      >
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
      <div className="collection-card-facts">
        <CompactGameFact kind="year" label="Annee de publication" value={String(item.game.creation_year ?? "-")} />
        <CompactGameFact kind="players" label="Nombre de joueurs" value={formatPlayers(item.game)} />
        <CompactGameFact kind="duration" label="Duree" value={formatDuration(item.game.duration_minutes)} />
      </div>
    </article>
  );
}

function NavIcon({ kind }: { kind: NavigationItem["key"] }) {
  if (kind === "home") {
    return <HomeIcon />;
  }

  if (kind === "catalog" || kind === "games") {
    return <GamesIcon />;
  }

  if (kind === "locations") {
    return <LocationIcon />;
  }

  return <SettingsIcon />;
}

function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="nav-icon">
      <path
        d="M4 11.5 12 4l8 7.5V20a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-8.5Z"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function GamesIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="nav-icon">
      <path
        d="M6 4h10a2 2 0 0 1 2 2v14H8a2 2 0 0 1-2-2V4Zm0 14a2 2 0 0 1 2-2h10M9 7h6"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function LocationIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="nav-icon">
      <path
        d="M12 21s7-5.1 7-11a7 7 0 1 0-14 0c0 5.9 7 11 7 11Zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="nav-icon">
      <path
        d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm7.4 4.8a7.7 7.7 0 0 0 0-2.6l2-1.5-2-3.4-2.4 1a8 8 0 0 0-2.2-1.3L14.5 3h-5l-.3 2.5A8 8 0 0 0 7 6.8l-2.4-1-2 3.4 2 1.5a7.7 7.7 0 0 0 0 2.6l-2 1.5 2 3.4 2.4-1a8 8 0 0 0 2.2 1.3l.3 2.5h5l.3-2.5a8 8 0 0 0 2.2-1.3l2.4 1 2-3.4-2-1.5Z"
        fill="none"
        stroke="currentColor"
        strokeLinejoin="round"
        strokeWidth="1.5"
      />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="button-icon">
      <path
        d="m19 19-4.2-4.2m1.7-4.3a6 6 0 1 1-12 0 6 6 0 0 1 12 0Z"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="button-icon">
      <path
        d="M7.5 10.5a4.5 4.5 0 1 1 9 0c0 4 1.5 4.6 1.5 6H6c0-1.4 1.5-2 1.5-6ZM10 19h4"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="button-icon">
      <path
        d="M12 5v14M5 12h14"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function PencilIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="button-icon">
      <path
        d="m4 20 4.4-1 10.1-10.1a2.1 2.1 0 0 0-3-3L5.4 16 4 20ZM14.2 7.2l2.6 2.6"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="button-icon">
      <path
        d="M5 7h14M10 11v6M14 11v6M8 7l1-3h6l1 3M7 7l1 13h8l1-13"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
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
  onRenameReference: (kind: ReferenceKey, id: number, name: string) => Promise<void>;
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
    onRenameReference,
    onSelectReference,
  } = props;

  function promptRenameReference(kind: ReferenceKey, item: NamedEntity) {
    const name = window.prompt(`Renommer ${item.name}`, item.name);
    if (name === null) {
      return;
    }

    const trimmedName = name.trim();
    if (!trimmedName || trimmedName === item.name) {
      return;
    }

    void onRenameReference(kind, item.id, trimmedName);
  }

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
                  <form className="entity-form" onSubmit={(event) => void onCreateReference(kind, event)}>
                    <input
                      value={drafts[kind]}
                      aria-label={`Ajouter un ${referenceTitles[kind].slice(0, -1).toLowerCase()}`}
                      onChange={(event) => onDraftChange((current) => ({ ...current, [kind]: event.target.value }))}
                      placeholder={`Ajouter un ${referenceTitles[kind].slice(0, -1).toLowerCase()}`}
                    />
                    <button
                      type="submit"
                      className="primary-button icon-button entity-add-button"
                      aria-label={`Ajouter un ${referenceTitles[kind].slice(0, -1).toLowerCase()}`}
                      title={`Ajouter un ${referenceTitles[kind].slice(0, -1).toLowerCase()}`}
                    >
                      <PlusIcon />
                    </button>
                  </form>

                  <div className="simple-table">
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
                          <span className="simple-row-name">{item.name}</span>
                          <div className="entity-row-actions">
                            <button
                              type="button"
                              className="icon-button secondary-button"
                              onClick={() => promptRenameReference(kind, item)}
                              aria-label={`Modifier ${item.name}`}
                              title={`Modifier ${item.name}`}
                            >
                              <PencilIcon />
                            </button>
                            <button
                              type="button"
                              className="icon-button secondary-button danger-icon"
                              onClick={() => void onDeleteReference(kind, item.id)}
                              aria-label={`Supprimer ${item.name}`}
                              title={`Supprimer ${item.name}`}
                            >
                              <TrashIcon />
                            </button>
                          </div>
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

function getUserFirstName(user: AuthenticatedUser) {
  const label = user.name?.trim() || user.email?.split("@")[0]?.trim() || "joueur";
  return label.split(/\s+/)[0] || "joueur";
}

export default App;
