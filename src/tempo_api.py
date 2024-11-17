import requests

BASE_URL = "https://www.api-couleur-tempo.fr/api/jourTempo"

# Dictionnaire pour mapper les codes de jour aux couleurs
CODE_TO_COLOR = {
    1: "Bleu",
    2: "Blanc",
    3: "Rouge"
}

def get_tempo_color_today():
    """Récupère la couleur du jour avec des logs pour le débogage."""
    try:
        response = requests.get(f"{BASE_URL}/today")
        print(f"Status Code (Aujourd'hui) : {response.status_code}")
        print(f"Réponse brute (Aujourd'hui) : {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse JSON (Aujourd'hui) : {data}")
            code_jour = data.get("codeJour")
            return CODE_TO_COLOR.get(code_jour, "Inconnu")
        else:
            raise Exception("Erreur lors de la récupération de la couleur du jour.")
    except Exception as e:
        print(f"Erreur lors de la récupération du jour d'aujourd'hui : {e}")
        return None

def get_tempo_color_tomorrow():
    """Récupère la couleur de demain avec des logs pour le débogage."""
    try:
        response = requests.get(f"{BASE_URL}/tomorrow")
        print(f"Status Code (Demain) : {response.status_code}")
        print(f"Réponse brute (Demain) : {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse JSON (Demain) : {data}")
            code_jour = data.get("codeJour")
            return CODE_TO_COLOR.get(code_jour, "Inconnu")
        else:
            raise Exception("Erreur lors de la récupération de la couleur de demain.")
    except Exception as e:
        print(f"Erreur lors de la récupération du jour de demain : {e}")
        return None
