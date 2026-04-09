export type NavKey = "home" | "catalog" | "games" | "locations" | "settings";
export type ReferenceKey = "authors" | "artists" | "editors" | "distributors";

export type NamedEntity = {
  id: number;
  name: string;
};

export type Game = {
  id: number;
  name: string;
  type: string;
  extension_of_id: number | null;
  creation_year: number | null;
  min_players: number | null;
  max_players: number | null;
  min_age: number | null;
  duration_minutes: number | null;
  url: string | null;
  image_url: string | null;
  authors: NamedEntity[];
  artists: NamedEntity[];
  editors: NamedEntity[];
  distributors: NamedEntity[];
};

export type GamePage = {
  items: Game[];
  total: number;
  skip: number;
  limit: number;
};

export type UserLocation = {
  id: number;
  user_id: string;
  name: string;
};

export type CollectionItem = {
  id: number;
  collection_id: number;
  game_id: number;
  location_id: number | null;
  quantity: number | null;
  game: Game;
};

export type CollectionGame = {
  id: number;
  collection_id: number;
  game_id: number;
  location_id: number | null;
  quantity: number | null;
};

export type CollectionBoard = {
  collection_id: number;
  locations: UserLocation[];
  items: CollectionItem[];
};

export type GameFormState = {
  name: string;
  type: string;
  extension_of_id: string;
  creation_year: string;
  min_players: string;
  max_players: string;
  min_age: string;
  duration_minutes: string;
  url: string;
  image_url: string;
  authors: string;
  artists: string;
  editors: string;
  distributors: string;
};

export type ReferenceCollection = Record<ReferenceKey, NamedEntity[]>;
export type ReferenceDrafts = Record<ReferenceKey, string>;

export const navItems: { key: NavKey; label: string }[] = [
  { key: "home", label: "Accueil" },
  { key: "catalog", label: "Catalogue" },
  { key: "games", label: "Ma collection" },
  { key: "locations", label: "Lieux" },
  { key: "settings", label: "Parametres" },
];

export const referenceNavItems: ReferenceKey[] = ["authors", "artists", "editors", "distributors"];

export const referenceTitles: Record<ReferenceKey, string> = {
  authors: "Auteurs",
  artists: "Artistes",
  editors: "Editeurs",
  distributors: "Distributeurs",
};

export const referenceEndpoints: Record<ReferenceKey, string> = {
  authors: "authors",
  artists: "artists",
  editors: "editors",
  distributors: "distributors",
};

export const defaultGameForm: GameFormState = {
  name: "",
  type: "Jeu de base",
  extension_of_id: "",
  creation_year: "",
  min_players: "",
  max_players: "",
  min_age: "",
  duration_minutes: "",
  url: "",
  image_url: "",
  authors: "",
  artists: "",
  editors: "",
  distributors: "",
};
