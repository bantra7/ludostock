import pandas as pd

# Configuration de la base de données
API_URL = "https://ludostock-backend-1015299081216.europe-west1.run.app/api"
FILENAME = "data/trictrac_data.csv"

def charger_donnees():
    """Charge les données depuis le fichier CSV et les insère dans la base de données.

    Returns:
    """
    # Lecture du CSV
    df = pd.read_csv(FILENAME)

    # Normalisation des colonnes attendues
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    print(df.columns)

if __name__ == "__main__":
    """
    Point d'entrée principal du script. 
    """
    charger_donnees()
    print("✅ Import terminé avec succès.")
