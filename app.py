import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re
import base64
from streamlit_option_menu import option_menu

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Tuvalum Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded", # Force l'ouverture au démarrage
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# COULEURS
C_MAIN = "#0a4650"   # Vert Foncé
C_SEC = "#08e394"    # Vert Flashy
C_TER = "#dcff54"    # Vert Clair
C_SOFT = "#e0fdf4"   # Vert Doux
C_DECATHLON = "#0292e9"
C_BG = "#ffffff"
C_GRAY_LIGHT = "#f8f9fa"

# VARIABLES GLOBALES
VAT_DB = {
    "Alemania (19%)": 0.19, "Austria (20%)": 0.20, "Bélgica (21%)": 0.21,
    "Bulgaria (20%)": 0.20, "Canarias (0%)": 0.00, "Ceuta/Melilla (0%)": 0.00,
    "Chipre (19%)": 0.19, "Croacia (25%)": 0.25, "Dinamarca (25%)": 0.25,
    "Eslovaquia (20%)": 0.20, "Eslovenia (22%)": 0.22, "España (21%)": 0.21,
    "Estonia (20%)": 0.20, "Finlandia (24%)": 0.24, "Francia (20%)": 0.20,
    "Grecia (24%)": 0.24, "Hungría (27%)": 0.27, "Irlanda (23%)": 0.23,
    "Italia (22%)": 0.22, "Letonia (21%)": 0.21, "Lituania (21%)": 0.21,
    "Luxemburgo (17%)": 0.17, "Malta (18%)": 0.18, "Noruega (0% - Export)": 0.00,
    "Otro País / Resto Mundo (0% - Export)": 0.00, "Países Bajos (21%)": 0.21,
    "Polonia (23%)": 0.23, "Portugal (23%)": 0.23, "Reino Unido (0% - Export)": 0.00,
    "Rep. Checa (21%)": 0.21, "Rumanía (19%)": 0.19, "Suecia (25%)": 0.25,
    "Suiza (0% - Export)": 0.00, "UE B2B Intracomunitario (0%)": 0.00
}

SHIPPING_COSTS = {"ES": 22.0, "FR": 79.0, "DE": 85.0, "IT": 85.0, "PT": 35.0, "BE": 49.0, "default": 105.0}
RECOND_UNIT_COST = 54.5

# ==============================================================================
# 2. CSS "NUCLEAR" (OVERRIDE THEME)
# ==============================================================================
st.markdown(
    f"""
    <meta name="robots" content="noindex, nofollow">
    <style>
        /* 1. VARIABLE OVERRIDE: CECI REMPLACE LE ROUGE PARTOUT */
        :root {{
            --primary-color: {C_SEC};
            --background-color: #ffffff;
            --secondary-background-color: #f0f2f6;
            --text-color: #31333F;
            --font: sans-serif;
        }}
        
        /* 2. LAYOUT */
        .block-container {{padding-top: 2rem !important; padding-bottom: 2rem !important;}}
        #MainMenu, footer {{visibility: hidden; display: none !important;}}
        [data-testid="stAppViewContainer"], .stApp {{background-color: white !important;}}
        
        /* 3. SIDEBAR ARROW FIX (LA FLECHE REVIENT !) */
        [data-testid="stSidebarCollapsedControl"] {{
            display: block !important;
            color: {C_MAIN} !important;
            background-color: white !important;
            border-radius: 50%;
            border: 1px solid #eee;
            z-index: 100000;
        }}
        /* Cacher la ligne rouge du haut uniquement */
        [data-testid="stDecoration"] {{display: none !important;}}
        
        /* 4. FORCAGE BORDURES VERTES (INPUTS, SELECTS) */
        /* Cible tous les inputs au focus */
        .stTextInput input:focus, 
        .stNumberInput input:focus, 
        div[data-baseweb="select"] > div:focus-within,
        div[data-baseweb="base-input"]:focus-within {{
            border-color: {C_SEC} !important;
            box-shadow: 0 0 0 1px {C_SEC} !important;
        }}

        /* 5. CALENDRIER & RADIOS (ZERO ROUGE) */
        div[data-baseweb="calendar"] button[aria-selected="true"] {{background-color: {C_SEC} !important; color: {C_MAIN} !important;}}
        div[data-baseweb="calendar"] div[aria-selected="true"] {{background-color: {C_SEC} !important;}}
        span[data-baseweb="tag"] {{background-color: {C_SEC} !important;}}
        
        /* 6. BOUTONS */
        .stButton > button {{
            background-color: {C_MAIN} !important; color: white !important; border: none;
            transition: all 0.3s ease;
        }}
        .stButton > button:hover {{
            background-color: {C_SEC} !important; color: {C_MAIN} !important;
        }}

        /* 7. KPI CARDS (FIXED HEIGHT) */
        .kpi-card, .kpi-card-soft, .kpi-card-soft-v3 {{
            padding: 15px 20px; border-radius: 15px; 
            box-shadow: 0 2px 6px rgba(0,0,0,0.03); margin-bottom: 15px; 
            height: 160px !important; display: flex; flex-direction: column; justify-content: space-between;
        }}
        .kpi-card {{ background-color: white; border: 1px solid #e1e8e8; }}
        .kpi-card-soft, .kpi-card-soft-v3 {{ background-color: {C_SOFT}; border: 1px solid #d1fae5; opacity: 0.95; }}
        
        .kpi-title {{font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase; margin-top: 5px;}} 
        .kpi-value {{font-size: 28px; color: {C_MAIN}; font-weight: 800; margin: 5px 0;}} 
        .kpi-sub-container {{display:flex; justify-content:space-between; border-top: 1px solid rgba(0,0,0,0.05); padding-top: 10px; font-size: 13px; font-weight: 600; margin-bottom: 5px;}}
        .kpi-sub-left {{color: #64748b;}} .kpi-sub-right {{color: {C_MAIN};}}
        
        .product-img {{border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 15px; width: 100%; object-fit: cover;}}
        
        /* HACK SIDEBAR PADDING */
        section[data-testid="stSidebar"] > div > div:nth-child(2) {{
            padding-top: 20px !important; padding-left: 0 !important; padding-right: 0 !important;
        }}
        [data-testid="stSidebar"] img {{margin-left: 20px;}}
    </style>
    """,
    unsafe_allow_html=True
)

# TRADUCTIONS
TRADUCTIONS = {
    "Español": {
        "nav_res": "Resultados", "nav_evol": "Evolución", "nav_table": "Tabla Ventas", "nav_calc": "Margen & Dto", "nav_price": "Control Precios",
        "opt_prev_month": "Mes Pasado", "opt_yesterday": "Ayer", "opt_today": "Hoy", "opt_month": "Este Mes", "opt_year": "Este Año", "opt_custom": "Personalizado", 
        "btn_refresh": "Actualizar",
        "t_kpi1": "Ventas Hoy (Pagadas)", "t_kpi2": "Ventas Hoy (Pendientes)", 
        "t_kpi3": "Ventas (pagadas)", "t_kpi4": "Ventas pendientes (select)",
        "sub_rev": "Ingresos", "sub_mar": "Margen",
        "chart_channel": "Canales", "chart_mp": "Marketplaces (Top 7)", "chart_subcat": "Categoría", "chart_brand": "Top 5 Marcas", "chart_price": "Rango de Precios", "chart_country": "Países",
        "avg_price": "Precio Medio", "avg_margin": "Margen Medio", "avg_margin_pct": "% Margen", "avg_rot": "Rotación Media", "loading": "⏳ Cargando...", 
        "calc_title": "Calculadora Financiera", "sku_ph": "ej: 201414", "sku_not_found": "SKU no encontrado", "age": "Antigüedad", "price_input": "Precio Venta (€)", "cost_input": "Coste Compra (€)", "discount_input": "Descuento (€)", "unit_days": "días", 
        "col_sku": "SKU", "col_order": "Pedido", "col_country": "País", "col_channel": "Canal", "col_price": "Precio Pagado", "col_cost": "Coste Compra", "col_margin": "Margen", "col_margin_tot": "Margen Total", "col_date": "Fecha Compra", 
        "pricing_title": "Control de Precios & Rotación", "col_img": "Foto", "col_p_curr": "P. Actual", "col_p_rec": "P. Rec.", "col_action": "Acción (€)", "col_margin_proj": "Margen Proy.",
        "advice_ok": "✅ Mantener Precio", "advice_disc": "📉 Descuento Máximo", "advice_neutral": "⚪ Descuento Recomendado", "btn_search": "Comparar Precio (Google)", "vat_select": "🌍 País Destino (IVA)",
        "help_fiscal_title": "📘 Ayuda Fiscal", "evol_title": "Ventas - Ingresos - Margenes", "sel_month": "Mes", "sel_year": "Año", "settings": "⚙️ Ajustes", "mp_forecast": "Ventas Marketplace (fecha selec.)"
    }
}
t = TRADUCTIONS["Español"]

