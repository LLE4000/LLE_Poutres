
import streamlit as st
import math, io, os, tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PIL import Image
import matplotlib.pyplot as plt

# ----------------- Données béton / acier -----------------
beton_coeffs = {
    "C20/25": {"mu": 0.1363, "sigma": 12.96, "fctm": 2.2},
    "C25/30": {"mu": 0.1513, "sigma": 12.96, "fctm": 2.6},
    "C30/37": {"mu": 0.1709, "sigma": 12.96, "fctm": 2.9},
    "C35/45": {"mu": 0.1868, "sigma": 12.96, "fctm": 3.2},
}
acier_fyk = {"BE 500": 500, "BE 400": 400}

# ----------------- Fonctions utilitaires -----------------
def latex_to_png(latex, fontsize=20):
    fig, ax = plt.subplots(figsize=(0.01, 0.01))
    ax.axis("off")
    ax.text(0.5, 0.5, f"${latex}$", fontsize=fontsize, ha="center", va="center")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def calc_section_barres(n, d):
    return n * (math.pi * d ** 2 / 4)

def build_pdf(data):
    tmp = io.BytesIO()
    c = canvas.Canvas(tmp, pagesize=A4)
    y = 285  # mm from bottom
    def title(txt): 
        nonlocal y
        c.setFont("Helvetica-Bold", 14); c.drawString(20*mm, y*mm, txt); y -= 8
    def text(txt, size=11): 
        nonlocal y
        c.setFont("Helvetica", size); c.drawString(25*mm, y*mm, txt); y -= 6

    title(f"Note de calcul – Poutre béton armé ({data['proj']})")
    text(f"Date : {data['date']}")
    y -= 4

    # 1. Données
    title("1. Données générales")
    text(f"Béton : {data['beton']}   |   Acier : {data['acier']}")
    text(f"Dimensions : b = {data['b']} mm   h = {data['h']} mm   enrobage = {data['enrobage']} mm")
    text(f"Hauteur utile limite : d_max = {data['dmax']:.1f} mm")
    y -= 4

    # 2. Moments
    sec_num = 2
    for m, res in zip(data['moments'], data['results']):
        title(f"{sec_num}. {m['nom']}"); sec_num +=1
        text(f"Moment M = {m['moment']} kNm")
        # Formule d
        img_d = latex_to_png(r"d = \sqrt{\dfrac{M\cdot10^{6}}{\mu\,\sigma\,b}}", 18)
        img_As = latex_to_png(r"A_s = \dfrac{M\cdot10^{6}}{f_{yd}\cdot0.9\,d}", 18)

        # place images
        w, h_img = img_d.size
        img_path_d = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
        img_d.save(img_path_d); 
        c.drawImage(img_path_d, 30*mm, (y-20)*mm, width=120*mm, preserveAspectRatio=True, mask='auto')
        y -= 25
        text(f"d calculé = {res['d']:.1f} mm")
        # formule As
        img_path_As = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
        img_As.save(img_path_As)
        c.drawImage(img_path_As, 30*mm, (y-20)*mm, width=120*mm, preserveAspectRatio=True, mask='auto')
        y -= 25
        text(f"A_s calculé = {res['As']:.1f} mm2")
        # limites
        text(f"A_s,min = {data['Asmin']:.1f} mm2")
        text(f"A_s,max = {data['Asmax']:.1f} mm2")
        text(f"A_s choisi = {data['barres_txt']}  →  {data['Aschoisi']:.1f} mm2")
        y -= 6

    c.save()
    tmp.seek(0)
    return tmp.read()

# ----------------- Interface Streamlit -----------------
st.set_page_config(page_title="Calcul armatures – Procédé 30.37", layout="centered")
st.title("Calcul d'armatures – Procédé 30.37")

proj = st.text_input("Nom du projet", "Projet BA")
beton = st.selectbox("Classe de béton", list(beton_coeffs.keys()))
acier = st.selectbox("Type d'acier", list(acier_fyk.keys()))
col1,col2,col3 = st.columns(3)
with col1: b = st.number_input("Largeur b (mm)", 300)
with col2: h = st.number_input("Hauteur h (mm)", 500)
with col3: enrob = st.number_input("Enrobage (mm)", 30)

multi = st.checkbox("Moment supérieur + inférieur")
moments=[]
if multi:
    Msup = st.number_input("Moment supérieur (kNm)", 90.0); Minf = st.number_input("Moment inférieur (kNm)", 120.0)
    moments=[{"nom":"Moment supérieur","moment":abs(Msup)},{"nom":"Moment inférieur","moment":abs(Minf)}]
else:
    M = st.number_input("Moment (kNm)", 120.0); moments=[{"nom":"Moment","moment":abs(M)}]

st.markdown("### Choix des armatures")
nb = st.number_input("Nombre de barres",1, value=5); dia = st.number_input("Diamètre (mm)",6, value=8)
Aschoisi = calc_section_barres(nb,dia); barres_txt=f"{nb}Ø{dia}"

# ----- calculs principaux -----
coeff = beton_coeffs[beton]; mu, sigma, fctm = coeff['mu'], coeff['sigma'], coeff['fctm']
fyk = acier_fyk[acier]; fyd = fyk/1.5
dmax = h - enrob
Asmin = 0.26 * fctm / fyk * b * dmax
Asmax = 0.04 * b * h

results=[]
for m in moments:
    d = math.sqrt((m['moment']*1e6)/(mu*sigma*b)); d=min(d,dmax)
    As = (m['moment']*1e6)/(fyd*0.9*d)
    results.append({'d':d,'As':As})

# ----- Génération PDF -----
data_pdf = {
    'proj': proj, 'date': datetime.today().strftime("%d/%m/%Y"), 'beton': beton, 'acier': acier,
    'b': b, 'h': h, 'enrobage': enrob, 'dmax': dmax,
    'moments': moments, 'results': results,
    'Asmin': Asmin, 'Asmax': Asmax,
    'barres_txt': barres_txt, 'Aschoisi': Aschoisi
}
pdf_bytes = build_pdf(data_pdf)
st.download_button("📄 Télécharger la note de calcul (PDF)", data=pdf_bytes, file_name=f"{proj}.pdf")
