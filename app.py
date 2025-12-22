import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import re
import math
import base64

# ==============================================================================
# 1. CONFIGURATION & DESIGN
# ==============================================================================
st.set_page_config(
    page_title="Tuvalum Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# COULEURS
C_MAIN = "#0a4650"   # Vert Foncé
C_SEC = "#08e394"    # Vert Flashy (Focus)
C_TER = "#dcff54"    # Vert Clair
C_SOFT = "#e0fdf4"   # Vert Doux
C_BG = "#ffffff"     # Fond Blanc
C_ALERT = "#ff4b4b"  # Rouge
C_WARN = "#ffa421"   # Orange
C_GRAY_LIGHT = "#e5e7eb"

# CSS GLOBAL
st.markdown(
    f"""
    <meta name="robots" content="noindex, nofollow">
    <style>
        /* 1. Hauteur du contenu (Baisser de 40px environ) */
        .block-container {{
            padding-top: 3.5rem !important; /* Augmenté pour baisser le contenu */
            padding-bottom: 2rem !important;
        }}
        
        /* 2. Cacher les menus Streamlit */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{display: none !important;}}
        
        /* 3. Forcer le fond blanc */
        [data-testid="stAppViewContainer"] {{background-color: white;}}
        .stApp {{background-color: white !important;}}
        
        /* 4. Style Boutons */
        .stButton button {{
            background-color: {C_MAIN} !important; 
            color: white !important; 
            border-radius: 8px; 
            border: none;
            transition: all 0.3s ease;
        }}
        .stButton button:hover {{
            background-color: {C_SEC} !important;
            color: {C_MAIN} !important;
        }}

        /* 5. INPUTS: CONTOUR VERT FLASHY AU FOCUS (Demande Client) */
        /* Cible les champs texte, nombres, et selectbox quand on clique dedans */
        div[data-baseweb="input"]:focus-within, 
        div[data-baseweb="select"]:focus-within, 
        div[data-baseweb="base-input"]:focus-within {{
            border-color: {C_SEC} !important;
            box-shadow: 0 0 0 1px {C_SEC} !important;
        }}
        /* Cible le DatePicker */
        div[data-baseweb="calendar"] {{
             border-color: {C_SEC} !important;
        }}

        /* 6. Cartes KPI */
        .kpi-card, .kpi-card-soft {{
            background-color: white; padding: 20px; border-radius: 15px; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #e1e8e8; 
            margin-bottom: 20px; min-height: 140px; display: flex; flex-direction: column; justify-content: center;
        }}
        .kpi-card-soft {{background-color: #e0fdf4; border: 1px solid #d1fae5; opacity: 0.95;}}
        .kpi-title {{font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase;}} 
        .kpi-value {{font-size: 32px; color: {C_MAIN}; font-weight: 800; margin: 5px 0;}} 
        .kpi-sub {{font-size: 16px; font-weight: 700; color: #64748b; display:flex; justify-content:space-between; margin-top:8px;}}
        
        .product-img {{border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 15px; width: 100%; object-fit: cover;}}
    </style>
    """,
    unsafe_allow_html=True
)

# RÈGLES FINANCIÈRES
MIN_MARGIN_BUFFER = 50.0
COMMISSION_MP = 0.10 

# BASE DE DATOS DE IVAS
VAT_DB = {
    "Alemania (19%)": 0.19, "Austria (20%)": 0.20, "Bélgica (21%)": 0.21,
    "Bulgaria (20%)": 0.20, "Canarias - IGIC (13.5%)": 0.135, "Ceuta/Melilla (0%)": 0.00,
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

# TEXTOS (ESPAÑOL ONLY)
TRADUCTIONS = {
    "Español": {
        "nav_header": "📊 Dashboard", "nav_res": "Resultados", "nav_table": "Tabla Ventas", "nav_calc": "Margen & Dto", "nav_price": "Control Precios",
        "date_header": "📅 Periodo", 
        "opt_prev_month": "Mes Pasado", "opt_yesterday": "Ayer", "opt_today": "Hoy", "opt_month": "Este Mes", "opt_year": "Este Año", "opt_custom": "Personalizado", 
        "btn_refresh": "Actualizar",
        "t_kpi1": "Ventas Hoy (Pagadas)", "t_kpi2": "Ventas Hoy (Pendientes)", "t_kpi3": "Ventas Selecc. (Pagadas)", "t_kpi4": "Ventas Selecc. (Pendientes)",
        "sub_rev": "Ingresos", "sub_mar": "Margen", "chart_channel": "Canales", "chart_mp": "Marketplaces", 
        "chart_subcat": "Categoría", "chart_brand": "Top 5 Marcas", "chart_price": "Rango de Precios", "chart_country": "Países",
        "avg_price": "Precio Medio", "avg_margin": "Margen Medio", "avg_margin_pct": "% Margen", "avg_rot": "Rotación Media", 
        "loading": "⏳ Cargando...", 
        "calc_title": "Calculadora Financiera", "calc_info": "Búsqueda LIVE por SKU.", "sku_ph": "ej: 201414", "sku_found": "SKU Encontrado", "sku_not_found": "SKU no encontrado", 
        "regime": "Régimen Fiscal", "age": "Antigüedad", "price_input": "Precio Venta (€)", "cost_input": "Coste Compra (€)", "discount_input": "Descuento (€)",
        "sim_title": "Simulación Margen Bruto", "unit_days": "días", "state_new": "Nuevo", "state_recond": "Reacondicionado",
        "col_sku": "SKU", "col_order": "Pedido", "col_country": "País", "col_channel": "Canal", "col_price": "Precio Pagado", "col_cost": "Coste Compra", "col_margin": "Margen", "col_margin_tot": "Margen Total", "col_rot": "Rot. (Días)", "col_prod": "Producto", "col_date": "Fecha Compra", "col_cat": "Cat.", "col_subcat": "Sub-Cat.", "col_fiscal": "Régimen",
        "pricing_title": "Control de Precios & Rotación", "col_img": "Foto", "col_p_init": "P. Origen", "col_p_curr": "P. Actual", "col_p_rec": "P. Rec.", "col_action": "Acción (€)", "col_margin_proj": "Margen Proy.",
        "advice_ok": "✅ Mantener Precio", "advice_disc": "📉 Descuento Máximo", "advice_neutral": "⚪ Descuento Recomendado",
        "btn_search": "Comparar Precio (Google)", "vat_select": "🌍 País Destino (IVA)",
        "help_fiscal_title": "📘 Ayuda Fiscal", "evol_title": "Evolución Mensual", "sel_month": "Mes", "sel_year": "Año",
        "settings": "⚙️ Ajustes", "clean_mem": "🗑️ Limpiar Memoria",
        "mp_forecast": "💰 Previsión Cobros Marketplaces"
    }
}
t = TRADUCTIONS["Español"]

# HELPER DATE
def date_to_spanish(dt, format_type="full"):
    months_es = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
    if format_type == "month": return months_es[dt.month]
    if format_type == "day_num": return dt.strftime("%d/%m")
    return dt.strftime("%d/%m")

# HELPER BASE64
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# HELPER KPI
def card_kpi_white(c, t, n, r, m, col): 
    c.markdown(f"""<div class="kpi-card" style="border-left:5px solid {col};"><div class="kpi-title">{t}</div><div class="kpi-value">{n}</div><div class="kpi-sub"><span>{r}</span><span style="color:#0a4650">{m}</span></div></div>""", unsafe_allow_html=True)

def card_kpi_soft(c, t, n, r, m, col): 
    c.markdown(f"""<div class="kpi-card-soft" style="border-left:5px solid {col};"><div class="kpi-title">{t}</div><div class="kpi-value">{n}</div><div class="kpi-sub"><span>{r}</span><span style="color:#0a4650">{m}</span></div></div>""", unsafe_allow_html=True)

# ==============================================================================
# 2. LOGIN SYSTEM
# ==============================================================================
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    
    bg_path = "fondo.png"
    if not os.path.exists(bg_path): bg_path = "fondo.png"
    logo_path = "logo_blanc.png"
    bg_b64 = get_img_as_base64(bg_path)
    logo_b64 = get_img_as_base64(logo_path)
    bg_css = f"background-image: url('data:image/jpeg;base64,{bg_b64}');" if bg_b64 else "background-color: #0a4650;"
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 300px;">' if logo_b64 else '<h1 style="color:white; font-size:60px;">Tuvalum</h1>'

    # CSS ONLY FOR LOGIN SCREEN
    st.markdown(f"""<style>
        [data-testid="stHeader"], [data-testid="stToolbar"] {{display: none;}}
        .stApp {{background-color: white;}}
        .login-left {{position: fixed; top: 0; left: 0; width: 50%; height: 100vh; {bg_css} background-size: cover; background-position: center;}}
        .login-overlay {{position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: {C_MAIN}; opacity: 0.85; display: flex; align-items: center; justify-content: center;}}
        div[data-testid="stForm"] {{
            position: fixed; top: 65%; right: 25%; transform: translate(50%, -50%);
            width: 380px; padding: 40px; border: none; box-shadow: none; background-color: white; z-index: 999;
        }}
        div[data-testid="stForm"] input {{background-color: white !important; border: 1px solid #e0e0e0; color: #333;}}
        div[data-testid="stForm"] button {{background-color: transparent !important; color: #333 !important; border: none;}}
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{
            background-color: {C_SEC} !important; color: white !important; font-weight: bold; border-radius: 6px; height: 50px; margin-top: 20px;
        }}
        .block-container {{padding: 0 !important; max-width: 100%;}}
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
                login_placeholder.empty()
                st.rerun()
            else: st.error("Contraseña incorrecta")
    return False

if not check_password(): st.stop()

# --- SIDEBAR ---
if os.path.exists("images/logo rond.png"): 
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    c_logo, _ = st.sidebar.columns([1, 0.5])
    with c_logo: st.image("images/logo rond.png", width=120)
elif os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=150)

st.sidebar.markdown("---")
st.sidebar.caption(t["nav_header"])
page = st.sidebar.radio("Nav", [t["nav_res"], t["nav_table"], t["nav_calc"], t["nav_price"]], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption(t["date_header"])
mode_options = [t['opt_prev_month'], t['opt_yesterday'], t['opt_today'], t['opt_month'], t['opt_year'], t['opt_custom']]
date_mode = st.sidebar.radio("", mode_options, index=3, label_visibility="collapsed")

now = datetime.now(); today_dt = now.date()
if 'start_date_state' not in st.session_state: st.session_state.start_date_state = today_dt.replace(day=1)
if 'end_date_state' not in st.session_state: st.session_state.end_date_state = today_dt

if date_mode == t['opt_today']: 
    st.session_state.start_date_state = today_dt
    st.session_state.end_date_state = today_dt
elif date_mode == t['opt_yesterday']:
    yesterday = today_dt - timedelta(days=1)
    st.session_state.start_date_state = yesterday
    st.session_state.end_date_state = yesterday
elif date_mode == t['opt_month']: 
    st.session_state.start_date_state = today_dt.replace(day=1)
    st.session_state.end_date_state = today_dt
elif date_mode == t['opt_prev_month']:
    first_this = today_dt.replace(day=1)
    last_prev = first_this - timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    st.session_state.start_date_state = first_prev
    st.session_state.end_date_state = last_prev
elif date_mode == t['opt_year']: 
    st.session_state.start_date_state = today_dt.replace(month=1, day=1)
    st.session_state.end_date_state = today_dt
else:
    with st.sidebar.form("custom_date"):
        d_input = st.date_input(t['opt_custom'], value=(st.session_state.start_date_state, st.session_state.end_date_state))
        if st.form_submit_button(t["btn_refresh"]):
            if isinstance(d_input, (list, tuple)) and len(d_input) > 0:
                st.session_state.start_date_state = d_input[0]
                st.session_state.end_date_state = d_input[1] if len(d_input) > 1 else d_input[0]

start_date = pd.to_datetime(st.session_state.start_date_state)
end_date = pd.to_datetime(st.session_state.end_date_state).replace(hour=23, minute=59, second=59)

st.sidebar.markdown("---")
# MENU AJUSTES DEROULANT (Demande Client)
with st.sidebar.expander(t["settings"], expanded=False):
    if st.button("🔄 Actualizar Datos"):
        st.rerun()
    if st.button("🧹 Limpiar Memoria"):
        st.cache_data.clear()
        st.success("OK!")

# --- MOTEUR DATA ---
def fetch_product_details_batch(prod_id_list):
    if not prod_id_list: return {}
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]
    unique_ids = list(set(prod_id_list))
    DATA_MAP = {}
    chunk_size = 50 
    chunks = [unique_ids[i:i + chunk_size] for i in range(0, len(unique_ids), chunk_size)]
    for chunk in chunks:
        query_parts = []
        for idx, pid in enumerate(chunk):
            query_parts.append(f"""p{idx}: product(id: "gid://shopify/Product/{pid}") {{ 
                title vendor createdAt
                metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} 
                fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} 
                category: metafield(namespace: "custom", key: "cseg_subcategoria") {{ value }}
            }}""")
        full_query = "{" + " ".join(query_parts) + "}"
        try:
            r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":full_query}, headers={"X-Shopify-Access-Token": token})
            data = r.json().get("data", {})
            if data:
                for idx, pid in enumerate(chunk):
                    key = f"p{idx}"
                    if key in data and data[key]:
                        n = data[key]
                        raw_cost = n["metafield"]["value"] if n["metafield"] else "0"
                        cost_val = float(re.sub(r'[^\d.]', '', str(raw_cost).replace(',','.'))) if raw_cost else 0.0
                        fiscal_val = n["fiscal"]["value"] if n["fiscal"] else "PRO"
                        brand_val = n["vendor"] if n["vendor"] else "Autre"
                        subcat_raw = n["category"]["value"] if (n["category"] and n["category"]["value"]) else "Autre"
                        s_low = str(subcat_raw).lower()
                        subcat_clean = "Autre"
                        if "carretera" in s_low or "aero" in s_low: subcat_clean = "Carretera"
                        elif "gravel" in s_low: subcat_clean = "Gravel"
                        elif "mtb" in s_low or "rigid" in s_low: subcat_clean = "Rigidas"
                        elif "doble" in s_low: subcat_clean = "Dobles"
                        elif "electri" in s_low or "e-bike" in s_low or "ebike" in s_low: subcat_clean = "E-Bike"
                        elif "urbana" in s_low: subcat_clean = "Urbana"
                        created_at = pd.to_datetime(n["createdAt"]).tz_convert(None)
                        DATA_MAP[pid] = {"cost": cost_val, "fiscal": fiscal_val, "brand": brand_val, "subcat": subcat_clean, "created_at": created_at}
                    else: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None}
        except:
            for pid in chunk: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None}
    return DATA_MAP

@st.cache_data(ttl=600)
def get_data_v100(start_date_limit):
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]
    h_rest = {"X-Shopify-Access-Token": token}
    limit_dt = pd.to_datetime(start_date_limit) - timedelta(days=2)
    url_o = f"https://{shop_url}/admin/api/2024-01/orders.json?status=any&limit=250&order=created_at+desc"
    orders = []; MAX_PAGES = 50 
    for _ in range(MAX_PAGES):
        r = requests.get(url_o, headers=h_rest)
        if r.status_code!=200: break
        od = r.json().get("orders",[])
        if not od: break
        orders.extend(od)
        if pd.to_datetime(od[-1]["created_at"]).tz_convert(None) < limit_dt: break
        if 'next' in r.links: url_o = r.links['next']['url']
        else: break
    
    clean_o = []; returns_o = []; product_ids_to_fetch = []
    MPs=["decathlon","alltricks","bikeroom","campsider","buycycle","bikeflip","ebikemood","cycletyre"]
    CURRENCY_RATES = {"EUR": 1.0, "CHF": 1.06, "PLN": 0.24, "CZK": 0.04, "HUF": 0.0025, "RON": 0.20, "SEK": 0.088, "DKK": 0.13, "GBP": 1.18}

    for o in orders:
        t = (o.get("tags","") or "").lower()
        c = "Online"; mp = "-"
        if "tienda tuvalum" in t: c="Tienda"
        elif "marketplace" in t:
            c="Marketplace"
            mp = next((m.capitalize() for m in MPs if m in t),"Autre MP")
            if mp not in ["Decathlon", "Alltricks", "Campsider", "Bikeroom"]: mp = "Autre MP"
        
        country = (o.get("shipping_address") or {}).get("country_code", "Autre")
        curr = o.get("currency", "EUR")
        raw_price = float(o["total_price"])
        total_eur = raw_price
        if o.get("total_price_set") and o["total_price_set"].get("shop_money"):
            sm = o["total_price_set"]["shop_money"]
            if sm["currency_code"] == "EUR": total_eur = float(sm["amount"])
            else: total_eur = raw_price * CURRENCY_RATES.get(curr, 1.0)
        else: total_eur = raw_price * CURRENCY_RATES.get(curr, 1.0)

        pid = None; sku = ""
        if o.get("line_items"):
            for line in o["line_items"]:
                s = line.get("sku", "")
                if s and len(s) == 6 and (s.startswith("2") or s.startswith("5")):
                    sku = s
                    pid = str(line.get("product_id") or "")
                    break
            if not pid and o["line_items"]:
                line = o["line_items"][0]
                pid = str(line.get("product_id") or "")
                sku = line.get("sku", "")

        if pid: product_ids_to_fetch.append(pid)
        fin_status = o.get("financial_status")
        fulfill = o.get("fulfillment_status")
        
        if fin_status == "refunded" and fulfill != "unfulfilled":
            returns_o.append({"date": pd.to_datetime(o["created_at"]).tz_convert(None), "total": total_eur, "country": country, "channel": c, "mp": mp, "sku": sku, "parent_id": pid, "order_name": o["name"]})
            continue 
            
        if o.get("cancelled_at") or total_eur < 200.0: continue
        
        clean_o.append({
            "date":pd.to_datetime(o["created_at"]).tz_convert(None),
            "total_ttc": total_eur, "status": fin_status, "is_cancelled": False,
            "channel":c, "mp_name":mp, "order_name":o["name"], "parent_id": pid,
            "country": country, "sku": sku, "order_id": str(o["id"])
        })
    
    df_ord = pd.DataFrame(clean_o)
    df_ret = pd.DataFrame(returns_o)
    
    if not df_ord.empty and product_ids_to_fetch:
        COST_MAP = fetch_product_details_batch(product_ids_to_fetch)
        def apply_data(row):
            pid = row["parent_id"]; price = row["total_ttc"]; country = str(row["country"]).upper()
            d = COST_MAP.get(pid, {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "subcat": "Autre", "created_at": None})
            cost = d["cost"]; fiscal = str(d["fiscal"]).upper(); margin = 0.0
            comm_mp = price * COMMISSION_MP if row["channel"] == "Marketplace" else 0.0
            if cost > 0:
                if "REBU" in fiscal: margin = ((price - cost) / 1.21) - comm_mp
                elif "INTRA" in fiscal: margin = (price - cost) - comm_mp 
                else: margin = ((price / 1.21) - (cost / 1.21)) - comm_mp
            rot = (row["date"] - d["created_at"]).days if d["created_at"] else 0
            return pd.Series([cost, fiscal, margin, d["brand"], d["subcat"], max(0, rot)])
        df_ord[["cost", "fiscal", "margin_real", "brand", "subcat", "rotation"]] = df_ord.apply(apply_data, axis=1)
            
    return df_ord, df_ret

def get_current_stock_and_pricing():
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]
    all_nodes = []
    has_next = True; cursor = None
    # AUGMENTATION PAGINATION A 12 (3000 produits max) pour être sûr d'avoir tout
    for _ in range(12):
        if not has_next: break
        q_args = f'first: 250, query: "status:active", sortKey: CREATED_AT, reverse: false'
        if cursor: q_args += f', after: "{cursor}"'
        q = f"""{{ products({q_args}) {{ pageInfo {{ hasNextPage endCursor }} edges {{ node {{ title tags totalInventory productType createdAt updatedAt featuredImage {{ url }} variants(first: 1) {{ edges {{ node {{ price compareAtPrice sku }} }} }} metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} }} }} }} }}"""
        try:
            r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":q}, headers={"X-Shopify-Access-Token": token})
            d = r.json().get("data",{}).get("products",{})
            all_nodes.extend(d.get("edges", []))
            has_next = d.get("pageInfo", {}).get("hasNextPage", False)
            cursor = d.get("pageInfo", {}).get("endCursor")
        except: break

    stock_data = []
    BLACKLIST_TERMS = ["taller", "gift card", "garantía", "garantia", "smartsense", "accesorio", "pack", "freight", "envío", "fianza", "caja", "embalaje"]
    for n in all_nodes:
        node = n["node"]
        title_lower = node.get("title", "").lower()
        tags = (node.get("tags") or [])
        inv = node.get("totalInventory", 0)
        if inv < 1: continue 
        if "bici_market" in tags: continue
        if any(bad in title_lower for bad in BLACKLIST_TERMS): continue
        
        days = (datetime.now() - pd.to_datetime(node["createdAt"]).tz_convert(None)).days
        updated_at = pd.to_datetime(node["updatedAt"]).tz_convert(None) # DATE MODIF
        
        v_edges = node["variants"]["edges"]
        if not v_edges: continue
        v = v_edges[0]["node"]
        p_curr = float(v["price"]); p_init = float(v["compareAtPrice"] or p_curr)
        raw_c = node["metafield"]["value"] if node["metafield"] else "0"
        cost = float(re.sub(r'[^\d.]', '', str(raw_c).replace(',','.'))) if raw_c else 0.0
        f = node["fiscal"]["value"] if node["fiscal"] else "PRO"
        m_curr = 0.0
        if cost > 0:
            if "REBU" in str(f).upper(): m_curr = ((p_curr - cost) / 1.21)
            elif "INTRA" in str(f).upper(): m_curr = (p_curr - cost)
            else: m_curr = ((p_curr / 1.21) - (cost / 1.21))
        stock_data.append({
            "sku": v["sku"], "title": node["title"], "img": node["featuredImage"]["url"] if node["featuredImage"] else None, 
            "days": days, "price_curr": p_curr, "price_init": p_init, "cost": cost, "fiscal": f, "margin_curr": m_curr,
            "updated_at": updated_at
        })
    return pd.DataFrame(stock_data)

def search_sku_live(sku):
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]
    q = f"""{{ products(first: 1, query: "sku:{sku}") {{ edges {{ node {{ title tags totalInventory updatedAt createdAt featuredImage {{ url }} 
        m_cost: metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} 
        m_fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} 
        m_state: metafield(namespace: "custom", key: "custitem_all_estado") {{ value }}
        m_year: metafield(namespace: "custom", key: "custitem_all_anodelmodelo") {{ value }}
        m_size: metafield(namespace: "custom", key: "cseg_talla") {{ value }}
        m_size_rec: metafield(namespace: "custom", key: "cseg_tallaalturacic") {{ value }}
        m_frame: metafield(namespace: "custom", key: "custitem_all_materialdelcuadro") {{ value }}
        m_wheels: metafield(namespace: "custom", key: "custitem_all_materialrueda") {{ value }}
        m_wheel_type: metafield(namespace: "custom", key: "custitem_all_tipodeneumaticos") {{ value }}
        m_speed: metafield(namespace: "custom", key: "cseg_cambiotrasero") {{ value }}
        m_speed_cass: metafield(namespace: "custom", key: "custitem_all_veldelcassette") {{ value }}
        m_plate: metafield(namespace: "custom", key: "cseg_desarrolloplat") {{ value }}
        m_cassette: metafield(namespace: "custom", key: "cseg_desarrollocass") {{ value }}
        m_brakes: metafield(namespace: "custom", key: "cseg_tipodefrenos") {{ value }}
        m_motor: metafield(namespace: "custom", key: "cseg_motor") {{ value }}
        m_battery: metafield(namespace: "custom", key: "cseg_capacidadbater") {{ value }}
        m_km: metafield(namespace: "custom", key: "custitem_kilometraje") {{ value }}
        variants(first: 1) {{ edges {{ node {{ price compareAtPrice }} }} }} 
    }} }} }} }}"""
    try:
        r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":q}, headers={"X-Shopify-Access-Token": token})
        d = r.json().get("data",{}).get("products",{}).get("edges",[])
        if d:
            n = d[0]["node"]
            raw_c = n["m_cost"]["value"] if n["m_cost"] else "0"
            cost = float(re.sub(r'[^\d.]', '', str(raw_c).replace(',','.'))) if raw_c else 0.0
            v_node = n["variants"]["edges"][0]["node"]
            price = float(v_node["price"])
            inv = n.get("totalInventory", 0)
            def gv(k): return n[k]["value"] if n.get(k) else "-"
            specs = {
                "state": gv("m_state"), "year": gv("m_year"), "size": f"{gv('m_size')} ({gv('m_size_rec')})",
                "frame": gv("m_frame"), "wheels": f"{gv('m_wheels')}", 
                "group": f"{gv('m_speed')} ({gv('m_speed_cass')}) - {gv('m_plate')}", 
                "brakes": gv("m_brakes"), "ebike": None, "inv": inv
            }
            motor = gv("m_motor")
            if motor != "-": specs["ebike"] = f"{motor} - {gv('m_battery')} Wh ({gv('m_km')} km)"
            fiscal = n["m_fiscal"]["value"] if n["m_fiscal"] else "PRO"
            return {"found": True, "title": n["title"], "cost": cost, "price": price, "created_at": pd.to_datetime(n["createdAt"]).tz_convert(None), "updated_at": pd.to_datetime(n["updatedAt"]).tz_convert(None), "fiscal": fiscal, "img": n["featuredImage"]["url"] if n["featuredImage"] else None, "specs": specs}
    except: pass
    return {"found": False}

def calculate_smart_discount(days, current_margin, current_price, is_deposit=False):
    if is_deposit: return 0.0
    target = 0.0
    if days < 45: target = 0.0
    elif 45 <= days < 75: target = 50.0
    elif 75 <= days < 90: target = 80.0
    elif 90 <= days < 120: target = 120.0
    elif 120 <= days < 150: target = 150.0
    elif days >= 150: target = 200.0
    buffer = 0.0 if days > 365 else MIN_MARGIN_BUFFER
    capacity = current_margin - buffer
    return round(min(target, max(0, capacity)) / 10) * 10

def plot_bar_smart(df, x_col, y_col, color_col=None, colors=None, fixed_order=None, orientation='v'):
    if df.empty: return go.Figure()
    if fixed_order: df = pd.merge(pd.DataFrame({x_col: fixed_order}), df, on=x_col, how="left").fillna(0)
    total = df[y_col].sum(); total = 1 if total == 0 else total
    df["pct"] = (df[y_col] / total * 100).round(1)
    df["text_inside"] = df.apply(lambda x: f"<b>{x['pct']}%</b>" if x[y_col] > 0 else "", axis=1)
    fig = go.Figure()
    if orientation == 'v':
        if color_col: fig = px.bar(df, x=x_col, y=y_col, color=color_col, color_discrete_map=colors, text="text_inside")
        else: fig.add_trace(go.Bar(x=df[x_col], y=df[y_col], text=df["text_inside"], textposition='inside', marker_color=C_MAIN, textfont=dict(size=14, color='white')))
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', margin=dict(t=40,b=20,l=0,r=0), height=400, xaxis_title=None, yaxis_title=None)
        fig.update_yaxes(range=[0, df[y_col].max() * 1.15])
        for i, row in df.iterrows():
            if row[y_col] > 0 or fixed_order: fig.add_annotation(x=row[x_col], y=row[y_col], text=f"<b>{int(row[y_col])}</b>", yshift=15, showarrow=False, font=dict(size=16, color="black"))
    else:
        df = df.sort_values(by=y_col, ascending=True)
        fig.add_trace(go.Bar(y=df[x_col], x=df[y_col], text=df["text_inside"], textposition='inside', orientation='h', marker_color=C_MAIN, textfont=dict(size=12, color='white')))
        fig.update_layout(margin=dict(t=20,b=20,l=0,r=20), height=400, xaxis_title=None, yaxis_title=None)
        max_x = df[y_col].max() * 1.15
        fig.update_xaxes(range=[0, max_x])
        for i, row in df.iterrows():
            if row[y_col] > 0: fig.add_annotation(y=row[x_col], x=row[y_col], text=f"<b>{int(row[y_col])}</b>", xshift=20, showarrow=False, font=dict(size=14, color="black"))
    return fig

# ==============================================================================
# AFFICHAGE PAGES
# ==============================================================================
placeholder = st.empty()

with placeholder.container():
    st.markdown(f"<div style='text-align:center; padding-top:100px;'><h3>{t['loading']}</h3></div>", unsafe_allow_html=True)

df_merged, df_returns = get_data_v100(start_date)

placeholder.empty()

df_today = df_merged[(df_merged["date"] >= pd.to_datetime(today_dt)) & (df_merged["date"] < pd.to_datetime(today_dt) + timedelta(days=1))] if not df_merged.empty else pd.DataFrame()
df_period = df_merged[(df_merged["date"] >= start_date) & (df_merged["date"] <= end_date)] if not df_merged.empty else pd.DataFrame()

if page == t["nav_res"] and not df_merged.empty:
    t_range = f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"
    header_txt = f"### 📅 {t['opt_yesterday']} ({date_to_spanish(start_date)})" if date_mode == t['opt_yesterday'] else f"### 📅 {date_to_spanish(start_date, 'day_num')} - {date_to_spanish(end_date, 'day_num')}"
    
    c1, c2 = st.columns(2)
    c1.markdown(f"### 📅 {t['opt_today']} ({date_to_spanish(today_dt)})")
    c2.markdown(header_txt)
    
    d_ok = df_today[df_today["status"]=="paid"]; d_ko = df_today[df_today["status"].isin(["pending","partially_paid"])]
    p_ok = df_period[df_period["status"]=="paid"]; p_ko = df_period[df_period["status"].isin(["pending","partially_paid"])]
    
    k1,k2,k3,k4 = st.columns(4)
    card_kpi_white(k1, t["t_kpi1"], len(d_ok), f"{t['sub_rev']}: {d_ok['total_ttc'].sum():,.0f}€", f"{t['sub_mar']}: {d_ok['margin_real'].sum():,.0f}€", C_MAIN)
    card_kpi_white(k2, t["t_kpi2"], len(d_ko), f"{t['sub_rev']}: {d_ko['total_ttc'].sum():,.0f}€", f"{t['sub_mar']}: {d_ko['margin_real'].sum():,.0f}€", C_SEC)
    card_kpi_soft(k3, t["t_kpi3"], len(p_ok), f"{t['sub_rev']}: {p_ok['total_ttc'].sum():,.0f}€", f"{t['sub_mar']}: {p_ok['margin_real'].sum():,.0f}€", C_MAIN)
    card_kpi_soft(k4, t["t_kpi4"], len(p_ko), f"{t['sub_rev']}: {p_ko['total_ttc'].sum():,.0f}€", f"{t['sub_mar']}: {p_ko['margin_real'].sum():,.0f}€", C_SEC)
    
    c_new1, c_new2, c_new3, c_new4 = st.columns(4)
    avg_price = p_ok['total_ttc'].mean() if not p_ok.empty else 0
    avg_margin = p_ok['margin_real'].mean() if not p_ok.empty else 0
    total_rev = p_ok['total_ttc'].sum(); total_marg = p_ok['margin_real'].sum()
    avg_marg_pct = (total_marg / total_rev * 100) if total_rev > 0 else 0
    avg_rot = p_ok['rotation'].mean() if not p_ok.empty else 0
    
    def kpi_simple(col, title, val, color): col.markdown(f"""<div class="kpi-card-soft" style="border-left:5px solid {color};"><div class="kpi-title">{title} (fecha selec.)</div><div class="kpi-value" style="font-size:30px;">{val}</div></div>""", unsafe_allow_html=True)
    kpi_simple(c_new1, t["avg_price"], f"{avg_price:,.0f}€", C_SEC)
    kpi_simple(c_new2, t["avg_margin"], f"{avg_margin:,.0f}€", C_SEC)
    kpi_simple(c_new3, t["avg_margin_pct"], f"{avg_marg_pct:,.1f}%", C_SEC)
    kpi_simple(c_new4, t["avg_rot"], f"{avg_rot:,.0f} {t['unit_days']}", C_SEC)
    
    st.markdown("---")
    
    c_head, c_f1, c_f2 = st.columns([6, 1.5, 1.5])
    years_list = [2025, 2024, 2023, 2022]
    sel_year = c_f2.selectbox(t["sel_year"], options=years_list, index=0) 
    months_in_year = [1,2,3,4,5,6,7,8,9,10,11,12]
    def_month_idx = datetime.now().month - 1
    sel_month_idx = c_f1.selectbox(t["sel_month"], options=months_in_year, format_func=lambda x: date_to_spanish(date(2024, x, 1), 'month'), index=def_month_idx)
    with c_head: st.subheader(f"{t['evol_title']} - {date_to_spanish(date(2024, sel_month_idx, 1), 'month')} {sel_year}")
    
    df_evol = df_merged[(df_merged['date'].dt.month == sel_month_idx) & (df_merged['date'].dt.year == sel_year)].copy()
    
    if not df_evol.empty or True:
        start_m = date(sel_year, sel_month_idx, 1)
        next_m = start_m + timedelta(days=32)
        end_m = next_m.replace(day=1) - timedelta(days=1)
        full_range = pd.date_range(start=start_m, end=end_m)
        daily = df_evol[df_evol["status"]=="paid"].groupby(df_evol['date'].dt.date).agg(
            ingresos=("total_ttc", "sum"),
            margen=("margin_real", "sum"),
            ventas=("total_ttc", "count")
        ).reindex(full_range.date, fill_value=0).reset_index()
        daily.columns = ["date", "ingresos", "margen", "ventas"]
        daily["label"] = daily["date"].apply(lambda x: date_to_spanish(x, 'day_num')) 
        fig_ev = make_subplots(specs=[[{"secondary_y": True}]])
        fig_ev.add_trace(go.Scatter(x=daily["label"], y=daily["ingresos"], name="Ingresos (€)", line=dict(color=C_TER, shape='linear'), mode='lines+markers'), secondary_y=False)
        fig_ev.add_trace(go.Scatter(x=daily["label"], y=daily["margen"], name="Margen (€)", line=dict(color=C_SEC, shape='linear'), mode='lines+markers'), secondary_y=False)
        fig_ev.add_trace(go.Scatter(x=daily["label"], y=daily["ventas"], name="Ventas (#)", line=dict(color=C_MAIN, shape='linear', dash='dot'), mode='lines+markers'), secondary_y=True)
        fig_ev.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified", legend=dict(orientation="h", y=1.1))
        fig_ev.update_yaxes(title_text="€", secondary_y=False, showgrid=True, gridcolor='#eee')
        fig_ev.update_yaxes(title_text="#", secondary_y=True, showgrid=False)
        st.plotly_chart(fig_ev, use_container_width=True, key="chart_evol_main")

    g1, g2 = st.columns(2)
    with g1:
        st.subheader(t["chart_channel"])
        df_c = df_period[df_period["status"]=="paid"].groupby("channel").size().reset_index(name="c")
        st.plotly_chart(plot_bar_smart(df_c, "channel", "c", "channel", {"Online":C_SEC,"Marketplace":C_MAIN,"Tienda":C_TER}, fixed_order=["Online", "Marketplace", "Tienda"]), use_container_width=True, key="c1")
    with g2:
        st.subheader(t["chart_mp"])
        df_mp = df_period[(df_period["status"]=="paid")&(df_period["channel"]=="Marketplace")].groupby("mp_name").size().reset_index(name="c")
        st.plotly_chart(plot_bar_smart(df_mp, "mp_name", "c", fixed_order=["Decathlon", "Alltricks", "Campsider", "Bikeroom", "Autre MP"]), use_container_width=True, key="c2")
    g3, g4 = st.columns(2)
    with g3:
        st.subheader(t["chart_subcat"])
        df_s = p_ok.groupby("subcat").size().reset_index(name="c").sort_values("c", ascending=False)
        st.plotly_chart(plot_bar_smart(df_s, "subcat", "c"), use_container_width=True, key="c3")
    with g4:
        st.subheader(t["chart_brand"])
        df_b = p_ok.groupby("brand").size().reset_index(name="c").sort_values("c", ascending=False).head(5)
        st.plotly_chart(plot_bar_smart(df_b, "brand", "c"), use_container_width=True, key="c4")
    g5, g6 = st.columns(2)
    with g5:
        st.subheader(t["chart_country"])
        df_ctry = p_ok.groupby("country").size().reset_index(name="c")
        st.plotly_chart(plot_bar_smart(df_ctry, "country", "c", orientation='h'), use_container_width=True, key="c5")
    with g6:
        st.subheader(t["chart_price"])
        bins = [0, 1000, 1500, 2500, 4000, 100000]; labels = ["<1k", "1k-1.5k", "1.5k-2.5k", "2.5k-4k", ">4k"]
        p_ok['price_range'] = pd.cut(p_ok['total_ttc'], bins=bins, labels=labels)
        df_pr = p_ok.groupby("price_range").size().reset_index(name="c")
        st.plotly_chart(plot_bar_smart(df_pr, "price_range", "c", fixed_order=labels), use_container_width=True, key="c6")

elif page == t["nav_table"] and not df_merged.empty:
    st.header(f"📋 {t['nav_table']}")
    
    # 1. Sort by Date Oldest -> Newest for Cumulative Sum
    df_x = df_period[df_period["status"]=="paid"].copy()
    df_x = df_x.sort_values("date", ascending=True)
    df_x["margin_cum"] = df_x["margin_real"].cumsum()
    
    # 2. Sort back Newest -> Oldest for display
    df_x = df_x.sort_values("date", ascending=False)
    
    def fmt_currency(val):
        s = f"{val:,.0f}".replace(",", " ")
        return f"{s} €"

    # Inverse Indexing (Len -> 1)
    df_x["#"] = range(len(df_x), 0, -1)
    
    # Rounding & Formatting
    df_x["margin_real"] = df_x["margin_real"].round(0)
    df_x["margin_cum"] = df_x["margin_cum"].round(0)
    
    def display_styled_table(df_input):
        df_show = df_input.copy()
        df_show["canal_full"] = df_show.apply(lambda x: f"{x['channel']} ({x['mp_name']})" if x['channel']=="Marketplace" else x['channel'], axis=1)
        df_show["date_str"] = df_show["date"].dt.strftime("%d/%m/%Y")
        
        cols_final = ["#", "order_name", "canal_full", "country", "date_str", "sku", "cost", "total_ttc", "margin_real", "margin_cum"]
        df_final = df_show[cols_final].copy()
        
        # Group dates for striping
        df_final["date_group"] = (df_final["date_str"] != df_final["date_str"].shift()).cumsum()
        
        for c in ["cost", "total_ttc", "margin_real", "margin_cum"]:
            df_final[c] = df_final[c].apply(fmt_currency)

        df_final.columns = ["#", t["col_order"], t["col_channel"], t["col_country"], t["col_date"], t["col_sku"], t["col_cost"], t["col_price"], t["col_margin"], t["col_margin_tot"], "date_group"]
        
        def highlight_rows(row):
            is_even_group = row["date_group"] % 2 == 0
            bg_color = C_GRAY_LIGHT if is_even_group else "white"
            styles = [f'background-color: {bg_color}; color: #333;'] * len(row)
            # Green for Margin columns (Index 8 & 9)
            styles[8] = f'background-color: {C_SOFT}; color: {C_MAIN};' 
            styles[9] = f'background-color: {C_SOFT}; color: {C_MAIN};' 
            return styles

        st.dataframe(
            df_final.style.apply(highlight_rows, axis=1), 
            use_container_width=True, 
            height=600, 
            hide_index=True,
            column_config={"#": st.column_config.TextColumn("#", width="small")},
            column_order=["#", t["col_order"], t["col_channel"], t["col_country"], t["col_date"], t["col_sku"], t["col_cost"], t["col_price"], t["col_margin"], t["col_margin_tot"]]
        )

    display_styled_table(df_x)
    
    st.markdown("---")
    st.subheader(t["mp_forecast"])
    df_mp = df_x[df_x["channel"] == "Marketplace"].copy()
    if not df_mp.empty:
        display_styled_table(df_mp)
    else:
        st.info("No hay ventas de Marketplace en este periodo.")

elif page == t["nav_calc"]:
    
    c_left, c_right = st.columns([1, 1])
    
    f_cost=0.0; f_price=0.0; f_fiscal="PRO"; f_img=None; specs={}; days_stock=0; f_title=""; active_regime=None; is_deposit=False; is_sold=False; last_update=None
    
    with c_left:
        st.markdown("### ⚙️ Configuración")
        sku_query = st.text_input("🚲 SKU", placeholder=t["sku_ph"])
        
        if sku_query:
            r = search_sku_live(sku_query.strip())
            if r["found"]:
                f_cost=r["cost"]; f_price=r["price"]; f_fiscal=r["fiscal"]; f_img=r["img"]; specs=r["specs"]; f_title=r["title"]
                if pd.notnull(r["created_at"]): days_stock = (datetime.now() - r["created_at"]).days
                last_update = r["updated_at"].strftime("%d/%m/%Y")
                f_fiscal_up = str(f_fiscal).upper()
                if "REBU" in f_fiscal_up: active_regime = "REBU"
                elif "INTRA" in f_fiscal_up: active_regime = "INTRA"
                else: active_regime = "PRO"
                
                if str(sku_query).startswith("5"): is_deposit = True; st.error("⛔ DEPÓSITO - NO DESCUENTO")
                if specs["inv"] < 1: is_sold = True
            else: st.warning(t["sku_not_found"])

        sel_country = st.selectbox(t["vat_select"], options=sorted(list(VAT_DB.keys())), index=11)
        vat_rate = VAT_DB[sel_country]
        
        c_i1, c_i2, c_i3 = st.columns(3)
        def_cost = f_cost if f_cost > 0 else 0.0
        def_price = f_price if f_price > 0 else 0.0
        
        cost_val = c_i1.number_input(t["cost_input"], value=float(def_cost), step=10.0)
        price_val = c_i2.number_input(t["price_input"], value=float(def_price), step=10.0)
        disc_val = c_i3.number_input(t["discount_input"], value=0.0, step=10.0)
        
        final_P = max(0, price_val - disc_val)
        
        if f_title: st.link_button(f"🔍 {t['btn_search']}", f"https://www.google.com/search?q={f_title} {specs.get('year','')} precio", type="secondary", use_container_width=True)
        
        st.markdown("---")
        
        m_curr = 0.0
        if "REBU" in str(f_fiscal): m_curr = ((price_val - cost_val)/1.21)
        elif "INTRA" in str(f_fiscal): m_curr = (price_val - cost_val)
        else: m_curr = ((price_val/1.21) - (cost_val/1.21))
        
        rec_disc = calculate_smart_discount(days_stock, m_curr, price_val, is_deposit)
        
        if not sku_query:
             st.markdown(f"<div style='background:#e5e7eb; color:#6b7280; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{t['advice_neutral']}</div>", unsafe_allow_html=True)
        else:
            if is_deposit: st.markdown(f"<div style='background:#fee2e2; color:#991b1b; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>⛔ NO DESCUENTO (DEPÓSITO)</div>", unsafe_allow_html=True)
            elif rec_disc > 0: st.markdown(f"<div style='background:#ffa421; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{t['advice_disc']}: -{int(rec_disc)} €</div>", unsafe_allow_html=True)
            else: st.markdown(f"<div style='background:#065f46; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>{t['advice_ok']}</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        def get_margin(regime, pvp, cost, vat):
            if regime == "REBU":
                if vat == 0: return pvp - cost 
                return (pvp - cost) / 1.21 
            elif regime == "PRO":
                if vat == 0: return pvp - (cost / 1.21) 
                if vat == 0.21: return (pvp / 1.21) - (cost / 1.21)
                return (pvp / (1 + vat)) - (cost / 1.21)
            elif regime == "INTRA":
                if vat == 0: return pvp - cost 
                return (pvp / (1 + vat)) - cost 
            return 0
            
        final_margin = get_margin(active_regime, final_P, cost_val, vat_rate)
        
        if active_regime:
            val_txt = f"{final_margin:,.0f} €" if cost_val > 0 else " - "
            st.markdown(f"""<div style="background:{C_SOFT}; border: 3px solid {C_SEC}; transform:scale(1.02); box-shadow:0 10px 20px rgba(0,0,0,0.1); padding:20px; border-radius:15px; text-align:center; margin: 0 auto; width: 100%; margin-bottom:15px;"><div style="font-weight:bold; color:#555; font-size:18px;">{active_regime} -> {sel_country}</div><div style="font-size:42px; font-weight:900; color:{C_MAIN}">{val_txt}</div></div>""", unsafe_allow_html=True)
            
            expl = ""
            if active_regime == "REBU":
                if vat_rate > 0: expl = f"<b>Cálculo (REBU B2C):</b> (({final_P:.0f} - {cost_val:.0f}) / 1.21) = {final_margin:,.0f}"
                else: expl = f"<b>Cálculo (REBU Export):</b> {final_P:.0f} - {cost_val:.0f} = {final_margin:,.0f}"
            elif active_regime == "PRO":
                if vat_rate == 0: expl = f"<b>Cálculo (PRO Export):</b> {final_P:.0f} - ({cost_val:.0f}/1.21) = {final_margin:,.0f}"
                else: expl = f"<b>Cálculo (PRO B2C):</b> ({final_P:.0f} / {1+vat_rate:.2f}) - ({cost_val:.0f} / 1.21) = {final_margin:,.0f}"
            elif active_regime == "INTRA":
                if vat_rate == 0: expl = f"<b>Cálculo (INTRA Export):</b> {final_P:.0f} - {cost_val:.0f} = {final_margin:,.0f}"
                else: expl = f"<b>Cálculo (INTRA B2C):</b> ({final_P:.0f} / {1+vat_rate:.2f}) - {cost_val:.0f} = {final_margin:,.0f}"
            st.markdown(f"""<div style="background:#e3f2fd; padding:10px; border-radius:5px; font-size:13px; color:#0d47a1; text-align:center;">{expl}</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
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
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            
            bg_age = "#e5e7eb" 
            age_txt = "-"
            if days_stock > 0:
                age_txt = f"{days_stock} {t['unit_days']}"
                bg_age = "#d1fae5" 
                if days_stock > 45: bg_age = "#ffedd5" 
                if days_stock > 90: bg_age = "#fee2e2" 
            
            color_age = "#065f46" if days_stock <= 90 else "#991b1b"
            if days_stock == 0: color_age = "#374151"

            st.markdown(f"""<div style="background-color:{bg_age}; padding:15px; border-radius:10px; color:{color_age}; text-align:center; border:1px solid {color_age}; margin-bottom:15px;">
                <div style="font-size:14px; text-transform:uppercase; font-weight:bold;">{t['age']}</div>
                <div style="font-size:32px; font-weight:800;">{age_txt}</div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown(f'<img src="{f_img}" class="product-img">', unsafe_allow_html=True)
            
            border_col = C_ALERT if is_sold else C_SEC
            bg_col = "#fee2e2" if is_sold else "#d1fae5"
            sold_txt = f"<br><b>🔴 VENDIDO ({last_update})</b>" if is_sold else ""
            
            st.markdown(f"""
            <div style="background-color:{bg_col}; padding:15px; border-radius:10px; color:#0a4650; margin-top:15px; border:2px solid {border_col};">
                <h3 style="margin:0; padding-bottom:10px;">✅ {f_title} {sold_txt}</h3>
                <ul style="margin:0; padding-left:20px; line-height:1.6;">
                    <li><b>Estado:</b> {specs.get('state','-')}</li>
                    <li><b>Año:</b> {specs.get('year','-')}</li>
                    <li><b>Talla:</b> {specs.get('size','-')}</li>
                    <li><b>Cuadro:</b> {specs.get('frame','-')}</li>
                    <li><b>Ruedas:</b> {specs.get('wheels','-')}</li>
                    <li><b>Transmisión:</b> {specs.get('group','-')}</li>
                    <li><b>Frenos:</b> {specs.get('brakes','-')}</li>
                </ul>
            </div>""", unsafe_allow_html=True)

elif page == t["nav_price"]:
    st.header(f"📉 {t['pricing_title']}")
    with st.spinner("Analizando inventario..."):
        df_stock = get_current_stock_and_pricing()
    
    if not df_stock.empty:
        df_stock["disc"] = df_stock.apply(lambda x: calculate_smart_discount(x["days"], x["margin_curr"], x["price_curr"]), axis=1)
        df_stock["rec"] = df_stock["price_curr"] - df_stock["disc"]
        df_stock["m_proj"] = df_stock.apply(lambda x: (((x["rec"]-x["cost"])/1.21)) if "REBU" in str(x["fiscal"]) else (((x["rec"]/1.21)-(x["cost"]/1.21))), axis=1)
        
        # TRADUCTION & COLONNE DATE MODIF
        cfg = {
            "img": st.column_config.ImageColumn(t["col_img"]),
            "sku": st.column_config.TextColumn("SKU"),
            "days": st.column_config.NumberColumn("Días Stock", format="%d"),
            "price_curr": st.column_config.NumberColumn(t["col_p_curr"], format="%d€"),
            "rec": st.column_config.NumberColumn(t["col_p_rec"], format="%d€"),
            "disc": st.column_config.NumberColumn(t["col_action"], format="-%d€"),
            "m_proj": st.column_config.NumberColumn(t["col_margin_proj"], format="%d€"),
            "updated_at": st.column_config.DateColumn("Últ. Modif.", format="DD/MM/YYYY") # AJOUT CLIENT
        }
        
        # FILTRES LOGIQUES
        df_crit = df_stock[df_stock["days"] > 360]
        df_urg = df_stock[(df_stock["days"] > 180) & (df_stock["days"] <= 360)]
        df_warn = df_stock[(df_stock["days"] > 90) & (df_stock["days"] <= 180)]
        df_watch = df_stock[(df_stock["days"] > 45) & (df_stock["days"] <= 90)]

        # AFFICHAGE
        with st.expander(f"🔴 CRITICO (> 360 días) - {len(df_crit)} bicis", expanded=True): 
            if not df_crit.empty: st.data_editor(df_crit, column_config=cfg, use_container_width=True, hide_index=True, key="crit")
            else: st.info("0 bicis.")

        with st.expander(f"🟠 URGENTE (180-360 días) - {len(df_urg)} bicis", expanded=True): 
            if not df_urg.empty: st.data_editor(df_urg, column_config=cfg, use_container_width=True, hide_index=True, key="urg")
            else: st.info("0 bicis.")

        with st.expander(f"🟡 ATENCION (90-180 días) - {len(df_warn)} bicis", expanded=False): 
            if not df_warn.empty: st.data_editor(df_warn, column_config=cfg, use_container_width=True, hide_index=True, key="warn")
            else: st.info("0 bicis.")

        with st.expander(f"🟢 MONITORIZAR (45-90 días) - {len(df_watch)} bicis", expanded=False): 
            if not df_watch.empty: st.data_editor(df_watch, column_config=cfg, use_container_width=True, hide_index=True, key="watch")
            else: st.info("0 bicis.")

    else: st.info("No data.")
