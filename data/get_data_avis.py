import time
import sys
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import pandas as pd
from bs4 import BeautifulSoup
import requests

NB_PAGES = 5778
TRICTRAC_URL = "https://trictrac.net/avis/"
BROKEN_URLS = []
BROKEN_URLS_FILE = "broken_urls.txt"
FILENAME = "trictac_data_avis.csv"
MAX_WORKERS = 20

LOGER_LEVEL = "DEBUG"
logger.remove()
logger.add(sys.stdout, level=LOGER_LEVEL)

def get_avatar_name(li):
    """Extract avatar name from img or button."""
    img = li.select_one("img._image_sgf14_42")
    if img and img.has_attr("alt"):
        return img["alt"].replace("avatar de :", "").strip()
    
    btn = li.select_one("button._avatarContainer_sgf14_2")
    if btn and btn.has_attr("data-nickname"):
        return btn["data-nickname"]
    
    return None

def charger_tous_les_avis(i: int) -> List[dict]:
    try:
        logger.debug(f"📦 Page {i} en cours...")
        url = f"{TRICTRAC_URL}/{i}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            BROKEN_URLS.append(url)
            logger.error(f"❌ Erreur ({response.status_code}) : {url}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("li._rads_wdmzw_9")
        avis = []

        for li in items:
            game = li.select_one(".style_gameTitle__RFwyp")
            game_link = li.select_one(".style_gameTitle__RFwyp a")
            date = li.select_one(".style_dateBox__cDUMX")
            score = li.select_one(".style_mark__k9tcv")
            avatar_name = get_avatar_name(li)

            avis.append({
                "Game": game.get_text(strip=True).replace("open_in_new", "") if game else None,
                "Game_Url": game_link["href"] if game_link and game_link.has_attr("href") else None,
                "Date": date.get_text(strip=True).replace("update", "") if date else None,
                "Avatar_Name": avatar_name,
                "Score": score.get_text(strip=True) if score else None
            })

        logger.debug(f"✅ Page {i} → {len(avis)} avis")
        return avis

    except Exception as e:
        BROKEN_URLS.append(f"{TRICTRAC_URL}/{i}")
        logger.error(f"⚠️ Erreur page {i}: {e}")
        return []

def save_results(all_avis):
    """Sauvegarde les résultats (CSV et URLs cassées)."""
    df = pd.DataFrame(all_avis)
    df.to_csv(FILENAME, index=False)
    logger.info(f"✅ {len(df)} avis enregistrés dans {FILENAME}")

    if BROKEN_URLS:
        with open(BROKEN_URLS_FILE, "w") as f:
            f.write("\n".join(BROKEN_URLS))
        logger.warning(f"⚠️ {len(BROKEN_URLS)} URLs cassées enregistrées dans {BROKEN_URLS_FILE}")

if __name__ == "__main__":
    start_time = time.time()
    all_avis = []

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(charger_tous_les_avis, i): i for i in range(1, NB_PAGES + 1)}

            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    all_avis.extend(future.result())
                except Exception as e:
                    logger.error(f"Erreur future pour la page {page_num}: {e}")

    except KeyboardInterrupt:
        logger.warning("🛑 Interruption manuelle détectée !")
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
    finally:
        save_results(all_avis)
        logger.info(f"⏱️ Temps total: {time.time() - start_time:.2f} sec")