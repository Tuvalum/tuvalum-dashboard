import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import os
import re

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="Tuvalum Dashboard", layout="wide", page_icon="🚲")

# COULEURS
C_MAIN = "#0a4650"   # Vert Foncé
C_SEC = "#08e394"    # Vert Flashy (Focus & Highlights)
C_TER = "#dcff54"    # Vert Clair
C_SOFT = "#e0fdf4"   # Vert Doux (Backgrounds)
C_BG = "#f2f7f8"     # Fond

COST_RECOND = 54.5

# TAUX DE CHANGE SECOURS
RATES_FALLBACK = {"EUR": 1.0, "HUF": 0.0025, "PLN": 0.23, "GBP": 1.16, "USD": 0.92, "DKK": 0.13, "SEK": 0.09, "CZK": 0.04}

# ==============================================================================
# 2. LOGIN
# ==============================================================================
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    st.markdown(f"""<style>.stApp {{background-image: url("https://images.unsplash.com/photo-1485965120184-e220f721d03e?q=80&w=1600&auto=format&fit=crop"); background-size: cover;}} [data-testid="stSidebar"],header {{display:none;}} [data-testid="stForm"] {{background:white; padding:40px; border-radius:15px; box-shadow:0 15px 50px rgba(0,0,0,0.5);}} button {{background:{C_SEC}!important; color:{C_MAIN}!important;}}</style>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([3, 2, 3])
    with c2:
        st.markdown("<br><br><br><h1>T</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.text_input("User", value="Tuvalum", disabled=True)
            password = st.text_input("Pass", type="password")
            if st.form_submit_button("LOG IN", type="secondary", use_container_width=True):
                if password == st.secrets["security"]["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else: st.error("Error")
    return False

if not check_password(): st.stop()

# ==============================================================================
# STYLE & DESIGN (VERT FLASHY EVERYWHERE)
# ==============================================================================
st.markdown(f"""<style>
    .stApp {{background-color: {C_BG};}} 
    
    /* Boutons */
    .stButton button {{background-color: {C_MAIN} !important; color:white !important; border-radius: 8px; border:none;}}
    
    /* KPI Cards */
    .kpi-card {{background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #e1e8e8; margin-bottom: 20px;}}
    .kpi-card-soft {{background-color: {C_SOFT}; padding: 20px; border-radius: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); border: 1px solid #d1fae5; margin-bottom: 20px; opacity: 0.95;}}
    .kpi-title {{font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase;}} 
    .kpi-value {{font-size: 32px; color: {C_MAIN}; font-weight: 800; margin: 8px 0;}} 
    .kpi-sub {{font-size: 13px; color: #94a3b8; display:flex; justify-content:space-between;}} 
    
    /* SUPPRESSION DU ROUGE STREAMLIT PAR DEFAUT (REMPLACÉ PAR VERT FLASHY) */
    input:focus, textarea:focus, select:focus {{border-color: {C_SEC} !important; box-shadow: 0 0 0 1px {C_SEC} !important;}}
    div[data-baseweb="select"] > div:first-child {{border-color: {C_SEC} !important;}}
    
    /* Radio Buttons */
    div[role="radiogroup"] > label > div:first-of-type {{background-color: {C_BG} !important; border-color: {C_SEC} !important;}}
    div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {{background-color: {C_SEC} !important;}}
    
    /* Calendrier - Date Selectionnée */
    span[data-baseweb="tag"] {{background-color: {C_SEC} !important;}}
    
    /* Date du jour (Cercle Vert) */
    div[role="grid"] div[aria-selected="true"] {{background-color: {C_SEC} !important; color: white !important;}}
    
    #MainMenu {{visibility: visible;}} footer {{visibility: hidden;}}
</style>""", unsafe_allow_html=True)

TRADUCTIONS = {
    "Español": {
        "lang_code": "ES", "nav_title": "Navegación", "page_1": "Dashboard", "page_1b": "Tabla Ventas", "page_3": "Stock", "page_4": "Calculadora", "btn_refresh": "Actualizar Datos",
        "t_kpi1": "Ventas Hoy (Pagadas)", "t_kpi2": "Ventas Hoy (Pendientes)", "t_kpi3": "Ventas Selecc. (Pagadas)", "t_kpi4": "Ventas Selecc. (Pendientes)",
        "sub_rev": "Ingresos", "sub_mar": "Margen", "chart_channel": "Canales", "chart_mp": "Marketplaces", 
        "kpi_to_ship": "Por Enviar", "table_shipping": "Lista Pedidos (Shopify)", 
        "chart_cat": "Categoría", "chart_subcat": "Sub-Categoría", "chart_brand": "Top 5 Marcas", "chart_price": "Rango de Precios", "chart_country": "Países",
        "avg_price": "Precio Medio", "avg_margin": "Margen Medio", "avg_margin_pct": "% Margen", "avg_rot": "Rotación Media (días)", 
        "loading": "Cargando datos (Max velocidad)...", "sidebar_date": "Periodo",
        "opt_today": "Hoy", "opt_month": "Este Mes", "opt_year": "Este Año", "opt_custom": "Personalizado",
        "calc_title": "Calculadora", "calc_info": "Búsqueda LIVE por SKU.", "sku_ph": "ej: B2837", "sku_found": "SKU Encontrado", "regime": "Régimen Fiscal", "age": "Antigüedad", 
        "price_input": "Precio Venta (€)", "cost_input": "Coste Compra (€)", "discount_input": "Descuento (€)",
        "sim_title": "Simulación Margen", "advice_new": "🔴 Novedad (< 1 mes): Sin descuento.", "advice_stock": "🟠 Stock (1-3 meses): Descuento máx 150€.", "advice_liq": "🟢 Liquidación (> 3 meses): Descuento posible.", "unit_days": "días",
        "col_sku": "SKU", "col_order": "Pedido", "col_country": "País", "col_channel": "Canal", "col_price": "PVP (€)", "col_cost": "Coste (€)", "col_margin": "Margen (€)", "col_rot": "Rot. (Días)", "col_prod": "Producto", "col_date": "Fecha", "col_cat": "Cat.", "col_subcat": "Sub-Cat.", "col_fiscal": "Régimen"
    },
    "Français": {
        "lang_code": "FR", "nav_title": "Navigation", "page_1": "Dashboard", "page_1b": "Tableau Ventes", "page_3": "Stock", "page_4": "Calculatrice", "btn_refresh": "Actualiser Données",
        "t_kpi1": "Ventes Jour (Payées)", "t_kpi2": "Ventes Jour (Attente)", "t_kpi3": "Ventes Sélecc. (Payées)", "t_kpi4": "Ventes Sélecc. (Attente)",
        "sub_rev": "CA", "sub_mar": "Marge", "chart_channel": "Canaux", "chart_mp": "Marketplaces", 
        "kpi_to_ship": "À Expédier", "table_shipping": "Liste Commandes", 
        "chart_cat": "Catégorie", "chart_subcat": "Sous-Catégorie", "chart_brand": "Top 5 Marques", "chart_price": "Gamme de Prix", "chart_country": "Pays",
        "avg_price": "Prix Moyen", "avg_margin": "Marge Moyenne", "avg_margin_pct": "% Marge", "avg_rot": "Rotation Moyenne (jours)", 
        "loading": "Chargement (Vitesse max)...", "sidebar_date": "Période",
        "opt_today": "Auj.", "opt_month": "Ce Mois", "opt_year": "Cette Année", "opt_custom": "Personnalisé",
        "calc_title": "Calculatrice", "calc_info": "Recherche LIVE par SKU.", "sku_ph": "ex: B2837", "sku_found": "SKU Trouvé", "regime": "Régime Fiscal", "age": "Ancienneté", 
        "price_input": "Prix Vente (€)", "cost_input": "Coût Achat (€)", "discount_input": "Remise (€)",
        "sim_title": "Simulation Marge", "advice_new": "🔴 Nouveauté (< 1 mois) : Pas de remise.", "advice_stock": "🟠 Stock (1-3 mois) : Remise Max 150€.", "advice_liq": "🟢 Déstockage (> 3 mois) : Remise possible.", "unit_days": "jours",
        "col_sku": "SKU", "col_order": "Cmd", "col_country": "Pays", "col_channel": "Canal", "col_price": "Prix (€)", "col_cost": "Coût (€)", "col_margin": "Marge (€)", "col_rot": "Rot. (Jours)", "col_prod": "Produit", "col_date": "Date", "col_cat": "Cat.", "col_subcat": "Sous-Cat.", "col_fiscal": "Régime"
    },
    "English": {
        "lang_code": "EN", "nav_title": "Navigation", "page_1": "Dashboard", "page_1b": "Sales Table", "page_3": "Stock", "page_4": "Calculator", "btn_refresh": "Update Data",
        "t_kpi1": "Sales Today (Paid)", "t_kpi2": "Sales Today (Pending)", "t_kpi3": "Sales Select. (Paid)", "t_kpi4": "Sales Select. (Pending)",
        "sub_rev": "Rev.", "sub_mar": "Margin", "chart_channel": "Channels", "chart_mp": "Marketplaces", 
        "kpi_to_ship": "To Ship", "table_shipping": "Order List", 
        "chart_cat": "Category", "chart_subcat": "Sub-Category", "chart_brand": "Top 5 Brands", "chart_price": "Price Range", "chart_country": "Countries",
        "avg_price": "Avg Price", "avg_margin": "Avg Margin", "avg_margin_pct": "Margin %", "avg_rot": "Avg Rotation (days)", 
        "loading": "Loading (Max speed)...", "sidebar_date": "Period",
        "opt_today": "Today", "opt_month": "This Month", "opt_year": "This Year", "opt_custom": "Custom",
        "calc_title": "Calculator", "calc_info": "LIVE SKU Search.", "sku_ph": "ex: B2837", "sku_found": "SKU Found", "regime": "Fiscal Regime", "age": "Age", 
        "price_input": "Sale Price Tax Inc (€)", "cost_input": "Purchase Cost (€)", "discount_input": "Discount (€)",
        "sim_title": "Margin Sim", "advice_new": "🔴 New (< 1 month): No discount.", "advice_stock": "🟠 Stock (1-3 months): Max discount 150€.", "advice_liq": "🟢 Clearance (> 3 months): Discount possible.", "unit_days": "days",
        "col_sku": "SKU", "col_order": "Order", "col_country": "Country", "col_channel": "Channel", "col_price": "Price (€)", "col_cost": "Cost (€)", "col_margin": "Margin (€)", "col_rot": "Rot. (Days)", "col_prod": "Product", "col_date": "Date", "col_cat": "Cat.", "col_subcat": "Sub-Cat.", "col_fiscal": "Regime"
    }
}

# --- MOTEUR DONNÉES (OPTIMISÉ) ---
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
                title vendor createdAt productType
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
                        
                        subcat_val = n["category"]["value"] if (n["category"] and n["category"]["value"]) else "Autre"
                        prod_type = n["productType"] if n["productType"] else "Autre"
                        
                        cat_val = prod_type
                        if subcat_val in ["Carretera", "Gravel", "Triathlon", "Gran Fondo"]: cat_val = "Road"
                        elif subcat_val in ["MTB", "Rigidas", "Dobles", "Enduro"]: cat_val = "MTB"
                        elif subcat_val in ["Urbana", "Plegable"]: cat_val = "City"
                        elif subcat_val in ["E-Bike", "Electrica"]: cat_val = "E-Bike"
                        
                        created_at = pd.to_datetime(n["createdAt"]).tz_convert(None)
                        DATA_MAP[pid] = {"cost": cost_val, "fiscal": fiscal_val, "brand": brand_val, "cat": cat_val, "subcat": subcat_val, "created_at": created_at}
                    else: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "cat": "Autre", "subcat": "Autre", "created_at": None}
        except:
            for pid in chunk: DATA_MAP[pid] = {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "cat": "Autre", "subcat": "Autre", "created_at": None}
    return DATA_MAP

@st.cache_data(ttl=600)
def get_data_v64(start_date_limit):
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
        last_order_date = pd.to_datetime(od[-1]["created_at"]).tz_convert(None)
        orders.extend(od)
        if last_order_date < limit_dt: break
        if 'next' in r.links: url_o = r.links['next']['url']
        else: break
    
    clean_o = []; product_ids_to_fetch = []
    MPs=["decathlon","alltricks","bikeroom","campsider","buycycle","bikeflip","ebikemood","cycletyre"]
    
    for o in orders:
        cancelled_at = o.get("cancelled_at")
        fin_status = o.get("financial_status")
        is_cancelled = cancelled_at is not None
        
        t = (o.get("tags","") or "").lower()
        c = "Online"; mp = "Autre"
        if "tienda tuvalum" in t or "venta asistida" in t: c="Tienda"; mp="-"
        elif "marketplace" in t:
            c="Marketplace"
            mp = next((m.capitalize() for m in MPs if m in t),"Autre MP")
        else: c="Online"; mp="-"
        
        country = "Autre"
        if o.get("shipping_address"): country = o["shipping_address"].get("country_code", "Autre")
        elif o.get("billing_address"): country = o["billing_address"].get("country_code", "Autre")
        
        raw_price = float(o["total_price"]); currency_code = o.get("currency", "EUR"); total_eur = 0.0
        try:
            if o.get("total_price_set") and o["total_price_set"].get("shop_money") and o["total_price_set"]["shop_money"]["currency_code"] == "EUR":
                total_eur = float(o["total_price_set"]["shop_money"]["amount"])
            else:
                rate = RATES_FALLBACK.get(currency_code, 1.0)
                total_eur = raw_price * rate
        except: total_eur = raw_price
        
        if total_eur < 200.0: continue 
        
        parent_id = None; sku = ""
        if o.get("line_items"):
            line = o["line_items"][0]
            parent_id = str(line.get("product_id") or "")
            sku = line.get("sku", "")
            if parent_id: product_ids_to_fetch.append(parent_id)
            
        clean_o.append({
            "date":pd.to_datetime(o["created_at"]).tz_convert(None),
            "total_ttc": total_eur, "status": fin_status, "is_cancelled": is_cancelled,
            "fulfillment":o.get("fulfillment_status") or "unfulfilled",
            "channel":c, "mp_name":mp, "order_name":o["name"], "parent_id": parent_id,
            "country": country, "sku": sku, "order_id": str(o["id"])
        })
    
    df_ord = pd.DataFrame(clean_o)
    
    if not df_ord.empty and product_ids_to_fetch:
        COST_MAP = fetch_product_details_batch(product_ids_to_fetch)
        def apply_data(row):
            pid = row["parent_id"]; price = row["total_ttc"]; sale_date = row["date"]
            data = COST_MAP.get(pid, {"cost": 0.0, "fiscal": "PRO", "brand": "Autre", "cat": "Autre", "subcat": "Autre", "created_at": None})
            cost = data["cost"]; fiscal = str(data["fiscal"]).upper(); margin = 0.0
            
            if cost > 0:
                if "REBU" in fiscal: margin = ((price - cost) / 1.21) - COST_RECOND
                elif "INTRA" in fiscal: margin = (price - cost) - COST_RECOND
                else: margin = ((price / 1.21) - (cost / 1.21)) - COST_RECOND
            
            rotation = 0
            if pd.notnull(data["created_at"]) and pd.notnull(sale_date):
                rotation = (sale_date - data["created_at"]).days
                if rotation < 0: rotation = 0
                
            return pd.Series([cost, fiscal, margin, data["brand"], data["cat"], data["subcat"], rotation])
            
        df_ord[["cost", "fiscal", "margin_real", "brand", "cat", "subcat", "rotation"]] = df_ord.apply(apply_data, axis=1)
        return df_ord
    return pd.DataFrame()

def search_sku_live(sku):
    shop_url = st.secrets["shopify"]["shop_url"]; token = st.secrets["shopify"]["access_token"]
    q = f"""{{ products(first: 1, query: "sku:{sku}") {{ edges {{ node {{ title createdAt metafield(namespace: "custom", key: "custitem_preciocompra") {{ value }} fiscal: metafield(namespace: "custom", key: "cseg_origenfiscal") {{ value }} price_meta: metafield(namespace: "custom", key: "custitem_precioventapvp") {{ value }} variants(first: 1) {{ edges {{ node {{ price }} }} }} }} }} }} }}"""
    try:
        r = requests.post(f"https://{shop_url}/admin/api/2024-01/graphql.json", json={"query":q}, headers={"X-Shopify-Access-Token": token})
        d = r.json().get("data",{}).get("products",{}).get("edges",[])
        if d:
            n = d[0]["node"]
            raw_cost = n["metafield"]["value"] if n["metafield"] else "0"
            cost_val = float(re.sub(r'[^\d.]', '', str(raw_cost).replace(',','.'))) if raw_cost else 0.0
            price = 0.0
            if n["price_meta"]: price = float(n["price_meta"]["value"])
            elif n["variants"]["edges"]: price = float(n["variants"]["edges"][0]["node"]["price"])
            return {"found": True, "title": n["title"], "cost": cost_val, "price": price, "created_at": pd.to_datetime(n["createdAt"]).tz_convert(None), "fiscal": n["fiscal"]["value"] if n["fiscal"] else "PRO"}
    except: pass
    return {"found": False}

# --- INTERFACE ---
if os.path.exists("images/logo rond.png"): 
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    c_logo, _ = st.sidebar.columns([1, 0.5])
    with c_logo: st.image("images/logo rond.png", width=120)

st.sidebar.markdown("---")

# MENU
page = st.sidebar.radio("Nav", ["Dashboard", "Tabla Ventas", "Calculadora"], label_visibility="collapsed")

st.sidebar.markdown("---")

# CONFIG DATES
T = TRADUCTIONS["Español"]
now = datetime.now(); today_dt = now.date(); jan1 = today_dt.replace(month=1, day=1)

if 'start_date_state' not in st.session_state: st.session_state.start_date_state = jan1
if 'end_date_state' not in st.session_state: st.session_state.end_date_state = today_dt

st.sidebar.write(f"**📅 {T['sidebar_date']}**")

# RADIO BUTTONS DATES
mode_options = [T['opt_today'], T['opt_month'], T['opt_year'], T['opt_custom']]
date_mode = st.sidebar.radio("", mode_options, index=2, label_visibility="collapsed")

if date_mode == T['opt_today']:
    st.session_state.start_date_state = today_dt; st.session_state.end_date_state = today_dt
elif date_mode == T['opt_month']:
    st.session_state.start_date_state = today_dt.replace(day=1); st.session_state.end_date_state = today_dt
elif date_mode == T['opt_year']:
    st.session_state.start_date_state = jan1; st.session_state.end_date_state = today_dt
else:
    with st.sidebar.form("custom_date"):
        d_input = st.date_input(T['opt_custom'], value=(st.session_state.start_date_state, st.session_state.end_date_state))
        submit_date = st.form_submit_button(T["btn_refresh"])
        if submit_date and isinstance(d_input, (list, tuple)) and len(d_input) > 0:
            st.session_state.start_date_state = d_input[0]
            st.session_state.end_date_state = d_input[1] if len(d_input) > 1 else d_input[0]

start_date = pd.to_datetime(st.session_state.start_date_state)
end_date = pd.to_datetime(st.session_state.end_date_state).replace(hour=23, minute=59, second=59)

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
with st.sidebar.expander("🌍 Idioma"):
    lang_choice = st.radio("", ["Español", "Français", "English"], index=0)
    T = TRADUCTIONS.get(lang_choice, TRADUCTIONS["Español"])
    lang_code = T["lang_code"]

with st.spinner(T["loading"]): df_merged = get_data_v64(start_date)

today_start = pd.to_datetime(today_dt); today_end = today_start + timedelta(days=1) - timedelta(seconds=1)
df_today = df_merged[(df_merged["date"] >= today_start) & (df_merged["date"] <= today_end)] if not df_merged.empty else pd.DataFrame()
df_period = df_merged[(df_merged["date"] >= start_date) & (df_merged["date"] <= end_date)] if not df_merged.empty else pd.DataFrame()

if lang_code == "ES" and not df_merged.empty:
    if not df_today.empty: df_today["channel"] = df_today["channel"].replace("Boutique", "Tienda")
    if not df_period.empty: df_period["channel"] = df_period["channel"].replace("Boutique", "Tienda")

def card_kpi(col, title, count_val, rev_val, marg_val, color, is_soft=False, show_margin=True):
    css_class = "kpi-card-soft" if is_soft else "kpi-card"
    margin_html = f'<span style="color:#0a4650;">{T["sub_mar"]}: <b>{marg_val}</b></span>' if show_margin else ""
    col.markdown(f"""<div class="{css_class}" style="border-left: 5px solid {color};"><div class="kpi-title">{title}</div><div class="kpi-value">{count_val}</div><div class="kpi-sub"><span style="color:#666;">{T['sub_rev']}: <b>{rev_val}</b></span>{margin_html}</div></div>""", unsafe_allow_html=True)

def plot_bar_smart(df, x_col, y_col, color_col=None, colors=None, fixed_order=None):
    if df.empty:
        fig = go.Figure()
        fig.update_layout(xaxis={"visible": False}, yaxis={"visible": False}, annotations=[dict(text="No Data", xref="paper", yref="paper", showarrow=False, font=dict(size=16, color="gray"))], height=400)
        return fig
    
    if fixed_order:
        all_cats = pd.DataFrame({x_col: fixed_order})
        df = pd.merge(all_cats, df, on=x_col, how="left").fillna(0)
    
    total = df[y_col].sum()
    if total == 0: total = 1
    
    df["pct"] = (df[y_col] / total * 100).round(1)
    df["text_inside"] = df.apply(lambda x: f"<b>{x['pct']}%</b>" if x[y_col] > 0 else "", axis=1)
    
    fig = go.Figure()
    if color_col:
        fig = px.bar(df, x=x_col, y=y_col, color=color_col, color_discrete_map=colors, text="text_inside")
    else:
        fig.add_trace(go.Bar(x=df[x_col], y=df[y_col], text=df["text_inside"], textposition='inside', marker_color=C_MAIN, textfont=dict(size=14, color='white')))
    
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', margin=dict(t=40,b=20,l=0,r=0), height=400, xaxis_title=None, yaxis_title=None)
    
    max_y = df[y_col].max() * 1.15
    fig.update_yaxes(range=[0, max_y])
    
    for i, row in df.iterrows():
        if row[y_col] > 0 or fixed_order:
            txt = f"<b>{int(row[y_col])}</b>"
            fig.add_annotation(x=row[x_col], y=row[y_col], text=txt, yshift=15, showarrow=False, font=dict(size=16, color="black"))
            
    return fig

# PAGE 1 : DASHBOARD
if page == "Dashboard" and not df_merged.empty:
    t_range = f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"
    ch1, ch2 = st.columns(2)
    ch1.markdown(f"### 📅 Hoy ({today_dt.strftime('%d/%m')})")
    ch2.markdown(f"### 📅 {t_range}")

    # LOGIQUE "PAID" INCLUT PARTIALLY REFUNDED
    PAID_STATUSES = ["paid", "partially_refunded"]
    
    df_d_ok = df_today[df_today["status"].isin(PAID_STATUSES)]
    df_d_ko = df_today[(df_today["status"].isin(["pending","partially_paid"])) & (df_today["is_cancelled"]==False)]
    df_p_ok = df_period[df_period["status"].isin(PAID_STATUSES)]
    df_p_ko = df_period[(df_period["status"].isin(["pending","partially_paid"])) & (df_period["is_cancelled"]==False)]

    c1,c2,c3,c4 = st.columns(4)
    card_kpi(c1, T["t_kpi1"], len(df_d_ok), f"{df_d_ok['total_ttc'].sum():,.0f}€", f"{df_d_ok['margin_real'].sum():,.0f}€", C_MAIN)
    card_kpi(c2, T["t_kpi2"], len(df_d_ko), f"{df_d_ko['total_ttc'].sum():,.0f}€", f"{df_d_ko['margin_real'].sum():,.0f}€", C_SEC)
    card_kpi(c3, T["t_kpi3"], len(df_p_ok), f"{df_p_ok['total_ttc'].sum():,.0f}€", f"{df_p_ok['margin_real'].sum():,.0f}€", C_MAIN)
    card_kpi(c4, T["t_kpi4"], len(df_p_ko), f"{df_p_ko['total_ttc'].sum():,.0f}€", f"{df_p_ko['margin_real'].sum():,.0f}€", C_SEC)

    c_new1, c_new2, c_new3, c_new4 = st.columns(4)
    avg_price = df_p_ok['total_ttc'].mean() if not df_p_ok.empty else 0
    avg_margin = df_p_ok['margin_real'].mean() if not df_p_ok.empty else 0
    total_rev = df_p_ok['total_ttc'].sum(); total_marg = df_p_ok['margin_real'].sum()
    avg_marg_pct = (total_marg / total_rev * 100) if total_rev > 0 else 0
    avg_rot = df_p_ok['rotation'].mean() if not df_p_ok.empty else 0
    
    with c_new1: card_kpi(st, T["avg_price"], f"{avg_price:,.0f}€", "", "", C_SEC, is_soft=True, show_margin=False)
    with c_new2: card_kpi(st, T["avg_margin"], f"{avg_margin:,.0f}€", "", "", C_SEC, is_soft=True, show_margin=False)
    with c_new3: card_kpi(st, T["avg_margin_pct"], f"{avg_marg_pct:,.1f}%", "", "", C_SEC, is_soft=True, show_margin=False)
    with c_new4: card_kpi(st, T["avg_rot"], f"{avg_rot:,.0f}", "", "", C_SEC, is_soft=True, show_margin=False)

    g1, g2 = st.columns(2)
    with g1:
        st.subheader(T["chart_channel"])
        df_ch = df_period[df_period["status"].isin(PAID_STATUSES)].groupby("channel").size().reset_index(name="c").sort_values("c", ascending=False)
        fixed_ch = ["Online", "Marketplace", "Tienda"]
        st.plotly_chart(plot_bar_smart(df_ch, "channel", "c", "channel", {"Online":C_SEC,"Marketplace":C_MAIN,"Tienda":C_TER}, fixed_order=fixed_ch), use_container_width=True)
    with g2:
        st.subheader(T["chart_mp"])
        df_mp = df_period[df_period["status"].isin(PAID_STATUSES) & (df_period["channel"]=="Marketplace")].groupby("mp_name").size().reset_index(name="c").sort_values("c", ascending=False)
        fixed_mp = ["Decathlon", "Alltricks", "Campsider", "Bikeroom", "Autre MP"]
        st.plotly_chart(plot_bar_smart(df_mp, "mp_name", "c", fixed_order=fixed_mp), use_container_width=True)

    c_new3, c_new4 = st.columns(2)
    with c_new3:
        st.subheader(T["chart_cat"])
        df_cat = df_p_ok.groupby("cat").size().reset_index(name="c").sort_values("c", ascending=False)
        st.plotly_chart(plot_bar_smart(df_cat, "cat", "c"), use_container_width=True)
    with c_new4:
        st.subheader(T["chart_brand"])
        df_brand = df_p_ok.groupby("brand").size().reset_index(name="c").sort_values("c", ascending=False).head(5)
        st.plotly_chart(plot_bar_smart(df_brand, "brand", "c"), use_container_width=True)

    c_g5_1, c_g5_2 = st.columns(2)
    with c_g5_1:
        st.subheader(T["chart_country"])
        df_ctry = df_p_ok.groupby("country").size().reset_index(name="c")
        if not df_ctry.empty:
            fig_pie = px.pie(df_ctry, values='c', names='country', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
            fig_pie.update_traces(textinfo='label+percent', textfont_size=13)
            st.plotly_chart(fig_pie, use_container_width=True)
    with c_g5_2:
        st.subheader(T["chart_price"])
        bins = [0, 1000, 1500, 2500, 4000, 100000]; labels = ["<1k", "1k-1.5k", "1.5k-2.5k", "2.5k-4k", ">4k"]
        df_p_ok['price_range'] = pd.cut(df_p_ok['total_ttc'], bins=bins, labels=labels)
        df_pr = df_p_ok.groupby("price_range").size().reset_index(name="c")
        st.plotly_chart(plot_bar_smart(df_pr, "price_range", "c", fixed_order=labels), use_container_width=True)

# PAGE 1B : TABLA VENTAS
elif page == "Tabla Ventas" and not df_merged.empty:
    st.header(f"📋 {T['page_1b']}")
    PAID_STATUSES = ["paid", "partially_refunded"]
    df_detail = df_period[df_period["status"].isin(PAID_STATUSES)].copy()
    df_detail["canal_display"] = df_detail.apply(lambda x: f"{x['channel']} ({x['mp_name']})" if x['channel']=="Marketplace" else x['channel'], axis=1)
    cols_show = ["sku", "order_name", "country", "canal_display", "total_ttc", "cost", "margin_real", "rotation", "date", "subcat", "fiscal"]
    df_show = df_detail[cols_show].sort_values("date", ascending=False)
    df_show.columns = [T["col_sku"], T["col_order"], T["col_country"], T["col_channel"], T["col_price"], T["col_cost"], T["col_margin"], T["col_rot"], T["col_date"], T["col_subcat"], T["col_fiscal"]]
    st.dataframe(df_show, use_container_width=True, hide_index=True)
    csv = df_show.to_csv(index=False).encode('utf-8')
    st.download_button("📥 CSV", data=csv, file_name="ventas_tuvalum.csv", mime="text/csv")

# PAGE 4 : CALCULADORA
elif page == "Calculadora":
    st.header(f"🧮 {T['page_4']}")
    st.info(T["calc_info"])
    col_input, col_res = st.columns([1, 2])
    with col_input:
        sku_input = st.text_input("SKU", placeholder=T["sku_ph"])
        found_cost=0.0; found_price=0.0; found_fiscal="PRO"
        if sku_input:
            res = search_sku_live(sku_input.strip())
            if res["found"]:
                found_cost=res["cost"]; found_price=res["price"]; found_fiscal=res["fiscal"]
                creation_date = res["created_at"]
                if pd.notnull(creation_date):
                    delta = datetime.now() - creation_date
                    days = delta.days
                    if days < 30: discount_advice=T["advice_new"]; color_advice="#ff4b4b"
                    elif 30 <= days <= 90: discount_advice=T["advice_stock"]; color_advice="#ffa421"
                    else: discount_advice=T["advice_liq"]; color_advice="#09ab3b"
                st.success(f"✅ {T['sku_found']} : {res['title']}")
                st.info(f"{T['regime']} : **{found_fiscal}**")
                st.markdown(f"**{T['age']} : {days} {T['unit_days']}**")
                st.markdown(f"<div style='background-color:{color_advice}; color:white; padding:10px; border-radius:5px;'>{discount_advice}</div>", unsafe_allow_html=True)
            else: st.warning(T["sku_not_found"])
        
        price_val = st.number_input(T["price_input"], min_value=0.0, value=float(found_price) if found_price else 2000.0, step=10.0)
        cost_val = st.number_input(T["cost_input"], min_value=0.0, value=float(found_cost) if found_cost else 0.0, step=10.0)
        discount_val = st.number_input(T["discount_input"], min_value=0.0, value=0.0, step=10.0)
        
        final_price = max(0.0, price_val - discount_val)

    with col_res:
        st.subheader(T["sim_title"])
        m_rebu = (final_price - cost_val) / 1.21 if final_price > cost_val else 0
        m_pro = (final_price / 1.21) - (cost_val / 1.21)
        m_intra = final_price - cost_val
        
        c1, c2, c3 = st.columns(3)
        f_fiscal = str(found_fiscal).upper()
        s_rebu = f"background-color:{C_SOFT}; transform:scale(1.05); border:none;" if "REBU" in f_fiscal else "background-color:white; border:1px solid #eee; opacity:0.7;"
        s_pro = f"background-color:{C_SOFT}; transform:scale(1.05); border:none;" if "PRO" in f_fiscal or "GENERAL" in f_fiscal else "background-color:white; border:1px solid #eee; opacity:0.7;"
        s_intra = f"background-color:{C_SOFT}; transform:scale(1.05); border:none;" if "INTRA" in f_fiscal else "background-color:white; border:1px solid #eee; opacity:0.7;"

        c1.markdown(f"""<div style="padding:20px; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.05); text-align:center; {s_rebu}"><div style="color:#666; font-weight:bold; margin-bottom:5px;">REBU</div><div style="font-size:28px; color:{C_MAIN}; font-weight:800;">{m_rebu:,.0f} €</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div style="padding:20px; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.05); text-align:center; {s_pro}"><div style="color:#666; font-weight:bold; margin-bottom:5px;">PRO</div><div style="font-size:28px; color:{C_MAIN}; font-weight:800;">{m_pro:,.0f} €</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div style="padding:20px; border-radius:15px; box-shadow:0 4px 10px rgba(0,0,0,0.05); text-align:center; {s_intra}"><div style="color:#666; font-weight:bold; margin-bottom:5px;">INTRA</div><div style="font-size:28px; color:{C_MAIN}; font-weight:800;">{m_intra:,.0f} €</div></div>""", unsafe_allow_html=True)