# HELPERS
def date_to_spanish(dt, format_type="full"):
    months_es = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    if format_type == "month": return months_es[dt.month]
    if format_type == "day_num": return dt.strftime("%d/%m")
    return dt.strftime("%d/%m")

def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f: data = f.read(); return base64.b64encode(data).decode()
    except: return None

def fmt_price(x):
    return f"{x:,.0f}".replace(",", " ") + " €"

# KPI HELPERS
def card_kpi_white_complex(c, title, count, label_rev, val_rev, label_mar, val_mar, col):
    html = f"""<div class="kpi-card" style="border-left:5px solid {col};"><div class="kpi-title">{title}</div><div class="kpi-value">{count} <span style="font-size:16px; color:#666; font-weight:normal;"></span></div><div class="kpi-sub-container"><span class="kpi-sub-left">{label_rev} {val_rev}</span><span class="kpi-sub-right">{label_mar} {val_mar}</span></div></div>"""
    c.markdown(html, unsafe_allow_html=True)

def card_kpi_soft_v3(c, title, main_val, left_label, left_val, right_label, right_val):
    html = f"""<div class="kpi-card-soft-v3"><div class="kpi-title">{title}</div><div class="kpi-value">{main_val}</div><div class="kpi-sub-container"><span class="kpi-sub-left">{left_label} {left_val}</span><span class="kpi-sub-right">{right_label} {right_val}</span></div></div>"""
    c.markdown(html, unsafe_allow_html=True)

def card_kpi_unified(c, title, main_val, label_rev, val_rev, label_mar, val_mar, border_col, is_soft=False):
    css_class = "kpi-card-soft-v3" if is_soft else "kpi-card"
    html = f"""<div class="{css_class}" style="border-left: 5px solid {border_col};"><div class="kpi-title">{title}</div><div class="kpi-value">{main_val}</div><div class="kpi-sub-container"><span class="kpi-sub-left">{label_rev} {val_rev}</span><span class="kpi-sub-right">{label_mar} {val_mar}</span></div></div>"""
    c.markdown(html, unsafe_allow_html=True)

def plot_bar_smart(df, x_col, y_col, color_col=None, colors=None, orientation='v', strict_order=None, limit=None, show_logos=False):
    if df.empty: return go.Figure()
    if limit: df = df.head(limit)
    final_colors = []
    if show_logos and x_col == "mp_name":
        for val in df[x_col]:
            if "Decathlon" in str(val): final_colors.append(C_DECATHLON)
            else: final_colors.append(C_MAIN)
    else: final_colors = [C_MAIN] * len(df)
    if strict_order: df = df.set_index(x_col).reindex(strict_order).fillna(0).reset_index()
    else: df = df.sort_values(by=y_col, ascending=(True if orientation == 'h' else False))
    total = df[y_col].sum(); total = 1 if total == 0 else total; df["pct"] = (df[y_col] / total * 100).round(1); df["text_inside"] = df.apply(lambda x: f"<b>{x['pct']}%</b>" if x[y_col] > 0 else "", axis=1)
    if orientation == 'h' and show_logos:
        df["y_label"] = df[x_col].apply(lambda name: f"<b>{name}</b>")
        for idx, row in df.iterrows():
            img_path = f"images/brands/{str(row[x_col]).lower().replace(' ', '')}.png" 
            if os.path.exists(img_path):
                img_b64 = get_img_as_base64(img_path)
                if img_b64: df.loc[idx, "y_label"] = f"<img src='data:image/png;base64,{img_b64}' width='30' height='30' style='vertical-align:middle; margin-right:5px;'> <b>{row[x_col]}</b>"
        x_col_plot = "y_label"
    else: x_col_plot = x_col
    fig = go.Figure()
    if orientation == 'v':
        fig.add_trace(go.Bar(x=df[x_col], y=df[y_col], text=df["text_inside"], textposition='inside', marker_color=C_MAIN, textfont=dict(size=14, color='white')))
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', margin=dict(t=40,b=20,l=0,r=0), height=400, xaxis_title=None, yaxis_title=None)
        fig.update_yaxes(range=[0, df[y_col].max() * 1.15])
        for i, row in df.iterrows(): 
            if row[y_col]>0: fig.add_annotation(x=row[x_col], y=row[y_col], text=f"<b>{int(row[y_col])}</b>", yshift=15, showarrow=False, font=dict(size=16, color="black"))
    else:
        fig.add_trace(go.Bar(y=df[x_col_plot], x=df[y_col], text=df["text_inside"], textposition='inside', orientation='h', marker_color=final_colors if show_logos else C_MAIN, textfont=dict(size=12, color='white')))
        fig.update_layout(margin=dict(t=20,b=20,l=0,r=20), height=400 + (len(df)*10), xaxis_title=None, yaxis_title=None)
        max_x = df[y_col].max() * 1.15
        fig.update_xaxes(range=[0, max_x]); fig.update_yaxes(tickmode='array', tickvals=df[x_col_plot], ticktext=df[x_col_plot])
        for i, row in df.iterrows(): 
            if row[y_col]>0: fig.add_annotation(y=row[x_col_plot], x=row[y_col], text=f"<b>{int(row[y_col])}</b>", xshift=25, showarrow=False, font=dict(size=14, color="black"))
    return fig

