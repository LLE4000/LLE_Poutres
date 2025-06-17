import streamlit as st
import math
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from datetime import datetime
import tempfile
import io
from PIL import Image

# Formule LaTeX -> image PNG
def render_formula(latex_code):
    fig, ax = plt.subplots(figsize=(4, 0.5))
    ax.text(0.5, 0.5, f"${latex_code}$", ha="center", va="center", fontsize=18)
    ax.axis("off")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def calcul_hauteur_utile(M_max, mu, sigma, b):
    return math.sqrt((M_max * 1e6) / (mu * sigma * b))

def calcul_As(M, fyd, d):
    return (M * 1e6) / (fyd * 0.9 * d)

def calcul_tau(V, b, h):
    return V * 1e3 / (0.75 * b * h)

def calc_section_barres(n, dia):
    return n * (math.pi * dia ** 2 / 4)

def build_pdf(data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = 280

    def write_line(text, offset=6, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 11)
        c.drawString(25 * mm, y * mm, text)
        y -= offset

    write_line("Note de calcul – Poutre BA", bold=True)
    write_line(f"Projet : {data['projet']} - Date : {data['date']}")
    write_line("")

    write_line("Dimensions :", bold=True)
    write_line(f"Largeur : {data['b']/1000:.2f} m   Hauteur : {data['h']/1000:.2f} m")
    write_line("")

    write_line("Sollicitations :", bold=True)
    write_line(f"M inf = {data['M_inf']} kNm   V = {data['V']} kN")
    if data['M_sup'] is not None:
        write_line(f"M sup = {data['M_sup']} kNm")
    if data['V_limite'] is not None:
        write_line(f"V limite = {data['V_limite']} kN")
    write_line("")

    write_line("Dimensionnement :", bold=True)
    write_line("Hauteur utile :")
    d_formula = render_formula(r"d = \sqrt{\frac{M \cdot 10^6}{\mu \cdot \sigma \cdot b}}")rac{M \cdot 10^6}{\mu \cdot \sigma \cdot b}}")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    d_formula.save(tmp.name)
    c.drawImage(tmp.name, 30 * mm, (y - 20) * mm, width=140 * mm, preserveAspectRatio=True, mask='auto')
    y -= 30
    write_line(f"d = {data['d']:.1f} mm  <  {data['h'] - data['enrobage']} mm")
    write_line("")

    write_line("Armatures principales inférieures :", bold=True)
    As_formula = render_formula(r"A_s = rac{M \cdot 10^6}{f_{yd} \cdot 0.9 \cdot d}")
    tmp2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    As_formula.save(tmp2.name)
    c.drawImage(tmp2.name, 30 * mm, (y - 20) * mm, width=140 * mm, preserveAspectRatio=True, mask='auto')
    y -= 30
    write_line(f"A_s = {data['As_inf']:.1f} mm²")
    write_line(f"A_s choisi = {data['n_barres']}Ø{data['dia_barres']} → {data['As_choisi']:.1f} mm²")
    write_line("")

    if data['M_sup'] is not None:
        write_line("Armatures supérieures :", bold=True)
        write_line(f"A_s sup = {data['As_sup']:.1f} mm²")
        write_line("")

    write_line("Effort tranchant :", bold=True)
    write_line("Formule : τ = V / (0.75 · b · h)")
    write_line(f"τ = {data['tau']:.2f} N/mm²")
    write_line(f"τ admis = {data['tau_adm']:.2f} N/mm²")
    if data['tau'] <= data['tau_adm']:
        write_line("→ OK")
    else:
        write_line("→ NON conforme")

    c.save()
    buffer.seek(0)
    return buffer.read()

st.set_page_config("Note de calcul poutre BA")
st.title("Calcul de poutre BA – Note de calcul PDF")

projet = st.text_input("Nom du projet", "Ma Poutre")
b = st.number_input("Largeur (mm)", value=300)
h = st.number_input("Hauteur (mm)", value=500)
enrobage = st.number_input("Enrobage (mm)", value=30)
mu = st.number_input("μ (selon béton)", value=0.1709)
sigma = st.number_input("σ (selon béton)", value=12.96)
fyk = st.number_input("fyk acier (MPa)", value=500)
fyd = fyk / 1.5

M_inf = st.number_input("Moment inf à l'ELS (kNm)", value=120.0)
V = st.number_input("Effort tranchant V (kN)", value=160.0)
opt_M_sup = st.checkbox("Ajouter un moment supérieur ?")
M_sup = st.number_input("Moment sup à l'ELS (kNm)", value=90.0) if opt_M_sup else None
opt_V_lim = st.checkbox("Limiter effort tranchant ?")
V_lim = st.number_input("Effort tranchant limité (kN)", value=90.0) if opt_V_lim else None

n_barres = st.number_input("Nombre de barres inférieures", value=7)
dia_barres = st.number_input("Diamètre barres (mm)", value=20)
As_choisi = calc_section_barres(n_barres, dia_barres)

Mmax = max(abs(M_inf), abs(M_sup) if M_sup else 0)
d = calcul_hauteur_utile(Mmax, mu, sigma, b)
As_inf = calcul_As(M_inf, fyd, d)
As_sup = calcul_As(M_sup, fyd, d) if M_sup else None
tau = calcul_tau(V, b, h)
tau_adm = 1.13  # par défaut

data = {
    'projet': projet, 'date': datetime.today().strftime("%d/%m/%Y"),
    'b': b, 'h': h, 'enrobage': enrobage,
    'M_inf': M_inf, 'M_sup': M_sup, 'V': V, 'V_limite': V_lim,
    'd': d, 'As_inf': As_inf, 'As_sup': As_sup,
    'n_barres': n_barres, 'dia_barres': dia_barres, 'As_choisi': As_choisi,
    'tau': tau, 'tau_adm': tau_adm
}

pdf_bytes = build_pdf(data)
st.download_button("📄 Télécharger la note de calcul", data=pdf_bytes, file_name=f"{projet}.pdf")
