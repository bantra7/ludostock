import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, parse_qs, unquote

BROKEN_URLS = []


def scrape_urls_en_parallele(urls, max_workers=10):
    global BROKEN_URLS
    jeux = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        try:
            for result in executor.map(extraire_infos_trictrac, urls):
                jeux.append(result)
        except:
            print(f"Erreur dans les urls suivantes : {urls}")
            BROKEN_URLS += urls

    return jeux


def charger_tous_les_jeux(i: int):
    print(f"📦 Chargement de la page {i}...")
    url = f"https://trictrac.net/jeux/{i}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Erreur de chargement : {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cartes = soup.select(".style_compactCard__SrGIj")

    urls = []
    for carte in cartes:
        urls.append(carte['href'])

    print(f"🔎 {len(urls)} jeux trouvés sur la page {i}.")
    return urls


def extraire_infos_trictrac(url):
    reponse = requests.get(url)
    soup = BeautifulSoup(reponse.text, "html.parser")
    # Nom / Url
    infos = {
        'Url': url,
        'Nom': soup.select_one("h1.style_specsTitle__NMRfc").text
    }

    # Jeu ou Extension et Année
    bloc = soup.select_one("h4.style_specsSubTitle__rfo9t")
    if bloc:
        ps = bloc.find_all("p")
        if len(ps) >= 1:
            infos["Type"] = ps[0].text.strip()
        if len(ps) >= 2 and ps[1].get("title") == "Année de sortie":
            infos["Année de sortie"] = ps[1].text.strip()
    # Infos techniques (table)
    table = soup.select_one("table.style_specsItems__HUu7f")
    for row in table.select("tr"):
        try:
            label = row.select_one("th").text.strip().replace(" :", "")
            value = row.select_one("td").text.strip()
            infos[label] = value
        except:
            pass

    # Contributeurs : auteurs, artistes, éditeurs, distributeurs
    try:
        contributeurs = soup.select("div.style_conceptorsSpecs___QBek[title]")
        for bloc in contributeurs:
            titre = bloc.get("title").strip()
            noms = [a.text.strip() for a in bloc.select("a")]
            if noms:
                infos[titre] = " / ".join(noms)
    except:
        pass
    # Image
    img = soup.select_one("img[itemprop='image']")
    src = img.get("src") or ""
    parsed_url = urlparse(src)
    params = parse_qs(parsed_url.query)
    img_url = unquote(params.get("url", [""])[0])
    infos['Url Image'] = img_url
    return infos


def scrape_tous_les_jeux(j_start: int):
    start = time.time()
    jeux = []
    try:
        for j in range(j_start, 1061):
            urls = charger_tous_les_jeux(j)

            jeux += [{**d, 'J': j} for d in scrape_urls_en_parallele(urls)]
            elapsed = time.time() - start
            avg_per_iter = elapsed / j
            remaining = avg_per_iter * (1060 - j)
            print(f"🔁 {j}/1060 Already {len(jeux)} games - Temps écoulé : {elapsed:.1f}s - Temps restant estimé : {remaining:.1f}s")
    except Exception as e:
        print(e)
    finally:
        return pd.DataFrame(jeux)


if __name__ == "__main__":
    df = scrape_tous_les_jeux(j_start=1)
    df.to_csv("tous_les_jeux_trictrac.csv", index=False)
    print("✅ Données enregistrées dans 'tous_les_jeux_trictrac.csv'")
    with open("broken_urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(BROKEN_URLS))
    print("✅ Urls cassées enregistrées dans 'broken_urls.txt'")