# ==============================================================================
# 3. LOGIN & TRANSITION FIX
# ==============================================================================
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    
    bg_path = "fondo.png"; logo_path = "logo_blanc.png"
    bg_b64 = get_img_as_base64(bg_path); logo_b64 = get_img_as_base64(logo_path)
    bg_css = f"background-image: url('data:image/jpeg;base64,{bg_b64}');" if bg_b64 else "background-color: #0a4650;"
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 300px;">' if logo_b64 else '<h1 style="color:white; font-size:60px;">Tuvalum</h1>'
    
    # CSS LOGIN AVEC FORCE VERTE
    st.markdown(f"""
    <style>
        [data-testid="stHeader"], [data-testid="stToolbar"] {{display: none !important;}}
        .stApp {{background-color: white;}}
        .login-left {{position: fixed; top: 0; left: 0; width: 50%; height: 100vh; {bg_css} background-size: cover; background-position: center;}}
        .login-overlay {{position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: {C_MAIN}; opacity: 0.85; display: flex; align-items: center; justify-content: center;}}
        div[data-testid="stForm"] {{position: fixed; top: 65%; right: 25%; transform: translate(50%, -50%); width: 380px; padding: 40px; border: none; box-shadow: none; background-color: white; z-index: 999;}}
        div[data-testid="stForm"] input {{background-color: white !important; border: 1px solid #e0e0e0 !important; color: #333;}}
        /* FORCE GREEN BORDER FOCUS */
        div[data-testid="stForm"] input:focus {{border-color: {C_SEC} !important; box-shadow: 0 0 0 1px {C_SEC} !important;}}
        div[data-testid="stForm"] button {{background-color: transparent !important; color: #333 !important; border: none;}}
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{background-color: {C_SEC} !important; color: white !important; font-weight: bold; border-radius: 6px; height: 50px; margin-top: 20px;}}
    </style>""", unsafe_allow_html=True)
    
    st.markdown(f"""<div class="login-left"><div class="login-overlay">{logo_html}</div></div>""", unsafe_allow_html=True)
    
    login_placeholder = st.empty()
    with login_placeholder.form("login_form"):
        st.markdown("<h2 style='text-align:center; color:#333; margin-bottom: 30px;'>Iniciar Sesión</h2>", unsafe_allow_html=True)
        st.text_input("Email", placeholder="admin@tuvalum.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.form_submit_button("INICIAR SESIÓN", type="primary", use_container_width=True):
            if password == st.secrets["security"]["password"]:
                st.session_state["password_correct"] = True
                # TRANSITION PROPRE : On vide le placeholder AVANT de recharger
                login_placeholder.empty()
                st.rerun()
            else: st.error("Contraseña incorrecta")
    return False

if not check_password(): st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=180)
    st.markdown("---")
    st.markdown("<p style='font-size: 12px; color: #888; font-weight: bold; margin-bottom: 5px; padding-left: 10px;'>DASHBOARD</p>", unsafe_allow_html=True)
    page = option_menu(
        menu_title=None, options=[t["nav_res"], t["nav_evol"], t["nav_table"], t["nav_calc"], t["nav_price"]],
        icons=["bar-chart-fill", "graph-up", "table", "calculator", "tag"], default_index=0,
        styles={"container": {"padding": "0!important", "background-color": "transparent", "margin": "0!important", "width": "100%"}, "icon": {"color": "#64748b", "font-size": "14px"}, "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "padding": "10px 15px", "--hover-color": "#f0f2f6", "color": "#333", "border-radius": "0px", "width": "100%"}, "nav-link-selected": {"background-color": C_SEC, "color": "white", "font-weight": "bold"}}
    )
    st.markdown("---")
    st.markdown("<p style='font-size: 12px; color: #888; font-weight: bold; margin-bottom: 5px; padding-left: 10px;'>PERIODO</p>", unsafe_allow_html=True)
    date_mode = option_menu(
        menu_title=None, options=[t['opt_prev_month'], t['opt_yesterday'], t['opt_today'], t['opt_month'], t['opt_year'], t['opt_custom']],
        icons=["calendar-minus", "calendar-check", "calendar-event", "calendar-month", "calendar-range", "calendar3"], default_index=3,
        styles={"container": {"padding": "0!important", "background-color": "transparent", "margin": "0!important", "width": "100%"}, "icon": {"color": "#64748b", "font-size": "14px"}, "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "padding": "10px 15px", "--hover-color": "#f0f2f6", "color": "#333", "border-radius": "0px", "width": "100%"}, "nav-link-selected": {"background-color": C_SEC, "color": "white", "font-weight": "bold"}}
    )
    now = datetime.now(); today_dt = now.date()
    if 'start_date_state' not in st.session_state: st.session_state.start_date_state = today_dt.replace(day=1)
    if 'end_date_state' not in st.session_state: st.session_state.end_date_state = today_dt
    if date_mode == t['opt_today']: st.session_state.start_date_state = today_dt; st.session_state.end_date_state = today_dt
    elif date_mode == t['opt_yesterday']: yesterday = today_dt - timedelta(days=1); st.session_state.start_date_state = yesterday; st.session_state.end_date_state = yesterday
    elif date_mode == t['opt_month']: st.session_state.start_date_state = today_dt.replace(day=1); st.session_state.end_date_state = today_dt
    elif date_mode == t['opt_prev_month']: first_this = today_dt.replace(day=1); last_prev = first_this - timedelta(days=1); first_prev = last_prev.replace(day=1); st.session_state.start_date_state = first_prev; st.session_state.end_date_state = last_prev
    elif date_mode == t['opt_year']: st.session_state.start_date_state = today_dt.replace(month=1, day=1); st.session_state.end_date_state = today_dt
    elif date_mode == t['opt_custom']:
        with st.form("custom_date"):
            d_input = st.date_input("Seleccionar rango", value=(st.session_state.start_date_state, st.session_state.end_date_state))
            if st.form_submit_button(t["btn_refresh"]):
                if isinstance(d_input, (list, tuple)) and len(d_input) > 0: st.session_state.start_date_state = d_input[0]; st.session_state.end_date_state = d_input[1] if len(d_input) > 1 else d_input[0]
    start_date = pd.to_datetime(st.session_state.start_date_state); end_date = pd.to_datetime(st.session_state.end_date_state).replace(hour=23, minute=59, second=59)
    st.markdown("---")
    with st.expander(t["settings"], expanded=False):
        if st.button("🔄 Actualizar Datos", use_container_width=True): st.rerun()
        if st.button("🧹 Limpiar Memoria", use_container_width=True): st.cache_data.clear(); st.success("OK!")

# --- MOTEUR DATA ---
def fetch_product_details_batch(prod_id_list):
    if not prod_id_list: return {}
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]; unique_ids = list(set(prod_id_list)); DATA_MAP = {}; chunk_size = 50; chunks = [unique_ids[i:i + chunk_size] for i in range(0, len(unique_ids), chunk_size)]
    for chunk in chunks:
        query_parts = []; 
        for idx, pid in enumerate(chunk): query_parts.append(f"""p{idx}: product(id: "gid://shopify/Product/{pid}") {{ title vendor createdAt metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} category: metafield(namespace: "custom", key: "cseg_subcategoria") {{ value }} }}""")
        full_query = "{" + " ".join(query_parts) + "}"; 
        try:
            r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":full_query}, headers={"X-Shopify-Access-Token": token}); data = r.json().get("data", {})
            if data:
                for idx, pid in enumerate(chunk):
                    key = f"p{idx}"; 
                    if key in data and data[key]:
                        n = data[key]; raw_cost = n["metafield"]["value"] if n["metafield"] else "0"; cost_val = float(re.sub(r'[^\d.]', '', str(raw_cost).replace(',','.'))) if raw_cost else 0.0; fiscal_val = n["fiscal"]["value"] if n["fiscal"] else "PRO"; brand_val = n["vendor"] if n["vendor"] else "Autre"; subcat_raw = n["category"]["value"] if (n["category"] and n["category"]["value"]) else "Autre"; s_low = str(subcat_raw).lower(); subcat_clean = "Autre"
                        if "carretera" in s_low or "aero" in s_low: subcat_clean = "Carretera"
                        elif "gravel" in s_low: subcat_clean = "Gravel"
                        elif "mtb" in s_low or "rigid" in s_low: subcat_clean = "Rigidas"
                        elif "doble" in s_low: subcat_clean = "Dobles"
                        elif "electri" in s_low or "e-bike" in s_low or "ebike" in s_low: subcat_clean = "E-Bike"
                        elif "urbana" in s_low: subcat_clean = "Urbana"
                        created_at = pd.to_datetime(n["createdAt"]).tz_convert(None); DATA_MAP[pid] = {"cost": cost_val, "fiscal": fiscal_val, "brand": brand_val, "subcat": subcat_clean, "created_at": created_at}
                    else: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None}
        except: 
            for pid in chunk: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None}
    return DATA_MAP

