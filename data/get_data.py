import time
import sys
from loguru import logger
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, parse_qs, unquote

NB_PAGES = 1060
TRICTRAC_URL = "https://trictrac.net/jeux/"
BROKEN_URLS = []
BROKEN_URLS_FILE = "broken_urls.txt"
FILENAME = "trictac_data_games.csv"

# Configuration du logger
LOGER_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
logger.remove()
logger.add(sys.stdout, level=LOGER_LEVEL)


def scrape_urls_en_parallele(urls: List[str], max_workers: int = 10) -> List[Dict[str, Any]]:
    """
    Récupère les informations des jeux en parallèle à partir d'une liste d'URLs.

    Args:
        urls (List[str]): Liste des URLs à scraper.
        max_workers (int, optional): Nombre maximum de threads. Par défaut à 10.

    Returns:
        List[Dict[str, Any]]: Liste des dictionnaires contenant les infos des jeux.
    """
    global BROKEN_URLS
    jeux = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        try:
            for result in executor.map(extraire_infos_trictrac, urls):
                jeux.append(result)
        except Exception:
            logger.error(f"Erreur dans les urls suivantes : {urls}")
            BROKEN_URLS += urls

    return jeux


def charger_tous_les_jeux(i: int) -> List[str]:
    """
    Charge toutes les URLs de jeux sur une page donnée.

    Args:
        i (int): Numéro de la page à charger.

    Returns:
        List[str]: Liste des URLs des jeux trouvés sur la page.
    """
    logger.info(f"📦 Chargement de la page {i}...")
    url = f"{TRICTRAC_URL}/{i}"
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"❌ Erreur de chargement : {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cartes = soup.select(".style_compactCard__SrGIj")

    urls = []
    for carte in cartes:
        urls.append(carte['href'])

    logger.info(f"🔎 {len(urls)} jeux trouvés sur la page {i}.")
    return urls


def extraire_infos_trictrac(url: str) -> Dict[str, Any]:
    """
    Extrait les informations d'un jeu à partir de son URL TricTrac.

    Args:
        url (str): URL du jeu à scraper.

    Returns:
        Dict[str, Any]: Dictionnaire contenant les informations du jeu.
    """
    reponse = requests.get(url)
    soup = BeautifulSoup(reponse.text, "html.parser")
    infos = {
        'Url': url,
        'Nom': soup.select_one("h1.style_specsTitle__NMRfc").text
    }

    bloc = soup.select_one("h4.style_specsSubTitle__rfo9t")
    if bloc:
        ps = bloc.find_all("p")
        if len(ps) >= 1:
            infos["Type"] = ps[0].text.strip()
        if len(ps) >= 2 and ps[1].get("title") == "Année de sortie":
            infos["Année de sortie"] = ps[1].text.strip()
    table = soup.select_one("table.style_specsItems__HUu7f")
    for row in table.select("tr"):
        try:
            label = row.select_one("th").text.strip().replace(" :", "")
            value = row.select_one("td").text.strip()
            logger.debug(f"🔍 {label}: {value}")
            infos[label] = value
        except Exception:
            pass

    try:
        contributeurs = soup.select("span.style_conceptorsSpecs___QBek[title]")
        logger.debug(f"👥 Contributeurs trouvés : {len(contributeurs)}")
        for bloc in contributeurs:
            titre = bloc.get("title").strip()
            noms = [a.text.strip() for a in bloc.select("a")]
            if noms:
                logger.debug(f"👥 {titre}: {', '.join(noms)}")
                infos[titre] = " / ".join(noms)
    except Exception:
        logger.error(f"Erreur lors de l'extraction des contributeurs pour {url}")
        pass
    img = soup.select_one("img[itemprop='image']")
    src = img.get("src") or ""
    parsed_url = urlparse(src)
    params = parse_qs(parsed_url.query)
    img_url = unquote(params.get("url", [""])[0])
    infos['Url Image'] = img_url
    return infos


def scrape_tous_les_jeux(j_start: int) -> pd.DataFrame:
    """
    Scrape tous les jeux à partir d'une page de départ jusqu'à la dernière page.

    Args:
        j_start (int): Numéro de la page de départ.

    Returns:
        pd.DataFrame: DataFrame contenant toutes les informations des jeux.
    """
    start = time.time()
    jeux = []
    try:
        for j in range(j_start, NB_PAGES+1):
            urls = charger_tous_les_jeux(j)

            jeux += [{**d, 'J': j} for d in scrape_urls_en_parallele(urls)]
            elapsed = time.time() - start
            avg_per_iter = elapsed / j
            remaining = avg_per_iter * (1060 - j)
            logger.info(f"🔁 {j}/1060 Already {len(jeux)} games - Temps écoulé : {elapsed:.1f}s - Temps restant estimé : {remaining:.1f}s")
    except Exception as e:
        logger.error(e)
    finally:
        return pd.DataFrame(jeux)


if __name__ == "__main__":
    """
    Point d'entrée principal du script.
    Scrape tous les jeux et sauvegarde les résultats dans un fichier CSV.
    Sauvegarde également les URLs cassées dans un fichier texte.
    """
    df = scrape_tous_les_jeux(j_start=1)
    df.to_csv(FILENAME, index=False)
    logger.info(f"✅ Données enregistrées dans {FILENAME}")
    with open(BROKEN_URLS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(BROKEN_URLS))
    logger.info("✅ Urls cassées enregistrées dans {BROKEN_URLS_FILE}")
