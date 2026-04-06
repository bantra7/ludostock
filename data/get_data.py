import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import Any, Dict, List, Optional
import unicodedata
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

NB_PAGES = 1060
TRICTRAC_URL = "https://trictrac.net/jeux"
BROKEN_URLS: List[str] = []
BROKEN_URLS_FILE = "data/raw/broken_urls.txt"
FILENAME = "data/raw/trictac_data_games.csv"
REQUEST_TIMEOUT = 15
DEFAULT_MAX_WORKERS = 10
CONTRIBUTOR_LABELS = {
    "auteur": "Auteurs",
    "auteurs": "Auteurs",
    "auteurs_autrices": "Auteurs",
    "artiste": "Artistes",
    "artistes": "Artistes",
    "illustrateur": "Artistes",
    "illustrateurs": "Artistes",
    "editeur": "Editeurs",
    "editeurs": "Editeurs",
    "distributeur": "Distributeurs",
    "distributeurs": "Distributeurs",
}

# Configuration du logger
LOGGER_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
logger.remove()
logger.add(sys.stdout, level=LOGGER_LEVEL)


def fetch_page(url: str) -> Optional[requests.Response]:
    """Execute une requete HTTP et loggue proprement les erreurs."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        logger.error(f"Erreur HTTP pour {url}: {exc}")
        return None


def scrape_urls_en_parallele(
    urls: List[str], max_workers: int = DEFAULT_MAX_WORKERS
) -> List[Dict[str, Any]]:
    """
    Recupere les informations des jeux en parallele a partir d'une liste d'URLs.

    Args:
        urls: Liste des URLs a scraper.
        max_workers: Nombre maximum de threads.

    Returns:
        La liste des dictionnaires contenant les infos des jeux.
    """
    jeux: List[Dict[str, Any]] = []
    if not urls:
        return jeux

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extraire_infos_trictrac, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                logger.error(f"Erreur inattendue pendant le scraping de {url}: {exc}")
                BROKEN_URLS.append(url)
                continue

            if result is None:
                BROKEN_URLS.append(url)
                continue

            jeux.append(result)

    return jeux


def charger_tous_les_jeux(page_number: int) -> List[str]:
    """
    Charge toutes les URLs de jeux sur une page donnee.

    Args:
        page_number: Numero de la page a charger.

    Returns:
        Liste des URLs des jeux trouves sur la page.
    """
    logger.info(f"Chargement de la page {page_number}...")
    url = f"{TRICTRAC_URL}/{page_number}"
    response = fetch_page(url)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cartes = soup.select('[class*="compactCard"]')

    urls: List[str] = []
    for carte in cartes:
        href = carte.get("href")
        if href:
            urls.append(urljoin(TRICTRAC_URL, href))

    logger.info(f"{len(urls)} jeux trouves sur la page {page_number}.")
    return urls


def extraire_texte(element: Optional[BeautifulSoup]) -> Optional[str]:
    """Retourne le texte nettoye d'un element HTML, ou None."""
    if element is None:
        return None
    texte = element.get_text(strip=True)
    return texte or None


def normaliser_libelle(label: str) -> str:
    """Normalise un libelle HTML pour le convertir en cle CSV stable."""
    sans_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", label)
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "_", sans_accents.lower()).strip("_")


def extraire_infos_trictrac(url: str) -> Optional[Dict[str, Any]]:
    """
    Extrait les informations d'un jeu a partir de son URL TricTrac.

    Args:
        url: URL du jeu a scraper.

    Returns:
        Dictionnaire contenant les informations du jeu, ou None si la page est inutilisable.
    """
    response = fetch_page(url)
    if response is None:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    nom = extraire_texte(soup.select_one("h1.style_specsTitle__NMRfc"))
    if not nom:
        logger.error(f"Titre introuvable pour {url}")
        return None

    infos: Dict[str, Any] = {
        "Url": url,
        "Nom": nom,
        "Auteurs": "",
        "Artistes": "",
        "Editeurs": "",
        "Distributeurs": "",
    }

    bloc = soup.select_one("h4.style_specsSubTitle__rfo9t")
    if bloc:
        ps = bloc.find_all("p")
        if len(ps) >= 1:
            type_jeu = extraire_texte(ps[0])
            if type_jeu:
                infos["Type"] = type_jeu
        if len(ps) >= 2 and ps[1].get("title") == "Annee de sortie":
            annee = extraire_texte(ps[1])
            if annee:
                infos["Annee de sortie"] = annee

    table = soup.select_one("table.style_specsItems__HUu7f")
    if table:
        for row in table.select("tr"):
            label = extraire_texte(row.select_one("th"))
            value = extraire_texte(row.select_one("td"))
            if not label or not value:
                continue

            clean_label = label.replace(" :", "")
            logger.debug(f"{clean_label}: {value}")
            infos[clean_label] = value
    else:
        logger.warning(f"Table des caracteristiques introuvable pour {url}")

    contributeurs = soup.select("span.style_conceptorsSpecs___QBek[title]")
    logger.debug(f"Contributeurs trouves : {len(contributeurs)}")
    for bloc_contributeur in contributeurs:
        titre = bloc_contributeur.get("title", "").strip()
        noms = [a.get_text(strip=True) for a in bloc_contributeur.select("a") if a.get_text(strip=True)]
        if titre and noms:
            infos[CONTRIBUTOR_LABELS.get(normaliser_libelle(titre), titre)] = " / ".join(noms)

    img = soup.select_one("img[itemprop='image']")
    src = img.get("src", "") if img else ""
    parsed_url = urlparse(src)
    params = parse_qs(parsed_url.query)
    img_url = unquote(params.get("url", [""])[0]) or src
    infos["Url Image"] = img_url

    return infos


def scrape_tous_les_jeux(j_start: int) -> pd.DataFrame:
    """
    Scrape tous les jeux a partir d'une page de depart jusqu'a la derniere page.

    Args:
        j_start: Numero de la page de depart.

    Returns:
        DataFrame contenant toutes les informations des jeux.
    """
    start = time.time()
    jeux: List[Dict[str, Any]] = []

    for iteration_index, page_number in enumerate(range(j_start, NB_PAGES + 1), start=1):
        urls = charger_tous_les_jeux(page_number)
        jeux.extend({**jeu, "J": page_number} for jeu in scrape_urls_en_parallele(urls))

        elapsed = time.time() - start
        avg_per_iter = elapsed / iteration_index
        remaining = avg_per_iter * (NB_PAGES - page_number)
        logger.info(
            f"{page_number}/{NB_PAGES} - {len(jeux)} jeux recuperes - "
            f"temps ecoule : {elapsed:.1f}s - temps restant estime : {remaining:.1f}s"
        )

    return pd.DataFrame(jeux)


if __name__ == "__main__":
    """
    Point d'entree principal du script.
    Scrape tous les jeux et sauvegarde les resultats dans un fichier CSV.
    Sauvegarde egalement les URLs cassees dans un fichier texte.
    """
    df = scrape_tous_les_jeux(j_start=1)
    df.to_csv(FILENAME, index=False)
    logger.info(f"Donnees enregistrees dans {FILENAME}")

    with open(BROKEN_URLS_FILE, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(BROKEN_URLS))

    logger.info(f"URLs cassees enregistrees dans {BROKEN_URLS_FILE}")