@st.cache_data(ttl=600, show_spinner=False)
def get_data_v100(start_date_limit):
    COMMISSION_MP = 0.10; shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]; h_rest = {"X-Shopify-Access-Token": token}; limit_dt = pd.to_datetime(start_date_limit) - timedelta(days=2); url_o = f"https://{shop_url}/admin/api/2024-01/orders.json?status=any&limit=250&order=created_at+desc"; orders = []; MAX_PAGES = 100 
    for _ in range(MAX_PAGES):
        r = requests.get(url_o, headers=h_rest); 
        if r.status_code!=200: break
        od = r.json().get("orders",[]); 
        if not od: break
        orders.extend(od); 
        if pd.to_datetime(od[-1]["created_at"]).tz_convert(None) < limit_dt: break
        if 'next' in r.links: url_o = r.links['next']['url']
        else: break
    clean_o = []; product_ids_to_fetch = []; MPs=["decathlon","alltricks","bikeroom","campsider","buycycle","bikeflip","ebikemood","cycletyre"]
    for o in orders:
        t_tags = (o.get("tags","") or "").lower(); c = "Online"; mp = "-"
        if "tienda tuvalum" in t_tags: c="Tienda"
        elif "marketplace" in t_tags: c="Marketplace"; mp = next((m.capitalize() for m in MPs if m in t_tags),"Autre MP"); 
        if mp not in ["Decathlon", "Alltricks", "Campsider", "Bikeroom"] and c=="Marketplace": mp = "Autre MP"
        country = (o.get("shipping_address") or {}).get("country_code", "Autre"); raw_price = float(o["total_price"]); total_eur = raw_price
        pid = None; sku = ""
        if o.get("line_items"):
            for line in o["line_items"]:
                s = line.get("sku", "")
                if s and len(s) == 6 and (s.startswith("2") or s.startswith("5")): sku = s; pid = str(line.get("product_id") or ""); break
            if not pid and o["line_items"]: line = o["line_items"][0]; pid = str(line.get("product_id") or ""); sku = line.get("sku", "")
        if pid: product_ids_to_fetch.append(pid)
        fin_status = o.get("financial_status"); fulfill = o.get("fulfillment_status")
        if fin_status == "refunded" and fulfill != "unfulfilled": continue
        if o.get("cancelled_at") or total_eur < 200.0: continue
        clean_o.append({"date":pd.to_datetime(o["created_at"]).tz_convert(None), "total_ttc": total_eur, "status": fin_status, "channel":c, "mp_name":mp, "order_name":o["name"], "parent_id": pid, "country": country, "sku": sku})
    df_ord = pd.DataFrame(clean_o)
    if not df_ord.empty and product_ids_to_fetch:
        unique_ids = list(set(product_ids_to_fetch)); DATA_MAP = {}; chunk_size = 50; chunks = [unique_ids[i:i + chunk_size] for i in range(0, len(unique_ids), chunk_size)]
        for chunk in chunks:
            query_parts = []; 
            for idx, pid in enumerate(chunk): query_parts.append(f"""p{idx}: product(id: "gid://shopify/Product/{pid}") {{ title vendor createdAt metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} category: metafield(namespace: "custom", key: "cseg_subcategoria") {{ value }} }}""")
            full_query = "{" + " ".join(query_parts) + "}"; 
            try:
                r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":full_query}, headers={"X-Shopify-Access-Token": token}); data = r.json().get("data", {})
                if data:
                    for idx, pid in enumerate(chunk):
                        key = f"p{idx}"; 
                        if key in data and data[key]:
                            n = data[key]; raw_cost = n["metafield"]["value"] if n["metafield"] else "0"; cost_val = float(re.sub(r'[^\d.]', '', str(raw_cost).replace(',','.'))) if raw_cost else 0.0; fiscal_val = n["fiscal"]["value"] if n["fiscal"] else "PRO"; brand_val = n["vendor"] if n["vendor"] else "Autre"; subcat_raw = n["category"]["value"] if (n["category"] and n["category"]["value"]) else "Autre"; s_low = str(subcat_raw).lower(); subcat_clean = "Autre"
                            if "carretera" in s_low or "aero" in s_low: subcat_clean = "Carretera"
                            elif "gravel" in s_low: subcat_clean = "Gravel"
                            elif "mtb" in s_low or "rigid" in s_low: subcat_clean = "Rigidas"
                            elif "doble" in s_low: subcat_clean = "Dobles"
                            elif "electri" in s_low or "e-bike" in s_low or "ebike" in s_low: subcat_clean = "E-Bike"
                            elif "urbana" in s_low: subcat_clean = "Urbana"
                            created_at = pd.to_datetime(n["createdAt"]).tz_convert(None); DATA_MAP[pid] = {"cost": cost_val, "fiscal": fiscal_val, "brand": brand_val, "subcat": subcat_clean, "created_at": created_at}
                        else: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None}
            except: 
                for pid in chunk: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None}
        
        def apply_data(row):
            pid = row["parent_id"]; price = row["total_ttc"]; d = DATA_MAP.get(pid, {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None}); cost = d["cost"]; fiscal = str(d["fiscal"]).upper(); margin = 0.0; comm_mp = price * COMMISSION_MP if row["channel"] == "Marketplace" else 0.0
            if cost > 0:
                if "REBU" in fiscal: margin = ((price - cost) / 1.21) - comm_mp
                elif "INTRA" in fiscal: margin = (price - cost) - comm_mp
                else: margin = ((price / 1.21) - (cost / 1.21)) - comm_mp
            rot = (row["date"] - d["created_at"]).days if d["created_at"] else 0
            return pd.Series([cost, fiscal, margin, d["brand"], d["subcat"], max(0, rot)])
        df_ord[["cost", "fiscal", "margin_real", "brand", "subcat", "rotation"]] = df_ord.apply(apply_data, axis=1)
    return df_ord, pd.DataFrame()

# FUNCION CONTROL PRECIOS
def get_current_stock_and_pricing():
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]; all_nodes = []; has_next = True; cursor = None
    for _ in range(15):
        if not has_next: break
        q_args = f'first: 250, query: "status:active", sortKey: CREATED_AT, reverse: false'; 
        if cursor: q_args += f', after: "{cursor}"'
        q = f"""{{ products({q_args}) {{ pageInfo {{ hasNextPage endCursor }} edges {{ node {{ title tags totalInventory createdAt updatedAt featuredImage {{ url }} variants(first: 1) {{ edges {{ node {{ price compareAtPrice sku }} }} }} metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} }} }} }} }}"""
        try:
            r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":q}, headers={"X-Shopify-Access-Token": token}); d = r.json().get("data",{}).get("products",{}); all_nodes.extend(d.get("edges", [])); has_next = d.get("pageInfo", {}).get("hasNextPage", False); cursor = d.get("pageInfo", {}).get("endCursor")
        except: break
    stock_data = []; BLACKLIST = ["taller", "gift card", "garantía", "garantia", "smartsense", "accesorio", "pack", "freight", "envío", "fianza", "caja", "embalaje"]
    for n in all_nodes:
        node = n["node"]; title_lower = node.get("title", "").lower(); tags = (node.get("tags") or []); inv = node.get("totalInventory", 0)
        if inv < 1 or "bici_market" in tags or any(bad in title_lower for bad in BLACKLIST): continue
        days = (datetime.now() - pd.to_datetime(node["createdAt"]).tz_convert(None)).days; updated_at = pd.to_datetime(node["updatedAt"]).tz_convert(None)
        v_edges = node.get("variants", {}).get("edges", [])
        if not v_edges: continue
        v = v_edges[0]["node"]
        try: p_curr = float(v.get("price", 0.0)); comp_price = v.get("compareAtPrice"); p_init = float(comp_price) if comp_price else p_curr; sku = v.get("sku", "")
        except: p_curr = 0.0; p_init = 0.0; sku = ""
        raw_c_node = node.get("metafield"); raw_c = raw_c_node["value"] if raw_c_node else "0"
        try: cost = float(re.sub(r'[^\d.]', '', str(raw_c).replace(',','.'))) if raw_c else 0.0
        except: cost = 0.0
        fiscal_node = node.get("fiscal"); f = fiscal_node["value"] if fiscal_node else "PRO"; m_curr = 0.0
        if cost > 0 and p_curr > 0:
            if "REBU" in str(f).upper(): m_curr = ((p_curr - cost) / 1.21)
            elif "INTRA" in str(f).upper(): m_curr = (p_curr - cost)
            else: m_curr = ((p_curr / 1.21) - (cost / 1.21))
        stock_data.append({"sku": sku, "title": node["title"], "img": node["featuredImage"]["url"] if node["featuredImage"] else None, "days": days, "price_curr": p_curr, "price_init": p_init, "cost": cost, "fiscal": f, "margin_curr": m_curr, "updated_at": updated_at})
    return pd.DataFrame(stock_data)

