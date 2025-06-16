
import streamlit as st
import math
import json
from fpdf import FPDF

# --- Coefficients Procédé 30.37 ---
beton_coeffs = {
    "C20/25": {"mu": 0.1363, "sigma": 12.96},
    "C25/30": {"mu": 0.1513, "sigma": 12.96},
    "C30/37": {"mu": 0.1709, "sigma": 12.96},
    "C35/45": {"mu": 0.1868, "sigma": 12.96},
}

acier_fyk = {
    "BE 500": 500,
    "BE 400": 400,
}

# --- Fonctions de calcul ---
def calculer_armatures(M_kNm, b, beton, acier, h, enrobage):
    mu = beton_coeffs[beton]["mu"]
    sigma = beton_coeffs[beton]["sigma"]
    fyk = acier_fyk[acier]
    gamma_s = 1.5

    d_calc = math.sqrt((M_kNm * 1e6) / (mu * sigma * b))
    d_max = h - enrobage
    d = min(d_calc, d_max)

    fyd = fyk / gamma_s
    z = 0.9 * d
    As = (M_kNm * 1e6) / (fyd * z)

    return d, As

def generer_pdf(projet, moments, geometrie, beton, acier, resultats):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Note de calcul – Projet : {projet}", ln=True)

    pdf.cell(200, 10, txt=f"Béton : {beton}, Acier : {acier}", ln=True)
    pdf.cell(200, 10, txt=f"Dimensions : b = {geometrie['b']} mm, h = {geometrie['h']} mm, enrobage = {geometrie['enrobage']} mm", ln=True)

    for i, m in enumerate(moments):
        d, As = resultats[i]
        titre = m["nom"]
        pdf.cell(200, 10, txt=f"{titre} – M = {m['moment']} kNm → d = {d:.1f} mm, As = {As:.1f} mm²", ln=True)

    return pdf.output(dest='S').encode('latin1')

# --- Interface utilisateur ---
st.title("Calcul d'armatures - Procédé 30.37")

nom_projet = st.text_input("Nom du projet", "Projet sans nom")
beton = st.selectbox("Classe de béton", list(beton_coeffs.keys()))
acier = st.selectbox("Type d'acier", list(acier_fyk.keys()))

col1, col2, col3 = st.columns(3)
with col1:
    b = st.number_input("Largeur b (mm)", value=300)
with col2:
    h = st.number_input("Hauteur h (mm)", value=500)
with col3:
    enrobage = st.number_input("Enrobage (mm)", value=30)

multi_moment = st.checkbox("Ajouter moment supérieur + moment inférieur")
moments = []

if multi_moment:
    M_sup = st.number_input("Moment supérieur M_sup (kNm)", value=90.0)
    M_inf = st.number_input("Moment inférieur M_inf (kNm)", value=120.0)
    moments = [
        {"nom": "Moment supérieur", "moment": abs(M_sup)},
        {"nom": "Moment inférieur", "moment": abs(M_inf)},
    ]
else:
    M = st.number_input("Moment fléchissant M (kNm)", value=120.0)
    moments = [{"nom": "Moment", "moment": abs(M)}]

# --- Calculs ---
resultats = []
for m in moments:
    d, As = calculer_armatures(m["moment"], b, beton, acier, h, enrobage)
    resultats.append((d, As))
    st.markdown(f"### {m['nom']}")
    st.latex(r"d = \sqrt{rac{M \cdot 10^6}{\mu \cdot \sigma \cdot b}}")
    st.write(f"Hauteur utile d = {d:.1f} mm (max = {h - enrobage:.1f} mm)")
    st.latex(r"A_s = rac{M \cdot 10^6}{f_{yd} \cdot 0.9 \cdot d}")
    st.write(f"Section d’armature A_s = {As:.1f} mm²")

# --- Enregistrement du projet ---
if st.button("💾 Enregistrer les données du projet"):
    data = {
        "projet": nom_projet,
        "beton": beton,
        "acier": acier,
        "geometrie": {"b": b, "h": h, "enrobage": enrobage},
        "moments": moments,
    }
    with open(f"{nom_projet}.json", "w") as f:
        json.dump(data, f, indent=4)
    st.success(f"Projet enregistré sous {nom_projet}.json")

# --- Export PDF ---
pdf_data = generer_pdf(nom_projet, moments, {"b": b, "h": h, "enrobage": enrobage}, beton, acier, resultats)
st.download_button("📄 Télécharger la note de calcul (PDF)", data=pdf_data, file_name=f"{nom_projet}.pdf")
