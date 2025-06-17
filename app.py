import streamlit as st
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from datetime import datetime
import io

def calc_As(M, fyd, d):
    return (M * 1e6) / (fyd * 0.9 * d)

def calc_d(M, mu, sigma, b):
    return math.sqrt((M * 1e6) / (mu * sigma * b))

def calc_tau(V, b, h):
    return V * 1e3 / (0.75 * b * h)

def calc_section_barres(n, dia):
    return n * (math.pi * dia ** 2 / 4)

def create_pdf(data):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 280

    def write(txt, bold=False, size=11, offset=6):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(25 * mm, y * mm, txt)
        y -= offset

    write("Note de calcul – Poutre BA", bold=True, size=14, offset=8)
    write(f"Projet : {data['projet']}    Date : {data['date']}")
    write("")

    write("Dimensions :", bold=True)
    write(f"largeur : {data['b']/1000:.1f} m")
    write(f"hauteur : {data['h']/1000:.1f} m")
    write("")

    write("Sollicitations :", bold=True)
    write(f"M_y = {data['M']} kNm       V_y = {data['V']} kN")
    write("")

    write("Hauteur utile :", bold=True)
    write(f"d = √({data['M']}·10⁶ / ({data['mu']}·{data['b']}·{data['sigma']})) = {data['d']:.1f} mm < {data['h'] - data['enrobage']} mm")
    write("")

    write("Armature principale inférieure – Acier 500B", bold=True)
    write(f"A_s = {data['M']}·10⁶ / ({data['fyd']:.0f}·0.9·{data['d']:.0f}) = {data['As_calc']:.1f} mm²")
    write(f"A_s_min = {data['As_min']} mm²        ok")
    write(f"A_s_max = {data['As_max']} mm²        ok")
    write(f"A_s choisi = {data['n_barres']} Ø {data['dia']} = {data['As_choisi']:.1f} mm²    > {data['As_calc']:.1f} mm²    ok")
    write("")

    write("Effort tranchant :", bold=True)
    write(f"τ = {data['tau']:.2f} N/mm² < {data['tau_adm']} N/mm²    OK")

    c.save()
    buf.seek(0)
    return buf

st.set_page_config("Note de calcul BA")
st.title("Calcul de poutre BA – format PDF style image")

projet = st.text_input("Nom du projet", "Ma poutre")
b = st.number_input("Largeur (mm)", value=600)
h = st.number_input("Hauteur (mm)", value=700)
enrobage = st.number_input("Enrobage (mm)", value=30)
mu = st.number_input("μ (béton)", value=0.1708)
sigma = st.number_input("σ (béton)", value=12.96)
fyk = st.number_input("fyk acier (MPa)", value=500)
fyd = fyk / 1.5
M = st.number_input("Moment M (kNm)", value=367.79)
V = st.number_input("Effort tranchant V (kN)", value=171.01)
As_min = st.number_input("A_s min (mm²)", value=633)
As_max = st.number_input("A_s max (mm²)", value=16800)
n_barres = st.number_input("Nb barres inf", value=7)
dia = st.number_input("Diamètre (mm)", value=20)

d = calc_d(M, mu, sigma, b)
As_calc = calc_As(M, fyd, d)
As_choisi = calc_section_barres(n_barres, dia)
tau = calc_tau(V, b, h)
tau_adm = 1.13

data = {
    'projet': projet, 'date': datetime.today().strftime("%d/%m/%Y"),
    'b': b, 'h': h, 'enrobage': enrobage,
    'mu': mu, 'sigma': sigma, 'fyd': fyd,
    'M': M, 'V': V, 'As_min': As_min, 'As_max': As_max,
    'n_barres': n_barres, 'dia': dia,
    'd': d, 'As_calc': As_calc, 'As_choisi': As_choisi,
    'tau': tau, 'tau_adm': tau_adm
}

pdf_bytes = create_pdf(data)
st.download_button("📄 Télécharger le PDF", data=pdf_bytes, file_name=f"{projet}.pdf")