def search_sku_live(sku):
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]
    q = f"""{{ products(first: 1, query: "sku:{sku}") {{ edges {{ node {{ title totalInventory updatedAt createdAt featuredImage {{ url }} m_cost: metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} m_fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} m_state: metafield(namespace: "custom", key: "custitem_all_estado") {{ value }} m_year: metafield(namespace: "custom", key: "custitem_all_anodelmodelo") {{ value }} m_size: metafield(namespace: "custom", key: "cseg_talla") {{ value }} m_size_rec: metafield(namespace: "custom", key: "cseg_tallaalturacic") {{ value }} m_frame: metafield(namespace: "custom", key: "custitem_all_materialdelcuadro") {{ value }} m_wheels: metafield(namespace: "custom", key: "custitem_all_materialrueda") {{ value }} m_speed: metafield(namespace: "custom", key: "cseg_cambiotrasero") {{ value }} m_speed_cass: metafield(namespace: "custom", key: "custitem_all_veldelcassette") {{ value }} m_plate: metafield(namespace: "custom", key: "cseg_desarrolloplat") {{ value }} m_brakes: metafield(namespace: "custom", key: "cseg_tipodefrenos") {{ value }} m_motor: metafield(namespace: "custom", key: "cseg_motor") {{ value }} m_battery: metafield(namespace: "custom", key: "cseg_capacidadbater") {{ value }} m_km: metafield(namespace: "custom", key: "custitem_kilometraje") {{ value }} variants(first: 1) {{ edges {{ node {{ price }} }} }} }} }} }} }}"""
    try:
        r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":q}, headers={"X-Shopify-Access-Token": token}); d = r.json().get("data",{}).get("products",{}).get("edges",[])
        if d:
            n = d[0]["node"]; raw_c = n["m_cost"]["value"] if n["m_cost"] else "0"; cost = float(re.sub(r'[^\d.]', '', str(raw_c).replace(',','.'))) if raw_c else 0.0; v_node = n["variants"]["edges"][0]["node"]; price = float(v_node["price"]); inv = n.get("totalInventory", 0); 
            def gv(k): return n[k]["value"] if n.get(k) else "-"; 
            specs = {"state": gv("m_state"), "year": gv("m_year"), "size": f"{gv('m_size')} ({gv('m_size_rec')})", "frame": gv("m_frame"), "wheels": f"{gv('m_wheels')}", "group": f"{gv('m_speed')} ({gv('m_speed_cass')}) - {gv('m_plate')}", "brakes": gv("m_brakes"), "ebike": None, "inv": inv}; motor = gv("m_motor"); 
            if motor != "-": specs["ebike"] = f"{motor} - {gv('m_battery')} Wh ({gv('m_km')} km)"
            fiscal = n["m_fiscal"]["value"] if n["m_fiscal"] else "PRO"
            return {"found": True, "title": n["title"], "cost": cost, "price": price, "created_at": pd.to_datetime(n["createdAt"]).tz_convert(None), "fiscal": fiscal, "img": n["featuredImage"]["url"] if n["featuredImage"] else None, "specs": specs}
    except: pass
    return {"found": False}

def calculate_smart_discount(days, current_margin, current_price, is_deposit=False):
    MIN_MARGIN_BUFFER = 50.0 # FIXED SCOPE
    if is_deposit: return 0.0
    target = 0.0; 
    if days >= 45: target = 50.0
    if days >= 75: target = 80.0
    if days >= 90: target = 120.0
    if days >= 120: target = 150.0
    if days >= 150: target = 200.0
    buffer = 0.0 if days > 365 else MIN_MARGIN_BUFFER; capacity = current_margin - buffer; return round(min(target, max(0, capacity)) / 10) * 10

# ==============================================================================
# AFFICHAGE PAGES
# ==============================================================================
placeholder = st.empty(); 
with placeholder.container(): 
    with st.spinner("Cargando, un momento por favor..."):
        df_merged, _ = get_data_v100(start_date)
placeholder.empty()

df_today = df_merged[(df_merged["date"] >= pd.to_datetime(today_dt)) & (df_merged["date"] < pd.to_datetime(today_dt) + timedelta(days=1))] if not df_merged.empty else pd.DataFrame()
df_period = df_merged[(df_merged["date"] >= start_date) & (df_merged["date"] <= end_date)] if not df_merged.empty else pd.DataFrame()

