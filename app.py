import streamlit as st
from src.smart_life_controller import SmartLifeController
from src.tempo_api import get_tempo_color_today, get_tempo_color_tomorrow

# Initialiser le contrôleur Smart Life
controller = SmartLifeController()

st.title("Contrôle de l'appareil Smart Life")

# Section pour le contrôle de l'appareil
st.header("Contrôler l'appareil")
action = st.selectbox("Choisir une action", ["on", "off"])

if st.button("Envoyer la commande"):
    try:
        result = controller.control_device(action)
        st.success(result)
    except Exception as e:
        st.error(f"Erreur lors de la communication avec l'API : {e}")

# Ligne de séparation
st.markdown("---")

# Section pour les informations Tempo
st.header("Informations Tempo")

# Récupérer la couleur du jour
try:
    couleur_aujourdhui = get_tempo_color_today()
    if couleur_aujourdhui:
        st.subheader("Couleur du jour :")
        st.success(f"Aujourd'hui : {couleur_aujourdhui}")
    else:
        st.error("Impossible de récupérer la couleur du jour.")
except Exception as e:
    st.error(f"Erreur lors de la récupération des informations Tempo pour aujourd'hui : {e}")

# Récupérer la couleur de demain
try:
    couleur_demain = get_tempo_color_tomorrow()
    if couleur_demain:
        st.subheader("Couleur de demain :")
        st.success(f"Demain : {couleur_demain}")
    else:
        st.error("Impossible de récupérer la couleur de demain.")
except Exception as e:
    st.error(f"Erreur lors de la récupération des informations Tempo pour demain : {e}")
