
import streamlit as st
import math
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io

st.set_page_config("Dimensionnement Poutre BA", layout="centered")

# --- Base de données béton et acier
beton_dict = {
    "C20/25": {"mu": 0.1363, "sigma": 12.96, "tau_adm": 0.75},
    "C25/30": {"mu": 0.1513, "sigma": 12.96, "tau_adm": 0.95},
    "C30/37": {"mu": 0.1708, "sigma": 12.96, "tau_adm": 1.13},
    "C35/45": {"mu": 0.1904, "sigma": 12.96, "tau_adm": 1.30},
    "C40/50": {"mu": 0.2060, "sigma": 12.96, "tau_adm": 1.50},
}
acier_list = ["500", "400"]

# --- Fonctions de calcul
def calc_d(M, mu, sigma, b): return math.sqrt((M * 1e6) / (mu * sigma * b))
def calc_As(M, fyd, d): return (M * 1e6) / (fyd * 0.9 * d)
def section_armature(n, dia): return n * (math.pi * dia**2 / 4)
def calc_tau(V, b, h): return (V * 1e3) / (0.75 * b * h)
def calc_pas(V, n_etriers, dia, fyd): return ((4 * n_etriers * math.pi * dia**2 / 4) * fyd * 1e6 * 0.9) / (V * 1e3)

# --- UI
st.title("🧱 Dimensionnement d'une poutre en béton armé")
st.markdown("---")

# Section 1 : Info projet
st.subheader("1. Informations sur le projet")
col1, col2 = st.columns([3, 1])
projet = col1.text_input("Nom du projet", placeholder="ex: Bâtiment RTDF")
partie = col1.text_input("Partie", placeholder="ex: Poutres RDC")
date_str = col1.text_input("Date (jj/mm/aaaa)", value=datetime.today().strftime("%d/%m/%Y"))
indice = col2.number_input("Indice", value=0)

# Section 2 : Caractéristiques poutre
st.subheader("2. Caractéristiques de la poutre")
col1, col2 = st.columns(2)
b_cm = col1.number_input("Largeur (cm)", value=60)
h_cm = col1.number_input("Hauteur (cm)", value=70)
enrobage = col1.number_input("Enrobage (cm)", value=3)

beton = col2.selectbox("Qualité béton", list(beton_dict.keys()), index=2)
acier = col2.selectbox("Qualité acier", acier_list, index=0)

mu = beton_dict[beton]["mu"]
sigma = beton_dict[beton]["sigma"]
tau_adm = beton_dict[beton]["tau_adm"]
fyk = int(acier)
fyd = fyk / 1.5

# Section 3 : Sollicitations
st.subheader("3. Sollicitations")
M = st.number_input("Moment inférieur M (kNm)", value=0.0)
V = st.number_input("Effort tranchant V (kN)", value=0.0)

colM, colV = st.columns(2)
M_sup_active = colM.checkbox("Ajouter un moment supérieur ?")
M_sup = colM.number_input("Moment supérieur M_sup (kNm)", value=0.0) if M_sup_active else None
V_red_active = colV.checkbox("Ajouter un effort tranchant réduit ?")
V_limite = colV.number_input("Effort tranchant limité V_red (kN)", value=0.0) if V_red_active else None

# Calculs automatiques
b = b_cm * 10
h = h_cm * 10
d_calc = calc_d(max(abs(M), abs(M_sup or 0)), mu, sigma, b)
d_max = h - enrobage * 10
check_d = d_calc <= d_max

if M == 0 or fyd == 0 or d_calc == 0:
    As_req = 0
    verif_As = False
else:
    As_req = calc_As(M, fyd, d_calc)
    verif_As = As_min <= As_choisi <= As_max and As_choisi >= As_req
As_min = 633
As_max = 16800

# Choix armatures commerciales
if M > 0:
    As_min = 633
    As_max = 16800
    st.subheader("4. Dimensionnement")
    st.markdown("#### 4.1 Hauteur utile")
    st.write(f"Hauteur utile d = {d_calc:.1f} mm")
    st.write(f"Hauteur max admissible = {d_max} mm {'✅' if check_d else '❌'}")

    st.markdown("#### 4.2 Vérification des armatures principales")
    n_barres = st.selectbox("Nombre de barres", [2, 3, 4, 5, 6, 7, 8])
    diametre = st.selectbox("Diamètre (mm)", [8, 10, 12, 14, 16, 20, 25, 32])
    As_choisi = section_armature(n_barres, diametre)

    verif_As = As_min <= As_choisi <= As_max and As_choisi >= As_req

    st.write(f"Aₛ requis : {As_req:.1f} mm²")
    st.write(f"Aₛ choisi : {n_barres}Ø{diametre} = {As_choisi:.1f} mm² {'✅' if verif_As else '❌'}")
    st.write(f"Aₛ min = {As_min} mm²  / Aₛ max = {As_max} mm²")

    if M_sup_active:
        As_sup = calc_As(M_sup, fyd, d_calc)
        st.write(f"Armature supérieure : Aₛ_sup = {As_sup:.1f} mm²")

    st.markdown("#### 4.3 Vérification des efforts tranchants")
    tau = calc_tau(V, b, h)
    verif_tau = tau <= tau_adm
    st.write(f"τ = {tau:.2f} N/mm²  (τ_adm = {tau_adm} N/mm²) → {'✅' if verif_tau else '❌'}")

    # Vérification des étriers
    st.markdown("##### Étriers")
    n_etriers = st.selectbox("Nombre de brins d’étrier", [1, 2])
    dia_etrier = st.selectbox("Diamètre étrier (mm)", [6, 8, 10])
    pas_th = calc_pas(V, n_etriers, dia_etrier, fyd)
    pas_sugg = int((pas_th // 50 + 1) * 50)
    pas_choisi = st.number_input("Pas choisi (mm)", value=pas_sugg)

    verif_pas = pas_choisi <= pas_th
    st.write(f"Pas théorique = {pas_th:.0f} mm → Suggestion : {pas_sugg} mm")
    st.write(f"Pas choisi : {pas_choisi} mm → {'✅' if verif_pas else '❌'}")

    if V_red_active:
        tau_r = calc_tau(V_limite, b, h)
        st.write(f"τ (réduit) = {tau_r:.2f} N/mm²")

    # PDF Button
else:
    st.info("💡 Entrez un moment pour lancer le dimensionnement automatique.")
if st.button("📄 Générer la note de calcul PDF"):
    st.warning("📄 La version PDF sera ajoutée dans la prochaine étape.")
