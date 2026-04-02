export type NavKey = "overview" | "games" | "authors" | "artists" | "editors" | "distributors";
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
  { key: "overview", label: "Vue d'ensemble" },
  { key: "games", label: "Jeux" },
  { key: "authors", label: "Auteurs" },
  { key: "artists", label: "Artistes" },
  { key: "editors", label: "Editeurs" },
  { key: "distributors", label: "Distributeurs" },
];

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