# --- PAGE RESULTADOS ---
if page == t["nav_res"]:
    # LIGNE 1: HOY
    st.subheader(f"📅 {t['opt_today']} ({date_to_spanish(today_dt)})")
    d_ok = df_today[df_today["status"]=="paid"]; d_ko = df_today[df_today["status"]!="paid"]
    k1, k2, k3, k4 = st.columns(4)
    rev_ok = d_ok['total_ttc'].sum(); mar_ok = d_ok['margin_real'].sum()
    card_kpi_white_complex(k1, t["t_kpi1"].replace("Ventas", ""), len(d_ok), "Ingresos:", fmt_price(rev_ok), "Margen:", fmt_price(mar_ok), C_MAIN)
    rev_ko = d_ko['total_ttc'].sum(); mar_ko = d_ko['margin_real'].sum()
    card_kpi_white_complex(k2, t["t_kpi2"].replace("Ventas", "") + " ⏳", len(d_ko), "Ingresos:", fmt_price(rev_ko), "Margen:", fmt_price(mar_ko), C_SEC)
    
    # LIGNE 2 (VERT DOUX) - SELECTION
    header_txt = f"{t['opt_yesterday']} ({date_to_spanish(start_date)})" if date_mode == t['opt_yesterday'] else f"{date_to_spanish(start_date, 'day_num')} - {date_to_spanish(end_date, 'day_num')}"
    st.subheader(f"📅 {header_txt}")
    p_ok = df_period[df_period["status"]=="paid"]; p_ko = df_period[df_period["status"]!="paid"]
    
    # Calculos KPIs
    count_ok = len(p_ok)
    recond_cost = count_ok * RECOND_UNIT_COST
    shipping_cost = p_ok["country"].map(SHIPPING_COSTS).fillna(SHIPPING_COSTS["default"]).sum()
    avg_shipping = shipping_cost / count_ok if count_ok > 0 else 0

    kp1, kp2, kp3, kp4 = st.columns(4)
    card_kpi_unified(kp1, t["t_kpi3"], count_ok, "Ingresos:", fmt_price(p_ok['total_ttc'].sum()), "Margen:", fmt_price(p_ok['margin_real'].sum()), C_MAIN, is_soft=True)
    card_kpi_unified(kp2, t["t_kpi4"] + " ⏳", len(p_ko), "Ingresos:", fmt_price(p_ko['total_ttc'].sum()), "Margen:", fmt_price(p_ko['margin_real'].sum()), C_SEC, is_soft=True)
    avg_price = p_ok['total_ttc'].mean() if not p_ok.empty else 0
    card_kpi_unified(kp3, "Precio Medio", fmt_price(avg_price), "", "", "", "", C_MAIN, is_soft=True)
    avg_rot = p_ok['rotation'].mean() if not p_ok.empty else 0
    card_kpi_unified(kp4, t["avg_rot"], f"{avg_rot:,.0f} {t['unit_days']}", "", "", "", "", C_MAIN, is_soft=True)
    
    # LIGNE 3 (MEDIAS Y COSTES)
    cm1, cm2, cm3, cm4 = st.columns(4)
    total_rev = p_ok['total_ttc'].sum(); total_marg = p_ok['margin_real'].sum(); avg_marg_pct = (total_marg / total_rev * 100) if total_rev > 0 else 0; avg_margin = p_ok['margin_real'].mean() if not p_ok.empty else 0
    
    card_kpi_unified(cm1, "Margen Medio", fmt_price(avg_margin), "", "", "", "", C_MAIN, is_soft=True)
    card_kpi_unified(cm2, t["avg_margin_pct"], f"{avg_marg_pct:,.1f}%", "", "", "", "", C_MAIN, is_soft=True)
    card_kpi_unified(cm3, "Coste Reacond.", fmt_price(recond_cost), "Coste medio:", fmt_price(RECOND_UNIT_COST), "", "", C_MAIN, is_soft=True)
    card_kpi_unified(cm4, "Coste Envío", fmt_price(shipping_cost), "Coste medio:", fmt_price(avg_shipping), "", "", C_MAIN, is_soft=True)

    st.markdown("---")
    
    if not p_ok.empty:
        g1, g2 = st.columns(2)
        with g1: 
            st.subheader(t["chart_channel"])
            df_c = p_ok.groupby("channel").size().reset_index(name="c")
            st.plotly_chart(plot_bar_smart(df_c, "channel", "c", "channel", {"Online": C_SEC, "Marketplace": C_MAIN, "Tienda": C_TER}), use_container_width=True)
        with g2: 
            st.subheader(t["chart_mp"])
            df_mp = p_ok[p_ok["channel"]=="Marketplace"].groupby("mp_name").size().reset_index(name="c")
            st.plotly_chart(plot_bar_smart(df_mp, "mp_name", "c", orientation='h', limit=7, show_logos=True), use_container_width=True)
        g3, g4 = st.columns(2)
        with g3: 
            st.subheader(t["chart_subcat"])
            df_s = p_ok.groupby("subcat").size().reset_index(name="c")
            st.plotly_chart(plot_bar_smart(df_s, "subcat", "c"), use_container_width=True)
        with g4: 
            st.subheader(t["chart_brand"])
            df_b = p_ok.groupby("brand").size().reset_index(name="c")
            st.plotly_chart(plot_bar_smart(df_b, "brand", "c", limit=5), use_container_width=True)
        g5, g6 = st.columns(2)
        with g5: 
            st.subheader(t["chart_country"])
            df_ctry = p_ok.groupby("country").size().reset_index(name="c")
            st.plotly_chart(plot_bar_smart(df_ctry, "country", "c", orientation='h'), use_container_width=True)
        with g6: 
            st.subheader(t["chart_price"])
            bins = [0, 1000, 1500, 2500, 4000, 100000]; labels = ["<1k", "1k-1.5k", "1.5k-2.5k", "2.5k-4k", ">4k"]
            p_ok['price_range'] = pd.cut(p_ok['total_ttc'], bins=bins, labels=labels)
            df_pr = p_ok.groupby("price_range").size().reset_index(name="c")
            st.plotly_chart(plot_bar_smart(df_pr, "price_range", "c", strict_order=labels), use_container_width=True)

# --- PAGE EVOLUCION ---
elif page == t["nav_evol"]:
    
    c_head, c_f1, c_f2 = st.columns([6, 1.5, 1.5])
    years_list = [2025, 2024, 2023, 2022]
    sel_year = c_f2.selectbox(t["sel_year"], options=years_list, index=0)
    
    start_of_year = datetime(sel_year, 1, 1)
    with st.spinner(f"Cargando datos completos de {sel_year}..."):
        df_full_year, _ = get_data_v100(start_of_year)
    
    months_in_year = [1,2,3,4,5,6,7,8,9,10,11,12]
    def_month_idx = datetime.now().month
    sel_month_idx = c_f1.selectbox(t["sel_month"], options=months_in_year, format_func=lambda x: date_to_spanish(date(2024, x, 1), 'month'), index=def_month_idx-1)
    
    with c_head: st.subheader(f"{t['evol_title']} - {date_to_spanish(date(2024, sel_month_idx, 1), 'month')} {sel_year}")
    
    # 1. GRAPH DIARIO
    df_evol = df_full_year[(df_full_year['date'].dt.month == sel_month_idx) & (df_full_year['date'].dt.year == sel_year)].copy()
    if True: 
        start_m = date(sel_year, sel_month_idx, 1); next_m = start_m + timedelta(days=32); end_m = next_m.replace(day=1) - timedelta(days=1); full_range = pd.date_range(start=start_m, end=end_m)
        daily = df_evol[df_evol["status"]=="paid"].groupby(df_evol['date'].dt.date).agg(ingresos=("total_ttc", "sum"), margen=("margin_real", "sum"), ventas=("total_ttc", "count")).reindex(full_range.date, fill_value=0).reset_index(); daily.columns = ["date", "ingresos", "margen", "ventas"]; daily["label"] = daily["date"].apply(lambda x: date_to_spanish(x, 'day_num'))
        fig_ev = make_subplots(specs=[[{"secondary_y": True}]]); fig_ev.add_trace(go.Scatter(x=daily["label"], y=daily["ingresos"], name="Ingresos (€)", line=dict(color=C_TER, shape='linear'), mode='lines+markers'), secondary_y=False); fig_ev.add_trace(go.Scatter(x=daily["label"], y=daily["margen"], name="Margen (€)", line=dict(color=C_SEC, shape='linear'), mode='lines+markers'), secondary_y=False); fig_ev.add_trace(go.Scatter(x=daily["label"], y=daily["ventas"], name="Ventas (#)", line=dict(color=C_MAIN, shape='linear', dash='dot'), mode='lines+markers'), secondary_y=True); fig_ev.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified", legend=dict(orientation="h", y=1.1)); fig_ev.update_yaxes(title_text="€", secondary_y=False, showgrid=True, gridcolor='#eee'); fig_ev.update_yaxes(title_text="#", secondary_y=True, showgrid=False); st.plotly_chart(fig_ev, use_container_width=True)

    st.markdown("---")
    st.header("VISTA ANUAL (Enero - Diciembre)")
    c_head_yr, c_sel_yr = st.columns([6, 2])
    with c_sel_yr: sel_year_anual = st.selectbox(f"{t['sel_year']} (Evolución Anual)", options=years_list, index=0)
    
    df_year = df_full_year[(df_full_year['date'].dt.year == sel_year_anual) & (df_full_year["status"]=="paid")].copy()
    full_months_idx = range(1, 13); month_map = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}; tick_vals = list(month_map.keys()); tick_text = list(month_map.values())

    st.subheader("🚲 Categorías (Evolución Anual)")
    if True:
        def map_cat(s):
            s = str(s).lower(); 
            if "carretera" in s: return "Route"; 
            if "gravel" in s: return "Gravel"; 
            if "e-bike" in s: return "E-Bike"; 
            if "rigid" in s or "doble" in s or "mtb" in s: return "VTT"; 
            return "Autre"
        df_year["cat_clean"] = df_year["subcat"].apply(map_cat)
        df_cat = df_year[df_year["cat_clean"] != "Autre"].groupby([df_year['date'].dt.month, "cat_clean"]).size().reset_index(name="count")
        df_cat.columns = ["month", "cat_clean", "count"]
        fig2 = px.line(df_cat, x="month", y="count", color="cat_clean", markers=True, color_discrete_map={"Route": C_MAIN, "VTT": C_SEC, "Gravel": C_TER, "E-Bike": "#f59e0b"})
        fig2.update_layout(height=400, xaxis_title=None, yaxis_title="Ventas (#)", hovermode="x unified", xaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_text, range=[0.5, 12.5]))
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("---")

    st.subheader("💰 Rangos de Precio (Evolución Anual)")
    if True:
        bins = [0, 1000, 1500, 2500, 4000, 100000]; labels = ["<1k", "1k-1.5k", "1.5k-2.5k", "2.5k-4k", ">4k"]
        df_year['price_range'] = pd.cut(df_year['total_ttc'], bins=bins, labels=labels)
        df_pr = df_year.groupby([df_year['date'].dt.month, "price_range"]).size().reset_index(name="count")
        df_pr.columns = ["month", "price_range", "count"]
        fig3 = px.line(df_pr, x="month", y="count", color="price_range", markers=True, color_discrete_sequence=px.colors.sequential.Teal)
        fig3.update_layout(height=400, xaxis_title=None, yaxis_title="Ventas (#)", hovermode="x unified", xaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_text, range=[0.5, 12.5]))
        st.plotly_chart(fig3, use_container_width=True)
    st.markdown("---")

    st.subheader("🌐 Canales (Evolución Anual)")
    if True:
        df_ch = df_year.groupby([df_year['date'].dt.month, "channel"]).size().reset_index(name="count")
        df_ch.columns = ["month", "channel", "count"]
        fig4 = px.line(df_ch, x="month", y="count", color="channel", markers=True, color_discrete_map={"Online": C_SEC, "Marketplace": C_MAIN, "Tienda": C_TER})
        fig4.update_layout(height=400, xaxis_title=None, yaxis_title="Ventas (#)", hovermode="x unified", xaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_text, range=[0.5, 12.5]))
        st.plotly_chart(fig4, use_container_width=True)

