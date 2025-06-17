
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Dimensionnement Poutre BA", layout="centered")

st.title("🧱 Dimensionnement d'une poutre en béton armé")

# Réinitialisation
if st.button("🔄 Réinitialiser les données"):
    st.experimental_rerun()

# Informations sur le projet
with st.container():
    st.markdown("### Informations sur le projet")
    nom_projet = st.text_input(label="", placeholder="Nom du projet", key="nom_projet")
    partie = st.text_input(label="", placeholder="Partie", key="partie")
    col1, col2 = st.columns(2)
    with col1:
        date_str = st.text_input(label="", placeholder="Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"), key="date")
    with col2:
        indice = st.text_input(label="", placeholder="Indice", value="0", key="indice")

# Caractéristiques de la poutre
with st.container():
    st.markdown("### Caractéristiques de la poutre")
    col1, col2, col3 = st.columns(3)
    with col1:
        b_cm = st.number_input("Largeur (cm)", min_value=10, max_value=120, value=40, key="b_cm")
    with col2:
        h_cm = st.number_input("Hauteur (cm)", min_value=10, max_value=150, value=70, key="h_cm")
    with col3:
        enrobage_cm = st.number_input("Enrobage (cm)", min_value=2, max_value=10, value=3, key="enrobage")

    col4, col5 = st.columns(2)
    with col4:
        qualite_beton = st.selectbox("Qualité béton", ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50"], index=2, key="beton")
    with col5:
        qualite_acier = st.selectbox("Qualité acier (fyk)", ["400", "500", "600"], index=1, key="acier")

# Sollicitations
with st.container():
    st.markdown("### Sollicitations")
    col1, col2 = st.columns(2)
    with col1:
        M = st.number_input("Moment inférieur M (kNm)", min_value=0.0, step=10.0, value=0.0, key="moment")
    with col2:
        V = st.number_input("Effort tranchant V (kN)", min_value=0.0, step=10.0, value=0.0, key="tranchant")

    st.checkbox("Ajouter un moment supplémentaire", key="moment_sup")
    st.checkbox("Ajouter un effort tranchant réduit", key="tranchant_sup")

# Dimensionnement (bref affichage à titre d’exemple)
with st.container():
    st.markdown("### Dimensionnement")
    st.markdown("- Hauteur utile `d = h - enrobage`")
    if M > 0 and V > 0:
        st.success("🧮 Données prêtes pour le calcul.")
    else:
        st.warning("Veuillez remplir les sollicitations pour lancer le dimensionnement.")
