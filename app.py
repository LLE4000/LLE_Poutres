
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
with st.container():
    st.markdown("### Informations sur le projet")
    col1, col2 = st.columns([3, 1])
    projet = st.text_input("", placeholder="Nom du projet", key="projet")
    partie = st.text_input("", placeholder="Partie (ex: Poutres RDC)", key="partie")
    col3, col4 = st.columns([3, 1])
    date_str = col3.text_input("", value=datetime.today().strftime("%d/%m/%Y"), placeholder="jj/mm/aaaa", key="date_str")
    indice = col4.number_input("Indice", value=0, key="indice")
