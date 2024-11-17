from src.tempo_api import get_tempo_color_today, get_tempo_color_tomorrow

print("\n=== Test pour aujourd'hui ===")
couleur_aujourdhui = get_tempo_color_today()
if couleur_aujourdhui:
    print(f"Couleur d'aujourd'hui : {couleur_aujourdhui}")
else:
    print("Aucune couleur récupérée pour aujourd'hui.")

print("\n=== Test pour demain ===")
couleur_demain = get_tempo_color_tomorrow()
if couleur_demain:
    print(f"Couleur de demain : {couleur_demain}")
else:
    print("Aucune couleur récupérée pour demain.")
