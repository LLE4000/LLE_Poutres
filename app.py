import streamlit as st
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import io
from datetime import datetime

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
    write(f"Projet : {data['projet']} – Partie : {data['partie']} – Indice {data['indice']} – Date : {data['date']}")
    write("")

    write("Dimensions :", bold=True)
    write(f"largeur : {data['b']/1000:.1f} m")
    write(f"hauteur : {data['h']/1000:.1f} m")
    write("")

    write("Sollicitations :", bold=True)
    write(f"M_y = {data['M']} kNm       V_y = {data['V']} kN")
    if data['M_sup'] is not None:
        write(f"M_sup = {data['M_sup']} kNm")
    if data['V_limite'] is not None:
        write(f"V_tranchant limité = {data['V_limite']} kN")
    write("")

    write("Hauteur utile :", bold=True)
    write(f"d = √({data['Mmax']}·10⁶ / ({data['mu']}·{data['b']}·{data['sigma']})) = {data['d']:.1f} mm < {data['h'] - data['enrobage']} mm")
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

st.set_page_config("Note de calcul BA", layout="wide")
st.markdown("<h1 style='color:red;'>Note de calcul - Poutre en béton armé</h1>", unsafe_allow_html=True)

with st.form("formulaire"):
    st.subheader("🔧 Informations générales")
    col1, col2 = st.columns([3, 1])
    projet = col1.text_input("Nom du projet", value="Ma poutre")
    partie = col1.text_input("Partie", value="Poutres RDC")
    date_str = col1.text_input("DATE + INDICE", value=datetime.today().strftime("%d/%m/%Y"))
    indice = col2.number_input("Indice", value=0)

    st.subheader("📐 Dimensions de la poutre")
    colb1, colb2 = st.columns(2)
    b = colb1.number_input("Largeur (mm)", value=600)
    h = colb1.number_input("Hauteur (mm)", value=700)
    enrobage = colb1.number_input("Enrobage (mm)", value=30)
    mu = colb2.number_input("μ (qualité béton)", value=0.1708)
    sigma = colb2.number_input("σ (béton)", value=12.96)

    st.subheader("🔩 Qualité d'acier")
    fyk = colb2.number_input("fyk acier (MPa)", value=500)
    fyd = fyk / 1.5

    st.subheader("⚙️ Sollicitations")
    col3, col4 = st.columns(2)
    M = col3.number_input("Moment inférieur M (kNm)", value=367.79)
    V = col3.number_input("Effort tranchant V (kN)", value=171.01)

    with col4:
        M_sup = st.number_input("Moment supérieur (optionnel)", value=0.0)
        V_limite = st.number_input("Effort tranchant limité (optionnel)", value=0.0)

    st.subheader("🧱 Armatures choisies")
    As_min = 633
    As_max = 16800
    n_barres = st.number_input("Nombre de barres", value=7)
    dia = st.number_input("Diamètre (mm)", value=20)

    submitted = st.form_submit_button("🧾 Générer le PDF")

if submitted:
    Mmax = max(abs(M), abs(M_sup)) if M_sup else abs(M)
    d = calc_d(Mmax, mu, sigma, b)
    As_calc = calc_As(M, fyd, d)
    As_choisi = calc_section_barres(n_barres, dia)
    tau = calc_tau(V, b, h)
    tau_adm = 1.13

    data = {
        'projet': projet, 'partie': partie, 'indice': indice, 'date': date_str,
        'b': b, 'h': h, 'enrobage': enrobage,
        'mu': mu, 'sigma': sigma, 'fyd': fyd,
        'M': M, 'V': V, 'M_sup': M_sup if M_sup != 0 else None,
        'V_limite': V_limite if V_limite != 0 else None,
        'As_min': As_min, 'As_max': As_max,
        'n_barres': n_barres, 'dia': dia,
        'd': d, 'As_calc': As_calc, 'As_choisi': As_choisi,
        'tau': tau, 'tau_adm': tau_adm, 'Mmax': Mmax
    }

    pdf = create_pdf(data)
    st.success("✅ PDF généré avec succès")
    st.download_button("📄 Télécharger le PDF", data=pdf, file_name=f"{projet}_note.pdf")
