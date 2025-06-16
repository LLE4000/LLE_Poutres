
import streamlit as st
import math
import json
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Calcul armatures – Procédé 30.37", layout="centered")

# --- Coefficients béton Procédé 30.37 ---
beton_coeffs = {
    "C20/25": {"mu": 0.1363, "sigma": 12.96, "fctm": 2.2},
    "C25/30": {"mu": 0.1513, "sigma": 12.96, "fctm": 2.6},
    "C30/37": {"mu": 0.1709, "sigma": 12.96, "fctm": 2.9},
    "C35/45": {"mu": 0.1868, "sigma": 12.96, "fctm": 3.2},
}

acier_fyk = {
    "BE 500": 500,
    "BE 400": 400,
}

def calc_section_barres(n_barres, diam):
    return n_barres * (math.pi * diam**2 / 4)

def generer_pdf(projet, date, beton, acier, b, h, enrobage, d, moments, results, fctm, fyk, Asmin, Asmax, barres_txt, Aschoisi):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Note de calcul – Poutre béton armé ({})".format(projet), ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "Date : {}".format(date), ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Données générales", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "Béton : {} | Acier : {}".format(beton, acier), ln=True)
    pdf.cell(0, 10, "Dimensions : b = {} mm, h = {} mm, enrobage = {} mm".format(b, h, enrobage), ln=True)
    pdf.cell(0, 10, "Hauteur utile calculée : d = {:.1f} mm".format(d), ln=True)
    pdf.ln(5)

    for i, m in enumerate(moments):
        titre = m["nom"]
        M = m["moment"]
        d_res, As = results[i]

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. {}".format(titre), ln=True)
        pdf.set_font("Arial", '', 12)

        pdf.cell(0, 10, "M = {} kNm".format(M), ln=True)
        pdf.cell(0, 10, "Formule : d = sqrt(M * 10^6 / (mu * sigma * b))", ln=True)
        pdf.cell(0, 10, "-> d = {:.1f} mm".format(d_res), ln=True)
        pdf.cell(0, 10, "Formule : As = M * 10^6 / (fyd * 0.9 * d)", ln=True)
        pdf.cell(0, 10, "-> As = {:.1f} mm2".format(As), ln=True)
        pdf.ln(3)

        pdf.cell(0, 10, "As,min = 0.26 * fctm / fyk * b * d = {:.1f} mm2".format(Asmin), ln=True)
        pdf.cell(0, 10, "As,max = 0.04 * b * h = {:.1f} mm2".format(Asmax), ln=True)
        pdf.cell(0, 10, "As choisi = {} -> {:.1f} mm2".format(barres_txt, Aschoisi), ln=True)
        pdf.ln(8)

    return pdf.output(dest='S').encode('latin1')

# --- Interface ---
st.title("Calcul d'armatures – Procédé 30.37")

nom_projet = st.text_input("Nom du projet", "Projet béton armé")
beton = st.selectbox("Classe de béton", list(beton_coeffs.keys()))
acier = st.selectbox("Type d'acier", list(acier_fyk.keys()))

col1, col2, col3 = st.columns(3)
with col1:
    b = st.number_input("Largeur b (mm)", value=300)
with col2:
    h = st.number_input("Hauteur h (mm)", value=500)
with col3:
    enrobage = st.number_input("Enrobage (mm)", value=30)

multi_moment = st.checkbox("Moment supérieur + inférieur")
moments = []
if multi_moment:
    M_sup = st.number_input("Moment supérieur (kNm)", value=90.0)
    M_inf = st.number_input("Moment inférieur (kNm)", value=120.0)
    moments = [
        {"nom": "Moment supérieur", "moment": abs(M_sup)},
        {"nom": "Moment inférieur", "moment": abs(M_inf)},
    ]
else:
    M = st.number_input("Moment fléchissant (kNm)", value=120.0)
    moments = [{"nom": "Moment", "moment": abs(M)}]

# Choix manuel des barres
st.markdown("### Choix des armatures")
colA, colB = st.columns(2)
with colA:
    nb_barres = st.number_input("Nombre de barres", min_value=1, value=5)
with colB:
    diam_barres = st.number_input("Diamètre des barres (mm)", min_value=6, value=8)

As_choisi = calc_section_barres(nb_barres, diam_barres)
barres_txt = "{}Ø{}".format(nb_barres, diam_barres)

# --- Calculs ---
mu = beton_coeffs[beton]["mu"]
sigma = beton_coeffs[beton]["sigma"]
fctm = beton_coeffs[beton]["fctm"]
fyk = acier_fyk[acier]
fyd = fyk / 1.5
d_calc = math.sqrt((moments[0]["moment"] * 1e6) / (mu * sigma * b))
d_max = h - enrobage
d = min(d_calc, d_max)

As_min = 0.26 * fctm / fyk * b * d
As_max = 0.04 * b * h

results = []
for m in moments:
    M = m["moment"]
    d_i = math.sqrt((M * 1e6) / (mu * sigma * b))
    d_i = min(d_i, d_max)
    z = 0.9 * d_i
    As = (M * 1e6) / (fyd * z)
    results.append((d_i, As))

# --- Export PDF ---
pdf_data = generer_pdf(
    nom_projet,
    datetime.today().strftime("%d/%m/%Y"),
    beton, acier,
    b, h, enrobage,
    d, moments,
    results,
    fctm, fyk,
    As_min, As_max,
    barres_txt, As_choisi
)

st.download_button("📄 Télécharger la note de calcul (PDF)", data=pdf_data, file_name="{}.pdf".format(nom_projet))
