
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Dimensionnement Poutre BA", layout="centered")

st.title("Dimensionnement d'une poutre en béton armé")

if st.button("🔄 Réinitialiser les données"):
    st.experimental_rerun()

# 1. Informations sur le projet
with st.container():
    st.markdown("#### Informations sur le projet")
    nom_projet = st.text_input(label="", placeholder="Nom du projet", key="nom_projet")
    partie = st.text_input(label="", placeholder="Partie", key="partie")
    col1, col2 = st.columns(2)
    with col1:
        date_str = st.text_input(label="", placeholder="Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"), key="date")
    with col2:
        indice = st.text_input(label="", placeholder="Indice", value="0", key="indice")

# 2. Caractéristiques de la poutre
with st.container():
    st.markdown("#### Caractéristiques de la poutre")
    col1, col2, col3 = st.columns(3)
    with col1:
        b = st.number_input("Largeur (cm)", value=40)
    with col2:
        h = st.number_input("Hauteur (cm)", value=70)
    with col3:
        enrobage = st.number_input("Enrobage (cm)", value=3)

    col4, col5 = st.columns(2)
    with col4:
        beton = st.selectbox("Qualité béton", ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50"], index=2)
    with col5:
        fyk = st.selectbox("Qualité acier (fyk)", ["400", "500", "600"], index=1)
fcd_dict = {"C20/25": 8.3, "C25/30": 10.8, "C30/37": 12.96, "C35/45": 15.2, "C40/50": 17.6}
tau_lim_dict = {"C20/25": 0.3, "C25/30": 0.35, "C30/37": 0.4, "C35/45": 0.45, "C40/50": 0.5}

fyd = int(fyk) / 1.15
fcd = fcd_dict[beton]
tau_lim = tau_lim_dict[beton]

# 3. Sollicitations
with st.container():
    st.markdown("#### Sollicitations")
    col1, col2 = st.columns(2)
    with col1:
        M = st.number_input("Moment inférieur M (kNm)", value=0.0)
    with col2:
        V = st.number_input("Effort tranchant V (kN)", value=0.0)
    M_sup_check = st.checkbox("Ajouter un moment supplémentaire")
    V_lim_check = st.checkbox("Ajouter un effort tranchant réduit")

# 4. Dimensionnement
with st.container():
    st.markdown("#### Dimensionnement")
    d = h - enrobage
    st.markdown(f"**Hauteur utile :** d = {d:.1f} cm")
    h_min = ((M * 1e6) / (0.1709 * fcd * b)) ** 0.5 / 10 if M > 0 else 0

    if h >= h_min:
        st.success("✅ Hauteur suffisante")
    else:
        st.error("❌ Hauteur insuffisante")

    # Calcul armatures inférieures
    As_req = (M * 1e6) / (fyd * 0.9 * d) if M > 0 else 0
    As_min = 0.0013 * b * h
    As_max = 0.04 * b * h
    st.markdown(f"**Armature requise :** Aₛ = {As_req:.1f} mm² (min: {As_min:.0f}, max: {As_max:.0f})")

    options_As = {"2Ø12": 226, "2Ø14": 308, "2Ø16": 402, "2Ø20": 628, "3Ø12": 339, "3Ø16": 603, "4Ø16": 804}
    choix = st.selectbox("Choisir armatures inférieures", list(options_As.keys()))
    As_choisi = options_As[choix]

    if As_min <= As_choisi <= As_max and As_choisi >= As_req:
        st.success("✅ Section d'armatures correcte")
    else:
        st.error("❌ Section d'armatures incorrecte")

    if M_sup_check:
        M_sup = st.number_input("Moment supérieur M_sup (kNm)", value=0.0)
        As_sup = (M_sup * 1e6) / (fyd * 0.9 * d)
        st.markdown(f"Aₛ_sup = {As_sup:.1f} mm²")
        choix_sup = st.selectbox("Choisir armatures supérieures", list(options_As.keys()), key="choix_sup")
        As_choisi_sup = options_As[choix_sup]
        if As_min <= As_choisi_sup <= As_max and As_choisi_sup >= As_sup:
            st.success("✅ Section supérieure correcte")
        else:
            st.error("❌ Section supérieure incorrecte")

    # Vérification effort tranchant
    tau = V * 1000 / (0.75 * b * h)
    st.markdown(f"τ = {tau:.2f} N/mm²")
    if tau <= tau_lim:
        st.success("✅ Effort tranchant admissible")
    else:
        st.error("❌ Effort tranchant trop élevé")

    # Calcul des étriers
    diam_etrier = st.selectbox("Diamètre d'étrier (mm)", [6, 8, 10], index=1)
    nb_brins = st.selectbox("Nombre de brins", [2, 3, 4], index=0)
    fyk_etrier = 500
    area_etrier = nb_brins * 3.14 * (diam_etrier / 2) ** 2
    s_theorique = (area_etrier * fyk_etrier * d * 10) / (V * 1000)
    pas_arrondi = int((s_theorique + 5) / 5) * 5
    st.markdown(f"**Pas théorique :** {s_theorique:.1f} mm ➝ suggestion : {pas_arrondi} mm")
    pas_choisi = st.number_input("Pas choisi (mm)", value=pas_arrondi)

    if pas_choisi <= s_theorique:
        st.success("✅ Pas correct")
    else:
        st.error("❌ Pas trop grand")

    if V_lim_check:
        V_lim = st.number_input("Effort tranchant réduit (kN)", value=0.0)
        tau_limite = V_lim * 1000 / (0.75 * b * h)
        s_theo_lim = (area_etrier * fyk_etrier * d * 10) / (V_lim * 1000)
        st.markdown(f"**τ réduit :** {tau_limite:.2f} N/mm²")
        st.markdown(f"**Pas réduit :** {s_theo_lim:.1f} mm")

        if tau_limite <= tau_lim:
            st.success("✅ τ réduit admissible")
        else:
            st.error("❌ τ réduit non admissible")