# --- PAGE TABLA VENTAS ---
elif page == t["nav_table"] and not df_merged.empty:
    st.header("📋 Ventas (Fecha Select)"); 
    df_x = df_period[df_period["status"]=="paid"].copy().sort_values("date", ascending=True); df_x["margin_cum"] = df_x["margin_real"].cumsum(); df_x = df_x.sort_values("date", ascending=False); df_x["#"] = range(len(df_x), 0, -1)
    
    def display_styled_table(df_input, is_mp=False):
        df_show = df_input.copy()
        if is_mp: df_show = df_show.sort_values("date", ascending=True); df_show["margin_cum"] = df_show["margin_real"].cumsum(); df_show = df_show.sort_values("date", ascending=False)
        df_show["canal_full"] = df_show.apply(lambda x: f"{x['channel']} ({x['mp_name']})" if x['channel']=="Marketplace" else x['channel'], axis=1)
        df_show["date_str"] = df_show["date"].dt.strftime("%d/%m/%Y")
        df_show["date_group"] = (df_show["date_str"] != df_show["date_str"].shift()).cumsum()
        cols = ["#", "date_str", "order_name", "canal_full", "country", "sku", "cost", "total_ttc", "margin_real", "margin_cum"]
        df_final = df_show[cols].copy(); df_final.columns = ["#", t["col_date"], t["col_order"], t["col_channel"], t["col_country"], t["col_sku"], t["col_cost"], t["col_price"], t["col_margin"], t["col_margin_tot"]]
        styler = df_final.style.format({t["col_cost"]: fmt_price, t["col_price"]: fmt_price, t["col_margin"]: fmt_price, t["col_margin_tot"]: fmt_price})
        styler = styler.set_properties(subset=[t["col_margin"], t["col_margin_tot"]], **{'background-color': '#d1fae5', 'color': '#0a4650', 'font-weight': 'bold'})
        styler = styler.apply(lambda row: [f'background-color: {"#f8f9fa" if df_show.loc[row.name, "date_group"]%2==0 else "white"}' for _ in row], axis=1)
        st.dataframe(styler, use_container_width=True, height=600, hide_index=True, column_config={"#": st.column_config.TextColumn("#", width="small")})

    display_styled_table(df_x)
    st.markdown("---"); st.subheader(t["mp_forecast"]); df_mp = df_x[df_x["channel"] == "Marketplace"].copy()
    if not df_mp.empty: display_styled_table(df_mp, is_mp=True)
    else: st.info("No hay ventas de Marketplace en este periodo.")

