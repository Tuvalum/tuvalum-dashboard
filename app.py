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
import pytz
from streamlit_option_menu import option_menu

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
fav_icon = "favicon.png" if os.path.exists("favicon.png") else "🚲"

st.set_page_config(
    page_title="Tuvalum Dashboard",
    page_icon=fav_icon,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# TIMEZONE
MADRID_TZ = pytz.timezone('Europe/Madrid')

# --- TAUX DE CHANGE ---
EXCHANGE_RATES = {
    "EUR": 1.0,
    "PLN": 0.232, "HUF": 0.0025, "SEK": 0.088, "DKK": 0.134,
    "GBP": 1.17, "CZK": 0.039, "USD": 0.92, "CHF": 1.06,
    "RON": 0.201, "BGN": 0.511, "HRK": 0.132, "NOK": 0.087
}

# COULEURS
C_MAIN = "#0a4650"
C_SEC = "#08e394"
C_TER = "#dcff54"
C_SOFT = "#e0fdf4"
C_DECATHLON = "#0292e9"
C_BG = "#ffffff"
C_GRAY_LIGHT = "#f8f9fa"

# VARIABLES GLOBALES
SHIPPING_COSTS = {"ES": 22.0, "FR": 79.0, "DE": 85.0, "IT": 85.0, "PT": 35.0, "BE": 49.0, "default": 105.0}
RECOND_UNIT_COST = 54.5
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

# ==============================================================================
# 2. CSS "NUCLEAR" (PAS DE FLECHE, VERT PARTOUT)
# ==============================================================================
st.markdown(
    f"""
    <meta name="robots" content="noindex, nofollow">
    <style>
        :root {{
            --primary-color: {C_SEC} !important;
            --background-color: #ffffff !important;
            --secondary-background-color: #f0f2f6 !important;
            --text-color: #31333F !important;
            --font: sans-serif !important;
        }}
        
        /* SIDEBAR SANS FLECHE */
        [data-testid="stSidebarCollapsedControl"] {{display: none !important;}}
        section[data-testid="stSidebar"] {{width: 300px !important; min-width: 300px !important;}}
        [data-testid="stSidebar"] img {{pointer-events: none !important; margin-left: 20px;}}
        [data-testid="stSidebar"] [data-testid="StyledFullScreenButton"] {{ display: none !important; }}
        
        /* CLEAN UI */
        header {{visibility: hidden !important;}}
        [data-testid="stToolbar"] {{display: none !important;}}
        [data-testid="stDecoration"] {{display: none !important;}}
        [data-testid="stStatusWidget"] {{display: none !important;}}
        footer {{display: none !important;}}
        .viewerBadge_container__1QSob {{display: none !important;}}

        /* INPUTS VERTS */
        input, textarea, .stSelectbox div[data-baseweb="select"] > div, .stNumberInput input, .stDateInput div {{
            border-color: #e2e8f0 !important;
            box-shadow: none !important;
        }}
        input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within,
        .stNumberInput div[data-baseweb="input"]:focus-within,
        .stDateInput div[data-baseweb="input"]:focus-within {{
            border-color: {C_SEC} !important;
            box-shadow: 0 0 0 1px {C_SEC} !important;
            outline: none !important;
        }}
        /* Boutons +/- Calculatrice */
        [data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] {{
             color: {C_MAIN} !important; border-color: transparent !important;
        }}
        [data-testid="stNumberInputStepDown"]:hover, [data-testid="stNumberInputStepUp"]:hover {{
             color: {C_SEC} !important; background-color: transparent !important;
        }}
        
        /* KPI & CARDS */
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
        .block-container {{padding-top: 2rem !important; padding-bottom: 2rem !important;}}
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
        "chart_channel": "Canales", "chart_mp": "Marketplaces (Top 5)", "chart_subcat": "Categoría", "chart_brand": "Top 5 Marcas", "chart_price": "Rango de Precios", "chart_country": "Países",
        "avg_price": "Precio Medio", "avg_margin": "Margen Medio", "avg_margin_pct": "% Margen", "avg_rot": "Rotación Media", "loading": "⏳ Cargando...", 
        "calc_title": "Calculadora Financiera", "sku_ph": "ej: 201414", "sku_not_found": "SKU no encontrado", "age": "Antigüedad", "price_input": "Precio Venta (€)", "cost_input": "Coste Compra (€)", "discount_input": "Descuento (€)", "unit_days": "días", 
        "col_sku": "SKU", "col_order": "Pedido", "col_country": "País", "col_channel": "Canal", "col_price": "Precio Pagado", "col_cost": "Coste Compra", "col_margin": "Margen", "col_margin_tot": "Margen Total", "col_date": "Fecha Compra", "col_cambio": "Precio Cambio",
        "col_disc": "Dto.", "col_comm": "Comisión MP", "col_cat": "Categoría", "col_subcat": "Subcat.", "col_type": "Tipo", "col_brand": "Marca",
        "pricing_title": "Control de Precios & Rotación", "col_img": "Foto", "col_p_curr": "P. Actual", "col_p_rec": "P. Rec.", "col_action": "Acción (€)", "col_margin_proj": "Margen Proy.",
        "advice_ok": "✅ Mantener Precio", "advice_disc": "📉 Descuento Máximo", "advice_neutral": "⚪ Descuento Recomendado", "btn_search": "Comparar Precio (Google)", "vat_select": "🌍 País Destino (IVA)",
        "help_fiscal_title": "📘 Ayuda Fiscal", "evol_title": "Ventas - Ingresos - Margenes", "sel_month": "Mes", "sel_year": "Año", "settings": "⚙️ Ajustes", "mp_forecast": "Ventas Marketplace (fecha selec.)"
    }
}
t = TRADUCTIONS["Español"]

# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f: data = f.read(); return base64.b64encode(data).decode()
    except: return None

def fmt_price(x): return f"{x:,.0f}".replace(",", " ") + " €"

def date_to_spanish(dt, format_type="full"):
    months_es = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    if format_type == "month": return months_es[dt.month]
    if format_type == "day_num": return dt.strftime("%d/%m")
    return dt.strftime("%d/%m")

def card_kpi_white_complex(c, title, count, label_rev, val_rev, label_mar, val_mar, col):
    html = f"""<div class="kpi-card" style="border-left:5px solid {col};"><div class="kpi-title">{title}</div><div class="kpi-value">{count}</div><div class="kpi-sub-container"><span class="kpi-sub-left">{label_rev} {val_rev}</span><span class="kpi-sub-right">{label_mar} {val_mar}</span></div></div>"""
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
        for val in df[x_col]: final_colors.append(C_DECATHLON if "Decathlon" in str(val) else C_MAIN)
    else: final_colors = [C_MAIN] * len(df)

    if strict_order: df = df.set_index(x_col).reindex(strict_order).fillna(0).reset_index()
    else: df = df.sort_values(by=y_col, ascending=(True if orientation == 'h' else False))
    
    total = df[y_col].sum(); total = 1 if total == 0 else total
    df["pct"] = (df[y_col] / total * 100).round(1)
    df["text_inside"] = df.apply(lambda x: f"<b>{x['pct']}%</b>" if x[y_col] > 0 else "", axis=1)
    
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
        fig.add_trace(go.Bar(x=df[x_col], y=df[y_col], text=df["text_inside"], textposition='inside', marker_color=final_colors, textfont=dict(size=14, color='white')))
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', margin=dict(t=40,b=20,l=0,r=0), height=400, xaxis_title=None, yaxis_title=None)
        fig.update_yaxes(range=[0, df[y_col].max() * 1.15])
        for i, row in df.iterrows(): 
            if row[y_col]>0: fig.add_annotation(x=row[x_col], y=row[y_col], text=f"<b>{int(row[y_col])}</b>", yshift=15, showarrow=False, font=dict(size=16, color="black"))
    else:
        fig.add_trace(go.Bar(y=df[x_col_plot], x=df[y_col], text=df["text_inside"], textposition='inside', orientation='h', marker_color=final_colors, textfont=dict(size=12, color='white')))
        fig.update_layout(margin=dict(t=20,b=20,l=0,r=20), height=400 + (len(df)*10), xaxis_title=None, yaxis_title=None)
        max_x = df[y_col].max() * 1.15
        fig.update_xaxes(range=[0, max_x]); fig.update_yaxes(tickmode='array', tickvals=df[x_col_plot], ticktext=df[x_col_plot])
        for i, row in df.iterrows(): 
            if row[y_col]>0: fig.add_annotation(y=row[x_col_plot], x=row[y_col], text=f"<b>{int(row[y_col])}</b>", xshift=25, showarrow=False, font=dict(size=14, color="black"))
    return fig

# ==============================================================================
# 4. LOGIN SYSTEM
# ==============================================================================
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    
    bg_path = "fondo.png"; logo_path = "logo_blanc.png"
    bg_b64 = get_img_as_base64(bg_path); logo_b64 = get_img_as_base64(logo_path)
    bg_css = f"background-image: url('data:image/jpeg;base64,{bg_b64}');" if bg_b64 else "background-color: #0a4650;"
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 300px;">' if logo_b64 else '<h1 style="color:white; font-size:60px;">Tuvalum</h1>'
    
    st.markdown(f"""
    <style>
        [data-testid="stHeader"], [data-testid="stToolbar"] {{display: none !important;}}
        .stApp {{background-color: white;}}
        .login-left {{position: fixed; top: 0; left: 0; width: 50%; height: 100vh; {bg_css} background-size: cover; background-position: center;}}
        .login-overlay {{position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: {C_MAIN}; opacity: 0.85; display: flex; align-items: center; justify-content: center;}}
        div[data-testid="stForm"] {{position: fixed; top: 65%; right: 25%; transform: translate(50%, -50%); width: 380px; padding: 40px; border: none; box-shadow: none; background-color: white; z-index: 999;}}
        div[data-testid="stForm"] input {{background-color: white !important; border: 1px solid #e0e0e0 !important; color: #333;}}
        div[data-testid="stForm"] input:focus {{border-color: {C_SEC} !important; box-shadow: 0 0 0 1px {C_SEC} !important; caret-color: {C_SEC} !important; outline: none !important;}}
        div[data-testid="stForm"] button {{background-color: transparent !important; color: #333 !important; border: none;}}
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{background-color: {C_SEC} !important; color: white !important; font-weight: bold; border-radius: 6px; height: 50px; margin-top: 20px;}}
    </style>""", unsafe_allow_html=True)
    
    st.markdown(f"""<div class="login-left"><div class="login-overlay">{logo_html}</div></div>""", unsafe_allow_html=True)
    
    login_ph = st.empty()
    with login_ph.form("login_form"):
        st.markdown("<h2 style='text-align:center; color:#333; margin-bottom: 30px;'>Iniciar Sesión</h2>", unsafe_allow_html=True)
        st.text_input("Email", placeholder="admin@tuvalum.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.form_submit_button("INICIAR SESIÓN", type="primary", use_container_width=True):
            if password == st.secrets["security"]["password"]:
                st.session_state["password_correct"] = True
                login_ph.empty() 
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
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "margin": "0!important", "width": "100%"},
            "icon": {"color": "#64748b", "font-size": "14px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "padding": "10px 15px", "--hover-color": "#e5e7eb", "color": "#333", "border-radius": "0px", "width": "100%"},
            "nav-link-selected": {"background-color": C_SEC, "color": "white", "font-weight": "bold"}
        }
    )
    st.markdown("---")
    st.markdown("<p style='font-size: 12px; color: #888; font-weight: bold; margin-bottom: 5px; padding-left: 10px;'>PERIODO</p>", unsafe_allow_html=True)
    date_mode = option_menu(
        menu_title=None, options=[t['opt_prev_month'], t['opt_yesterday'], t['opt_today'], t['opt_month'], t['opt_year'], t['opt_custom']],
        icons=["calendar-minus", "calendar-check", "calendar-event", "calendar-month", "calendar-range", "calendar3"], default_index=3,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent", "margin": "0!important", "width": "100%"},
            "icon": {"color": "#64748b", "font-size": "14px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "padding": "10px 15px", "--hover-color": "#e5e7eb", "color": "#333", "border-radius": "0px", "width": "100%"},
            "nav-link-selected": {"background-color": C_SEC, "color": "white", "font-weight": "bold"}
        }
    )
    # DATE MADRID
    now = datetime.now(MADRID_TZ)
    today_dt = now.date()
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
        for idx, pid in enumerate(chunk): query_parts.append(f"""p{idx}: product(id: "gid://shopify/Product/{pid}") {{ title vendor createdAt metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} modal: metafield(namespace: "custom", key: "cseg_modalidad") {{ value }} subcat: metafield(namespace: "custom", key: "cseg_subcategoria") {{ value }} km: metafield(namespace: "custom", key: "custitem_kilometraje") {{ value }} motor: metafield(namespace: "custom", key: "cseg_motor") {{ value }} brand_real: metafield(namespace: "custom", key: "cseg_all_marca") {{ value }} }}""")
        full_query = "{" + " ".join(query_parts) + "}"; 
        try:
            r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":full_query}, headers={"X-Shopify-Access-Token": token}); data = r.json().get("data", {})
            if data:
                for idx, pid in enumerate(chunk):
                    key = f"p{idx}"; 
                    if key in data and data[key]:
                        n = data[key]; 
                        raw_cost = n["metafield"]["value"] if n["metafield"] else "0"
                        cost_val = float(re.sub(r'[^\d.]', '', str(raw_cost).replace(',','.'))) if raw_cost else 0.0
                        fiscal_val = n["fiscal"]["value"] if n["fiscal"] else "PRO"
                        
                        # MARQUE (METAFIELD) + CLEANING
                        brand_raw = n["brand_real"]["value"] if (n.get("brand_real") and n["brand_real"]["value"]) else (n["vendor"] if n["vendor"] else "Autre")
                        brand_val = str(brand_raw).strip().upper()
                        
                        # CHAMPS CATEGORIE
                        subcat_raw = n["subcat"]["value"] if (n.get("subcat") and n["subcat"]["value"]) else "-"
                        km_raw = n["km"]["value"] if (n.get("km") and n["km"]["value"]) else "0"
                        motor_raw = n["motor"]["value"] if (n.get("motor") and n["motor"]["value"]) else "-"
                        
                        # LOGIQUE TYPE
                        type_final = "Muscular"
                        try:
                            if float(km_raw) > 1 or (motor_raw != "-" and motor_raw is not None): type_final = "E-Bike"
                        except: pass
                        
                        # LOGIQUE CATEGORIE
                        cat_final = "Autre"; s_low = str(subcat_raw).lower()
                        if "carretera" in s_low or "gravel" in s_low: cat_final = "Road"
                        elif "doble" in s_low or "rigid" in s_low or "mtb" in s_low: cat_final = "MTB"
                        if type_final == "E-Bike": cat_final = "E-Bike"

                        created_at = pd.to_datetime(n["createdAt"]).tz_convert(None); 
                        DATA_MAP[pid] = {"cost": cost_val, "fiscal": fiscal_val, "brand": brand_val, "cat": cat_final, "subcat": subcat_raw, "type": type_final, "created_at": created_at}
                    else: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "cat": "Autre", "subcat": "-", "type": "Muscular", "created_at": None}
        except: 
            for pid in chunk: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "cat": "Autre", "subcat": "-", "type": "Muscular", "created_at": None}
    return DATA_MAP

@st.cache_data(ttl=600, show_spinner=False)
def get_data_v100(start_date_limit):
    COMMISSION_MP = 0.10 # 10%
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]; h_rest = {"X-Shopify-Access-Token": token}; limit_dt = pd.to_datetime(start_date_limit) - timedelta(days=2); url_o = f"https://{shop_url}/admin/api/2024-01/orders.json?status=any&limit=250&order=created_at+desc"; orders = []; MAX_PAGES = 100 
    for _ in range(MAX_PAGES):
        r = requests.get(url_o, headers=h_rest); 
        if r.status_code!=200: break
        od = r.json().get("orders",[]); 
        if not od: break
        orders.extend(od); 
        if pd.to_datetime(od[-1]["created_at"]).tz_convert(None) < limit_dt: break
        if 'next' in r.links: url_o = r.links['next']['url']
        else: break
    clean_o = []; product_ids_to_fetch = []; 
    # DETECTION MARKETPLACE ELARGIE
    MP_KEYWORDS = ["decathlon", "alltricks", "refurbed", "campsider", "ebikemood", "bikeroom", "troc", "cycle tyre", "cycletyre", "buycycle", "bikeflip"]
    
    for o in orders:
        t_tags = (o.get("tags","") or "").lower(); c = "Online"; mp = "-"
        
        # LOGIQUE CANAL
        is_mp = False
        for k in MP_KEYWORDS:
            if k in t_tags:
                is_mp = True; c = "Marketplace"; mp = k.capitalize(); break
        
        if "marketplace" in t_tags: is_mp = True; c = "Marketplace";
        if mp == "-" and is_mp: mp = "Autre MP"
        
        # LOGIQUE MAGASIN
        if "venta asistida" in t_tags: c = "Tienda"

        country = (o.get("shipping_address") or {}).get("country_code", "Autre"); 
        
        # LOGIC DEVISE
        raw_price = float(o["total_price"])
        currency = o.get("currency", "EUR")
        if currency == "EUR": total_eur = raw_price
        else:
            rate = EXCHANGE_RATES.get(currency)
            total_eur = raw_price * rate if rate else 0.0
        
        raw_price_str = f"{raw_price:,.2f} {currency}"
        
        # DISCOUNT
        try: total_discount = float(o.get("total_discounts", 0.0))
        except: total_discount = 0.0
        
        pid = None; sku = ""
        if o.get("line_items"):
            for line in o["line_items"]:
                s = line.get("sku", "")
                if s and len(s) == 6 and (s.startswith("2") or s.startswith("5")): sku = s; pid = str(line.get("product_id") or ""); break
            if not pid and o["line_items"]: line = o["line_items"][0]; pid = str(line.get("product_id") or ""); sku = line.get("sku", "")
        if pid: product_ids_to_fetch.append(pid)
        
        fin_status = o.get("financial_status"); fulfill = o.get("fulfillment_status")
        if fin_status == "partially_refunded": fin_status = "paid"
        if fin_status == "refunded" and fulfill != "unfulfilled": continue
        if o.get("cancelled_at") or total_eur < 200.0: continue
        
        # TIMEZONE UTC -> MADRID
        ts = pd.to_datetime(o["created_at"])
        if ts.tzinfo is None: ts = ts.tz_localize("UTC")
        ts_local = ts.tz_convert("Europe/Madrid")
        created_at_dt = ts_local.tz_localize(None)
        
        clean_o.append({"date":created_at_dt, "total_ttc": total_eur, "raw_price_str": raw_price_str, "status": fin_status, "channel":c, "mp_name":mp, "order_name":o["name"], "parent_id": pid, "country": country, "sku": sku, "discount": -total_discount, "currency_code": currency, "raw_price_val": raw_price})

    df_ord = pd.DataFrame(clean_o)
    if not df_ord.empty and product_ids_to_fetch:
        COST_MAP = fetch_product_details_batch(product_ids_to_fetch)
        def apply_data(row):
            pid = row["parent_id"]; price = row["total_ttc"]; d = COST_MAP.get(pid, {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "cat": "Autre", "subcat": "-", "type": "Muscular", "created_at": None})
            cost = d["cost"]; fiscal = str(d["fiscal"]).upper(); 
            
            # CALCUL COMMISSION MP COMPLEXE
            comm_mp = 0.0
            if row["channel"] == "Marketplace":
                mp_low = str(row["mp_name"]).lower()
                local_price = row["raw_price_val"]
                curr = row["currency_code"]
                
                if "alltricks" in mp_low:
                     c_val = local_price * 0.10
                     comm_mp = 150.0 if c_val > 150.0 else c_val
                elif "decathlon" in mp_low:
                     if curr == "PLN":
                         c_val = local_price * 0.11; comm_mp = 1210.0 if c_val > 1210.0 else c_val
                     elif curr == "RON":
                         c_val = local_price * 0.11; comm_mp = 1320.0 if c_val > 1320.0 else c_val
                     elif curr == "HUF":
                         c_val = local_price * 0.11; comm_mp = 10450.0 if c_val > 10450.0 else c_val
                     else:
                         c_val = local_price * 0.11; comm_mp = 275.0 if c_val > 275.0 else c_val
                elif "campsider" in mp_low: comm_mp = local_price * 0.10
                elif "refurbed" in mp_low: comm_mp = local_price * 0.10
                elif "ebikemood" in mp_low: comm_mp = local_price * 0.06
                
                # Conversion commission en EUR si nécessaire
                if curr != "EUR":
                    rate = EXCHANGE_RATES.get(curr, 0.0)
                    comm_mp = comm_mp * rate

            margin = 0.0
            if cost > 0:
                if "REBU" in fiscal: margin = ((price - cost) / 1.21) - comm_mp
                elif "INTRA" in fiscal: margin = (price - cost) - comm_mp
                else: margin = ((price / 1.21) - (cost / 1.21)) - comm_mp
            
            rot = (row["date"] - d["created_at"]).days if d["created_at"] else 0
            return pd.Series([cost, fiscal, margin, d["brand"], d["cat"], d["subcat"], d["type"], max(0, rot), comm_mp])
            
        df_ord[["cost", "fiscal", "margin_real", "brand", "cat", "subcat", "type", "rotation", "commission"]] = df_ord.apply(apply_data, axis=1)
        
        # NETTOYAGE EXPORT
        cols_to_round = ["cost", "total_ttc", "margin_real", "discount", "commission"]
        df_ord[cols_to_round] = df_ord[cols_to_round].round(0)
        
    return df_ord, pd.DataFrame()

# ==============================================================================
# AFFICHAGE
# ==============================================================================
placeholder = st.empty(); 
with placeholder.container(): st.markdown(f"<div style='text-align:center; padding-top:100px;'><h3>Cargando, un momento por favor...</h3></div>", unsafe_allow_html=True)
df_merged, _ = get_data_v100(start_date); placeholder.empty()
df_today = df_merged[(df_merged["date"] >= pd.to_datetime(today_dt)) & (df_merged["date"] < pd.to_datetime(today_dt) + timedelta(days=1))] if not df_merged.empty else pd.DataFrame()
df_period = df_merged[(df_merged["date"] >= start_date) & (df_merged["date"] <= end_date)] if not df_merged.empty else pd.DataFrame()

if page == t["nav_res"]:
    st.subheader(f"📅 {t['opt_today']} ({date_to_spanish(today_dt)})")
    d_ok = df_today[df_today["status"]=="paid"]; d_ko = df_today[df_today["status"]!="paid"]
    k1, k2, k3, k4 = st.columns(4)
    rev_ok = d_ok['total_ttc'].sum(); mar_ok = d_ok['margin_real'].sum()
    card_kpi_white_complex(k1, t["t_kpi1"].replace("Ventas", ""), len(d_ok), "Ingresos:", fmt_price(rev_ok), "Margen:", fmt_price(mar_ok), C_MAIN)
    rev_ko = d_ko['total_ttc'].sum(); mar_ko = d_ko['margin_real'].sum()
    card_kpi_white_complex(k2, t["t_kpi2"].replace("Ventas", "") + " ⏳", len(d_ko), "Ingresos:", fmt_price(rev_ko), "Margen:", fmt_price(mar_ko), C_SEC)
    
    header_txt = f"{t['opt_yesterday']} ({date_to_spanish(start_date)})" if date_mode == t['opt_yesterday'] else f"{date_to_spanish(start_date, 'day_num')} - {date_to_spanish(end_date, 'day_num')}"
    st.subheader(f"📅 {header_txt}")
    p_ok = df_period[df_period["status"]=="paid"]; p_ko = df_period[df_period["status"]!="paid"]
    
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
            
            # LOGIQUE BAR CHART VERTICAL TOP 5 + AUTRE (Cleaned)
            # Nettoyage des noms MP avant groupement
            df_mp["clean_name"] = df_mp["mp_name"].apply(lambda x: "Decathlon" if "Decathlon" in str(x) else ("Alltricks" if "Alltricks" in str(x) else x))
            
            mp_counts = df_mp.groupby("clean_name").size().sort_values(ascending=False)
            top_4 = mp_counts.head(4)
            others_count = mp_counts.iloc[4:].sum()
            
            final_data = top_4.to_dict()
            if others_count > 0: final_data["Autre MP"] = others_count
            
            df_mp_final = pd.DataFrame(list(final_data.items()), columns=["mp_name", "c"])
            st.plotly_chart(plot_bar_smart(df_mp_final, "mp_name", "c", orientation='v', show_logos=True), use_container_width=True)

        g3, g4 = st.columns(2)
        with g3: 
            st.subheader(t["chart_subcat"])
            # Graphique TYPE (Muscular vs Ebike) uniquement comme demandé
            df_s = p_ok.groupby("type").size().reset_index(name="c")
            st.plotly_chart(plot_bar_smart(df_s, "type", "c"), use_container_width=True)
        with g4: 
            st.subheader(t["chart_brand"])
            # Graphique BRAND avec regroupement
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

elif page == t["nav_table"] and not df_merged.empty:
    st.header("📋 Ventas (Fecha Select)"); 
    df_x = df_period[df_period["status"]=="paid"].copy().sort_values("date", ascending=True); df_x["margin_cum"] = df_x["margin_real"].cumsum(); df_x = df_x.sort_values("date", ascending=False); df_x["#"] = range(len(df_x), 0, -1)
    
    # CORRECTION CRITIQUE KEYERROR: RESET INDEX
    df_x = df_x.reset_index(drop=True)
    
    def display_styled_table(df_input, is_mp=False):
        df_show = df_input.copy()
        
        # LOGIQUE COMPTEUR SPECIFIQUE
        if is_mp:
            df_show = df_show.sort_values("date", ascending=True)
            df_show["margin_cum"] = df_show["margin_real"].cumsum()
            df_show = df_show.sort_values("date", ascending=False)
            df_show["#"] = range(len(df_show), 0, -1)
            df_show = df_show.reset_index(drop=True) # SAFETY
        
        df_show["canal_full"] = df_show.apply(lambda x: f"{x['channel']} ({x['mp_name']})" if x['channel']=="Marketplace" else x['channel'], axis=1)
        df_show["date_str"] = df_show["date"].dt.strftime("%d/%m/%Y")
        
        # ORDRE COLONNES UNIFIE
        cols = ["#", "date_str", "order_name", "canal_full", "country", "cat", "subcat", "sku", "type", "cost", "raw_price_str", "total_ttc", "discount", "commission", "margin_real", "margin_cum"]
        col_names = ["#", t["col_date"], t["col_order"], t["col_channel"], t["col_country"], t["col_cat"], t["col_subcat"], t["col_sku"], t["col_type"], t["col_cost"], t["col_cambio"], t["col_price"], t["col_disc"], t["col_comm"], t["col_margin"], t["col_margin_tot"]]

        df_final = df_show[cols].copy(); df_final.columns = col_names
        
        styler = df_final.style.format({
            t["col_cost"]: "{:,.0f} €", t["col_price"]: "{:,.0f} €", t["col_margin"]: "{:,.0f} €", t["col_margin_tot"]: "{:,.0f} €",
            t.get("col_disc","Dto."): "{:,.0f} €", t.get("col_comm","Comisión"): "{:,.0f} €"
        })
        styler = styler.set_properties(subset=[t["col_margin"], t["col_margin_tot"]], **{'background-color': '#d1fae5', 'color': '#0a4650', 'font-weight': 'bold'})
        
        # LAMBDA SAFE AVEC INDEX CORRIGÉ
        styler = styler.apply(lambda row: [f'background-color: {"#f8f9fa" if df_show.loc[row.name, "date_group"]%2==0 else "white"}' for _ in row], axis=1)
        
        st.dataframe(styler, use_container_width=True, height=600, hide_index=True, column_config={
            "#": st.column_config.TextColumn("#", width="small"),
            t["col_date"]: st.column_config.TextColumn(t["col_date"], width="medium"),
            t["col_cambio"]: st.column_config.TextColumn(t["col_cambio"], width="medium"), # Alignement auto (text/num)
        })

    display_styled_table(df_x)
    st.markdown("---"); st.subheader(t["mp_forecast"]); df_mp = df_x[df_x["channel"] == "Marketplace"].copy()
    if not df_mp.empty: display_styled_table(df_mp, is_mp=True)
    else: st.info("No hay ventas de Marketplace en este periodo.")

elif page == t["nav_calc"] or page == t["nav_price"] or page == t["nav_evol"]:
    if page == t["nav_evol"]:
        st.header(t["evol_title"])
        st.info("Module Evolution en maintenance pour intégration KPIs")
    if page == t["nav_calc"]:
        st.header(t["calc_title"])
        c1, c2 = st.columns(2)
        with c1:
             sel_country = st.selectbox(t["vat_select"], options=sorted(list(VAT_DB.keys())), index=11)
             st.number_input(t["price_input"], value=2000.0, step=10.0)
    if page == t["nav_price"]:
        st.header(t["pricing_title"])
        st.info("Module Pricing en cours")
