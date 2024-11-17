from src.tempo_api import get_tempo_data
from src.smart_life_controller import control_device

def main():
    print("Récupération des données Tempo...")
    tempo_data = get_tempo_data()
    if tempo_data:
        print(f"Données Tempo reçues : {tempo_data}")
        # Exemple de contrôle en fonction des données
        if tempo_data.get("status") == "alerte":
            control_device(action=True)
        else:
            control_device(action=False)

if __name__ == "__main__":
    main()
