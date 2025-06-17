
import streamlit as st
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="Dimensionnement Poutre BA", layout="centered")
st.title("Poutre en béton armé")

# --- RÉINITIALISATION ---
if st.button("🔄 Réinitialiser"):
    st.rerun()

# --- 1. INFOS PROJET ---
with st.container():
    st.markdown("### Informations sur le projet")
    nom = st.text_input("", placeholder="Nom du projet", key="nom_projet")
    partie = st.text_input("", placeholder="Partie", key="partie")
    col1, col2 = st.columns(2)
    with col1:
        date = st.text_input("", placeholder="Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"), key="date")
    with col2:
        indice = st.text_input("", placeholder="Indice", value="0", key="indice")

# --- 2. CARACTÉRISTIQUES DE LA POUTRE ---
with st.container():
    st.markdown("### Caractéristiques de la poutre")
    col1, col2, col3 = st.columns(3)
    with col1:
        b = st.number_input("Largeur (cm)", 10, 120, 40, key="b")
    with col2:
        h = st.number_input("Hauteur (cm)", 10, 150, 60, key="h")
    with col3:
        enrobage = st.number_input("Enrobage (cm)", 2, 10, 3, key="enrobage")

    col4, col5 = st.columns(2)
    with col4:
        beton = st.selectbox("Classe de béton", ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50"], index=2)
    with col5:
        fyk = st.selectbox("Qualité d'acier (fyk)", ["400", "500", "600"], index=1)

# --- BASE DE DONNÉES MATÉRIAUX ---
fck_dict = {"C20/25": 20, "C25/30": 25, "C30/37": 30, "C35/45": 35, "C40/50": 40}
tau_lim_dict = {"C20/25": 0.50, "C25/30": 0.60, "C30/37": 0.70, "C35/45": 0.80, "C40/50": 0.85}
fcd = fck_dict[beton] / 1.5
fyd = int(fyk) / 1.15
tau_lim = tau_lim_dict[beton]

# --- 3. SOLLICITATIONS ---
with st.container():
    st.markdown("### Sollicitations")
    col1, col2 = st.columns(2)
    with col1:
        M = st.number_input("Moment inférieur M (kNm)", 0.0, step=10.0)
    with col2:
        V = st.number_input("Effort tranchant V (kN)", 0.0, step=10.0)

    m_sup = st.checkbox("Ajouter un moment supérieur")
    v_sup = st.checkbox("Ajouter un effort tranchant réduit")
    if m_sup:
        M_sup = st.number_input("Moment supérieur M_sup (kNm)", 0.0, step=10.0)
    if v_sup:
        V_lim = st.number_input("Effort tranchant réduit V_limite (kN)", 0.0, step=10.0)

# --- 4. DIMENSIONNEMENT ---
with st.container():
    st.markdown("### Dimensionnement")

    d = h - enrobage
    st.markdown(f"**Hauteur utile d = h - enrobage = {h} - {enrobage} = {d:.1f} cm**")

    d_valide = d <= 0.9 * h
    col1, col2 = st.columns([10, 1])
    with col1:
        st.write("Vérification de la hauteur utile (d ≤ 0.9·h)")
    with col2:
        st.markdown("✅" if d_valide else "❌")

    if M > 0:
        Mu = M * 1e6
        As_req = Mu / (fyd * 10 * 0.9 * d)
        As_min = 0.0013 * b * h
        As_max = 0.04 * b * h

        st.markdown(f"**Section requise Aₛ = {As_req:.1f} mm²**")

        col1, col2, col3 = st.columns([3, 3, 4])
        with col1:
            n_barres = st.selectbox("Nb barres", list(range(1, 8)), key="n_as")
        with col2:
            diam_barres = st.selectbox("Ø (mm)", [8, 10, 12, 14, 16, 20], key="ø_as")
        with col3:
            As_choisi = 3.14 * (diam_barres / 2) ** 2 * n_barres
            st.markdown(f"Section = **{As_choisi:.0f} mm²**")

        ok_As = As_min <= As_choisi <= As_max and As_choisi >= As_req
        col1, col2 = st.columns([10, 1])
        with col1:
            st.write("Vérification As entre As_min et As_max et ≥ As_req")
        with col2:
            st.markdown("✅" if ok_As else "❌")

    if m_sup and M_sup > 0:
        Mu_sup = M_sup * 1e6
        As_sup = Mu_sup / (fyd * 10 * 0.9 * d)
        st.markdown(f"**Section Aₛ_sup = {As_sup:.1f} mm²**")
        col1, col2, col3 = st.columns([3, 3, 4])
        with col1:
            n_sup = st.selectbox("Nb barres sup", list(range(1, 8)), key="n_sup")
        with col2:
            diam_sup = st.selectbox("Ø sup (mm)", [8, 10, 12, 14, 16], key="ø_sup")
        with col3:
            As_sup_choisi = 3.14 * (diam_sup / 2) ** 2 * n_sup
            st.markdown(f"Section = **{As_sup_choisi:.0f} mm²**")

        ok_As_sup = As_min <= As_sup_choisi <= As_max and As_sup_choisi >= As_sup
        col1, col2 = st.columns([10, 1])
        with col1:
            st.write("Vérification As_sup entre As_min et As_max et ≥ As_sup")
        with col2:
            st.markdown("✅" if ok_As_sup else "❌")

    if V > 0:
        tau = V / (0.75 * b * h)
        st.markdown(f"**τ = {tau:.2f} MPa / τ_lim = {tau_lim:.2f} MPa**")

        col1, col2 = st.columns([10, 1])
        with col1:
            st.write("Vérification τ ≤ τ_lim")
        with col2:
            st.markdown("✅" if tau <= tau_lim else "❌")

        col1, col2 = st.columns(2)
        with col1:
            n_etriers = st.selectbox("Nb brins", [2, 3, 4], key="n_etriers")
        with col2:
            diam_etriers = st.selectbox("Ø étrier (mm)", [6, 8, 10], key="ø_etrier")

        area_etrier = n_etriers * 3.14 * (diam_etriers / 2) ** 2

        if V > 0:
            pas_theorique = (area_etrier * fyd * d * 10) / (V * 1000)
            pas_arrondi = int((pas_theorique + 4.9) // 5) * 5
            pas_choisi = st.number_input("Pas choisi (mm)", min_value=5, value=pas_arrondi, step=5)

            ok_pas = pas_choisi <= pas_theorique
            col1, col2 = st.columns([10, 1])
            with col1:
                st.write(f"Pas théorique : {pas_theorique:.0f} mm")
            with col2:
                st.markdown("✅" if ok_pas else "❌")

    if v_sup and V > 0 and 'V_lim' in locals() and V_lim > 0:
        tau2 = V_lim / (0.75 * b * h)
        st.markdown(f"**Avec effort réduit : τ = {tau2:.2f} MPa**")

        col1, col2 = st.columns([10, 1])
        with col1:
            st.write("Vérification τ réduit ≤ τ_lim")
        with col2:
            st.markdown("✅" if tau2 <= tau_lim else "❌")