# --- PAGE CALCULADORA ---
elif page == t["nav_calc"]:
    c_left, c_right = st.columns([1, 1]); f_cost=0.0; f_price=0.0; f_fiscal="PRO"; f_img=None; specs={}; days_stock=0; f_title=""; active_regime=None; is_deposit=False; is_sold=False
    with c_left:
        st.markdown("### ⚙️ Configuración"); sku_query = st.text_input("🚲 SKU", placeholder=t["sku_ph"])
        if sku_query:
            r = search_sku_live(sku_query.strip())
            if r["found"]:
                f_cost=r["cost"]; f_price=r["price"]; f_fiscal=r["fiscal"]; f_img=r["img"]; specs=r["specs"]; f_title=r["title"]; days_stock = (datetime.now() - r["created_at"]).days if pd.notnull(r["created_at"]) else 0; f_fiscal_up = str(f_fiscal).upper(); active_regime = "REBU" if "REBU" in f_fiscal_up else ("INTRA" if "INTRA" in f_fiscal_up else "PRO"); is_deposit = str(sku_query).startswith("5"); is_sold = specs["inv"] < 1
                if is_deposit: st.error("⛔ DEPÓSITO - NO DESCUENTO")
            else: st.warning(t["sku_not_found"])
        sel_country = st.selectbox(t["vat_select"], options=sorted(list(VAT_DB.keys())), index=11); vat_rate = VAT_DB[sel_country]
        c_i1, c_i2, c_i3 = st.columns(3); cost_val = c_i1.number_input(t["cost_input"], value=float(f_cost), step=10.0); price_val = c_i2.number_input(t["price_input"], value=float(f_price), step=10.0); disc_val = c_i3.number_input(t["discount_input"], value=0.0, step=10.0); final_P = max(0, price_val - disc_val)
        if f_title: st.link_button(f"🔍 {t['btn_search']}", f"https://www.google.com/search?q={f_title} {specs.get('year','')} precio", type="secondary", use_container_width=True)
        st.markdown("---"); m_curr = ((price_val - cost_val)/1.21) if "REBU" in str(f_fiscal) else ((price_val - cost_val) if "INTRA" in str(f_fiscal) else ((price_val/1.21) - (cost_val/1.21))); rec_disc = calculate_smart_discount(days_stock, m_curr, price_val, is_deposit)
        if not sku_query: st.markdown(f"<div style='background:#e5e7eb; color:#6b7280; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{t['advice_neutral']}</div>", unsafe_allow_html=True)
        else:
            if is_deposit: st.markdown(f"<div style='background:#fee2e2; color:#991b1b; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>⛔ NO DESCUENTO (DEPÓSITO)</div>", unsafe_allow_html=True)
            elif rec_disc > 0: st.markdown(f"<div style='background:#ffa421; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{t['advice_disc']}: -{int(rec_disc)} €</div>", unsafe_allow_html=True)
            else: st.markdown(f"<div style='background:#065f46; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{t['advice_ok']}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        final_margin = (final_P - cost_val)/1.21 if active_regime == "REBU" else ((final_P/(1+vat_rate)) - (cost_val/1.21) if active_regime == "PRO" else ((final_P/(1+vat_rate)) - cost_val if active_regime == "INTRA" else 0))
        if active_regime: st.markdown(f"""<div style="background:{C_SOFT}; border: 3px solid {C_SEC}; transform:scale(1.02); box-shadow:0 10px 20px rgba(0,0,0,0.1); padding:20px; border-radius:15px; text-align:center; margin: 0 auto; width: 100%; margin-bottom:15px;"><div style="font-weight:bold; color:#555; font-size:18px;">{active_regime} -> {sel_country}</div><div style="font-size:42px; font-weight:900; color:{C_MAIN}">{fmt_price(final_margin)}</div></div>""", unsafe_allow_html=True)
        with st.expander(t["help_fiscal_title"], expanded=False):
            st.markdown("""
            ### 1️⃣ ORIGEN REBU (Comprado a Particular)
            Es el caso más común. Compramos la bici a una persona física que no emite factura con IVA.
            * **La Fórmula:** `((PVP - Coste) / 1.21)`
            * **Explicación:** Hacienda solo nos cobra el 21% de IVA sobre nuestro **BENEFICIO** (la diferencia entre compra y venta), no sobre el total.
            * **Ejemplo:**
                * Compras por 1.200 €, Vendes por 2.000 €.
                * Beneficio Bruto = 800 €.
                * Hacienda se lleva el IVA de esos 800 € (aprox 139 €).
                * Te quedan limpios **661 €** de margen neto (antes de gastos).

            ### 2️⃣ ORIGEN PRO (Comprado a Tienda/Empresa)
            Compramos la bici con una factura oficial española con IVA desglosado.
            * **La Fórmula:** `(PVP / 1.21) - (Coste / 1.21)`
            * **Explicación:** Al vender, debemos devolver a Hacienda el 21% del **PRECIO TOTAL** de venta.
            * **Ejemplo:**
                * Compras por 1.000 € (+210 IVA), Vendes por 2.000 € (IVA incl).
                * Hacienda se lleva el 21% de 2.000 € (aprox 347 €).
                * Pero te deduces los 210 € que pagaste al comprar.
                * Resultado: Pagas la diferencia a Hacienda.

            ### 3️⃣ ORIGEN INTRA (Comprado a Profesional UE sin IVA)
            Compramos a una tienda en Francia/Italia/etc. sin pagar IVA (inversión sujeto pasivo).
            * **Venta España (21%):** `(PVP / 1.21) - Coste`
            * **Explicación:** El coste es neto (no pagaste IVA). Pero al vender en España, debes ingresar el 21% del PVP total.

            ### 🌍 CASOS ESPECIALES (Exportación y B2B)
            **Suiza 🇨🇭, Noruega 🇳🇴, Canarias 🇮🇨, Ceuta/Melilla y B2B UE**
            * **Regla:** La venta está **EXENTA DE IVA (0%)**.
            * **Fórmula:** `PVP - Coste`
            * **Explicación:** Cobras el precio íntegro. El cliente pagará sus impuestos locales en aduana (Suiza/Canarias) o en su contabilidad (B2B).
            * **¡OJO!** Asegúrate de tener DUA de exportación o NIF-IVA válido (VIES) para B2B.
            """)

    with c_right:
        if f_img: 
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True); bg_age = "#e5e7eb"; age_txt = "-"; color_age = "#374151"
            if days_stock > 0: age_txt = f"{days_stock} {t['unit_days']}"; bg_age = "#d1fae5" if days_stock <= 45 else ("#ffedd5" if days_stock <= 90 else "#fee2e2"); color_age = "#065f46" if days_stock <= 90 else "#991b1b"
            st.markdown(f"""<div style="background-color:{bg_age}; padding:15px; border-radius:10px; color:{color_age}; text-align:center; border:1px solid {color_age}; margin-bottom:15px;"><div style="font-size:14px; text-transform:uppercase; font-weight:bold;">{t['age']}</div><div style="font-size:32px; font-weight:800;">{age_txt}</div></div>""", unsafe_allow_html=True); st.markdown(f'<img src="{f_img}" class="product-img">', unsafe_allow_html=True)
            border_col = C_ALERT if is_sold else C_SEC; bg_col = "#fee2e2" if is_sold else "#d1fae5"; sold_txt = " 🔴 VENDIDO" if is_sold else ""
            st.markdown(f"""<div style="background-color:{bg_col}; padding:15px; border-radius:10px; color:#0a4650; margin-top:15px; border:2px solid {border_col};"><h3 style="margin:0; padding-bottom:10px;">✅ {f_title}{sold_txt}</h3><ul style="margin-left: 20px;">
            <li><b>Estado:</b> {specs.get('state','-')}</li>
            <li><b>Año:</b> {specs.get('year','-')}</li>
            <li><b>Talla:</b> {specs.get('size','-')}</li>
            <li><b>Cuadro:</b> {specs.get('frame','-')}</li>
            <li><b>Ruedas:</b> {specs.get('wheels','-')}</li>
            <li><b>Transmisión:</b> {specs.get('group','-')}</li>
            <li><b>Frenos:</b> {specs.get('brakes','-')}</li>
            </ul></div>""", unsafe_allow_html=True)

# --- PAGE CONTROL PRECIOS ---
elif page == t["nav_price"]:
    st.header(f"📉 {t['pricing_title']}"); 
    with st.spinner("Analizando inventario..."): df_stock = get_current_stock_and_pricing()
    if not df_stock.empty:
        df_stock["disc"] = df_stock.apply(lambda x: calculate_smart_discount(x["days"], x["margin_curr"], x["price_curr"]), axis=1); df_stock["rec"] = df_stock["price_curr"] - df_stock["disc"]; df_stock["m_proj"] = df_stock.apply(lambda x: (((x["rec"]-x["cost"])/1.21)) if "REBU" in str(x["fiscal"]) else (((x["rec"]/1.21)-(x["cost"]/1.21))), axis=1)
        cfg = {"img": st.column_config.ImageColumn(t["col_img"]), "sku": st.column_config.TextColumn("SKU"), "days": st.column_config.NumberColumn("Días Stock", format="%d"), "price_curr": st.column_config.NumberColumn(t["col_p_curr"], format="%d€"), "rec": st.column_config.NumberColumn(t["col_p_rec"], format="%d€"), "disc": st.column_config.NumberColumn(t["col_action"], format="-%d€"), "m_proj": st.column_config.NumberColumn(t["col_margin_proj"], format="%d€"), "updated_at": st.column_config.DateColumn("Últ. Modif.", format="DD/MM/YYYY")}
        df_crit = df_stock[df_stock["days"] > 360]; df_urg = df_stock[(df_stock["days"] > 180) & (df_stock["days"] <= 360)]; df_warn = df_stock[(df_stock["days"] > 90) & (df_stock["days"] <= 180)]; df_watch = df_stock[(df_stock["days"] > 45) & (df_stock["days"] <= 90)]
        with st.expander(f"🔴 CRITICO (> 360 días) - {len(df_crit)} bicis", expanded=True): st.data_editor(df_crit, column_config=cfg, use_container_width=True, hide_index=True, key="crit") if not df_crit.empty else st.info("0 bicis.")
        with st.expander(f"🟠 URGENTE (180-360 días) - {len(df_urg)} bicis", expanded=True): st.data_editor(df_urg, column_config=cfg, use_container_width=True, hide_index=True, key="urg") if not df_urg.empty else st.info("0 bicis.")
        with st.expander(f"🟡 ATENCION (90-180 días) - {len(df_warn)} bicis", expanded=False): st.data_editor(df_warn, column_config=cfg, use_container_width=True, hide_index=True, key="warn") if not df_warn.empty else st.info("0 bicis.")
        with st.expander(f"🟢 MONITORIZAR (45-90 días) - {len(df_watch)} bicis", expanded=False): st.data_editor(df_watch, column_config=cfg, use_container_width=True, hide_index=True, key="watch") if not df_watch.empty else st.info("0 bicis.")
    else: st.info("No data.")
