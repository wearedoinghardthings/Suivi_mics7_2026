import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io, qrcode, datetime, zipfile, base64, time
from PIL import Image

try:
    from streamlit_qrcode_scanner import qrcode_scanner
    QR_LIVE_OK = True
except Exception:
    QR_LIVE_OK = False

try:
    from pyzbar.pyzbar import decode as qr_decode
    QR_PYZBAR_OK = True
except Exception:
    QR_PYZBAR_OK = False

# ════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Formation — Notes & Présences",
    page_icon="📊", layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS (desktop + mobile) ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif !important;
  background-color: #ffffff !important;
  color: #1a1a2e !important;
}
.main, .block-container {
  background-color: #ffffff !important;
  padding-top: 1rem !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: linear-gradient(160deg, #f0f4ff 0%, #e8f0fe 100%) !important;
  border-right: 1px solid #dce4f5;
}
section[data-testid="stSidebar"] * { color: #1a1a2e !important; }

/* ── Titres ── */
.main-title {
  font-family: 'DM Serif Display', serif;
  font-size: clamp(1.4rem, 4vw, 2rem);
  color: #2c3e7a; margin-bottom: .1rem;
}
.sub-title { font-size: clamp(.78rem, 2.5vw, .9rem); color: #6b7db3; margin-bottom: 1rem; }

/* ── KPI Cards ── */
.kpi-card {
  background: #fff; border: 1px solid #e0e8ff; border-radius: 14px;
  padding: clamp(10px, 2vw, 16px); text-align: center;
  box-shadow: 0 2px 10px rgba(44,62,122,.06); margin-bottom: 6px;
}
.kpi-value { font-size: clamp(1.3rem, 3.5vw, 1.7rem); font-weight: 700; color: #2c3e7a; line-height: 1; }
.kpi-label { font-size: clamp(.65rem, 1.8vw, .74rem); color: #7a8db3; margin-top: 4px;
             text-transform: uppercase; letter-spacing: .6px; font-weight: 500; }
.kpi-sub   { font-size: .68rem; color: #a0aec0; margin-top: 2px; }

/* ── Section titles ── */
.section-title {
  font-family: 'DM Serif Display', serif;
  font-size: clamp(1rem, 3vw, 1.2rem); color: #2c3e7a;
  margin-top: 1.3rem; margin-bottom: .4rem;
  border-left: 4px solid #4a6cf7; padding-left: 11px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: #f0f4ff; border-radius: 10px; padding: 4px; gap: 3px; flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px; font-weight: 500; color: #2c3e7a;
  padding: 6px 10px; font-size: clamp(.72rem, 2vw, .83rem); white-space: nowrap;
}
.stTabs [aria-selected="true"] {
  background: #fff !important; color: #4a6cf7 !important;
  box-shadow: 0 1px 6px rgba(74,108,247,.15);
}

/* ── Buttons ── */
.stDownloadButton > button {
  background: linear-gradient(135deg, #4a6cf7, #7b5ea7) !important;
  color: #fff !important; border: none !important;
  border-radius: 8px !important; font-weight: 600 !important;
  padding: 8px 16px !important; width: 100%;
}
.stButton > button {
  border-radius: 8px !important; font-weight: 500 !important;
  min-height: 44px; font-size: clamp(.82rem, 2.5vw, .9rem);
}

/* ── Badges mention ── */
.badge-tb { background:#e6f4ea;color:#1e7e34;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600; }
.badge-b  { background:#dbeafe;color:#1a56db;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600; }
.badge-ab { background:#fef3c7;color:#92400e;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600; }
.badge-in { background:#fee2e2;color:#b91c1c;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600; }

/* ── Scanner box ── */
.scan-box {
  background: #f8faff; border: 2px dashed #4a6cf7;
  border-radius: 14px; padding: 16px; text-align: center; margin: 8px 0;
}
.scan-success {
  background: #f0fdf4; border: 2px solid #bbf7d0;
  border-radius: 14px; padding: 16px; text-align: center; margin: 8px 0;
}
.scan-wait {
  background: #fffbeb; border: 2px solid #fcd34d;
  border-radius: 14px; padding: 16px; text-align: center; margin: 8px 0;
}

/* ── QR grid ── */
.qr-grid { display: flex; flex-wrap: wrap; gap: 10px; }
.qr-item {
  background: #fff; border: 1px solid #e0e8ff; border-radius: 10px;
  padding: 8px; text-align: center;
  width: clamp(110px, 22vw, 140px);
  box-shadow: 0 1px 6px rgba(44,62,122,.06);
}
.qr-name { font-size: clamp(.62rem, 1.8vw, .72rem); color: #2c3e7a; font-weight: 600;
           margin-top: 5px; line-height: 1.3; word-break: break-word; }

/* ── Admin box ── */
.admin-box {
  background: #faf5ff; border: 1px solid #e9d5ff;
  border-radius: 12px; padding: 16px; margin: 8px 0;
}

/* ── Mobile overrides ── */
@media (max-width: 768px) {
  .block-container { padding: .5rem .75rem 2rem !important; }
  .main-title { font-size: 1.5rem !important; }
  .kpi-value { font-size: 1.4rem !important; }
  .stTabs [data-baseweb="tab"] { padding: 5px 7px !important; font-size: .72rem !important; }
  section[data-testid="stSidebar"] { font-size: .88rem; }
  .qr-item { width: calc(50% - 10px) !important; }
}
@media (max-width: 480px) {
  .kpi-card { padding: 10px 8px !important; }
  .kpi-value { font-size: 1.2rem !important; }
  .kpi-label { font-size: .6rem !important; }
}
/* Forcer texte lisible sur mobile dans dataframe */
[data-testid="stDataFrame"] { font-size: clamp(.72rem, 2vw, .85rem) !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# DONNÉES PAR DÉFAUT
# ════════════════════════════════════════════════════════════════════════════
DEFAULT_DATA = {
    "Nom et Prénom": [
        "Acka Gustave Boris","Agnero Djadja","Kra Yao Assouman Aubin Gael",
        "Kouao Marie-Paule","Sangaré Aissata","Kouassi Kangah Akissi Philomène",
        "Yao Julienne","Amankan Adjo Josiane","Fouati Edwige","Agnehoura Vanessa",
        "Djeha Somaud Marthe Abigail","Gnomblé Christelle","Loua Saty Veronique",
        "Coulibaly Lancina Medard","Deza Boga Stefan","Beugré Brigitte",
        "Bogui Kacohon Prisca Sandrine epse Gris","Touré Madongon Mariam",
        "Konan Amenan Grâce-Victoire","Diarrassouba Madoussou",
    ],
    "Note 2":[18,18,17,18,17,13,16,16,15,14,14,15,0,14,0,10,0,14,0,0],
    "Note 3":[14,14,6,0,11,11,11,9,9,9,11,6,14,6,6,9,3,11,0,0],
    "Note 4":[15,18,15,14,13,14,13,15,14,16,0,14,15,9,10,0,15,15,11,0],
    "Note 5":[20,13,10,17,13,10,10,0,13,0,13,13,13,10,13,13,10,10,10,0],
    "Note 6":[12,16,16,12,14,16,16,16,12,14,14,8,12,12,12,18,14,12,12,10],
    "Note 7":[19,17,19,19,18,18,17,15,18,18,16,19,17,17,17,15,18,15,14,11],
    "Note 8":[20,20,18,18,15,18,13,17,13,17,17,15,15,15,17,12,18,0,13,10],
    "Note 9":[18,18,19,20,15,14,13,19,12,17,17,9,12,13,16,13,0,0,8,3],
}

# ════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "presences":        pd.DataFrame(columns=["Agent","Date","Heure","Session","Statut"]),
        "data_source":      "default",
        "gsheet_url":       "",
        "sessions_config":  ["Jour 1 - Matin","Jour 1 - Après-midi",
                             "Jour 2 - Matin","Jour 2 - Après-midi","Jour 3 - Matin"],
        "session_active":   "Jour 1 - Matin",
        "camera_on":        False,
        "last_scan_agent":  None,
        "last_scan_time":   None,
        "admin_logged_in":  False,
        "scan_cooldown":    2.0,  # secondes entre deux scans
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# ════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ════════════════════════════════════════════════════════════════════════════
def mention_info(n):
    if n>=16:  return "Très Bien","badge-tb"
    elif n>=14: return "Bien","badge-b"
    elif n>=10: return "Assez Bien","badge-ab"
    else:       return "Insuffisant","badge-in"

def get_note_cols(df): return [c for c in df.columns if c != df.columns[0]]

def compute_stats(df, note_cols, name_col):
    rows = []
    for _, row in df.iterrows():
        vals = [float(row[c]) for c in note_cols]
        moy  = round(np.mean(vals), 2)
        ml, _ = mention_info(moy)
        rows.append({"Agent":row[name_col],"Moyenne":moy,"Max":max(vals),
                     "Min":min(vals),"Médiane":round(np.median(vals),2),
                     "Écart-type":round(np.std(vals),2),"Nb notes":len(vals),"Mention":ml})
    return pd.DataFrame(rows)

def style_row(row):
    styles = []
    for col in row.index:
        if col in ["Moyenne","Max","Min","Médiane"]:
            v = row[col]
            if v>=16:   styles.append("background-color:#e6f4ea;color:#1e7e34")
            elif v>=14: styles.append("background-color:#dbeafe;color:#1a56db")
            elif v>=10: styles.append("background-color:#fef3c7;color:#92400e")
            else:       styles.append("background-color:#fee2e2;color:#b91c1c")
        else: styles.append("")
    return styles

def agent_to_qr_key(name): return f"AGENT::{name}"
def key_to_agent(key): return key.split("::",1)[1] if "::" in key else key

def add_presence(agent, session, statut="Présent"):
    now = datetime.datetime.now()
    new_row = pd.DataFrame([{
        "Agent":agent, "Date":now.strftime("%d/%m/%Y"),
        "Heure":now.strftime("%H:%M:%S"), "Session":session, "Statut":statut,
    }])
    st.session_state.presences = pd.concat(
        [st.session_state.presences, new_row], ignore_index=True)

def is_already_pointed(agent, session):
    pres = st.session_state.presences
    if len(pres) == 0: return False, None
    today = datetime.date.today().strftime("%d/%m/%Y")
    match = pres[(pres["Agent"]==agent)&(pres["Session"]==session)&(pres["Date"]==today)]
    if len(match) > 0: return True, match.iloc[0]["Heure"]
    return False, None

def presence_stats_only_pointed(agents):
    """
    Stats uniquement sur les agents ayant AU MOINS UN pointage.
    Pas de statut 'Absent' automatique — on attend le pointage.
    """
    pres = st.session_state.presences
    sessions = st.session_state.sessions_config
    rows = []
    for agent in agents:
        ap = pres[pres["Agent"] == agent]
        if len(ap) == 0:
            rows.append({
                "Agent":agent,"Présences":0,
                "Sessions totales":len(sessions),"Taux (%)":0.0,
                "Statut":"Non pointé",
            })
        else:
            sessions_done = ap["Session"].unique().tolist()
            nb = len(sessions_done)
            taux = round(nb / len(sessions) * 100, 1) if sessions else 0
            rows.append({
                "Agent":agent,"Présences":nb,
                "Sessions totales":len(sessions),"Taux (%)":taux,
                "Statut":"Assidu" if taux>=80 else ("Moyen" if taux>=50 else "Faible"),
            })
    return pd.DataFrame(rows)

def get_admin_password():
    try:
        return st.secrets["admin"]["password"]
    except Exception:
        return "formation2026"

def load_gsheet_data(url):
    try:
        if "spreadsheets/d/" in url:
            sid = url.split("spreadsheets/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
        else:
            csv_url = url
        df = pd.read_csv(csv_url)
        df.columns = df.columns.astype(str).str.strip()
        return df, None
    except Exception as e:
        return None, str(e)

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Source des données (notes)")
    source_choice = st.radio("Source",
        ["📌 Données par défaut","📁 Fichier Excel","🔗 Google Sheets"],
        label_visibility="collapsed")
    uploaded_file = None
    if "Excel" in source_choice:
        st.session_state.data_source = "excel"
        uploaded_file = st.file_uploader("Excel", type=["xlsx","xls"], label_visibility="collapsed")
    elif "Google" in source_choice:
        st.session_state.data_source = "gsheet"
        st.session_state.gsheet_url = st.text_input(
            "URL Google Sheets", value=st.session_state.gsheet_url,
            placeholder="https://docs.google.com/spreadsheets/d/...")
    else:
        st.session_state.data_source = "default"
    st.markdown("---")

# ── Chargement données notes ─────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_gsheet_cached(url): return load_gsheet_data(url)

if st.session_state.data_source == "excel" and uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.astype(str).str.strip()
        st.sidebar.success(f"✅ {df.shape[0]} agents · {df.shape[1]-1} notes")
    except Exception as e:
        st.sidebar.error(str(e)); df = pd.DataFrame(DEFAULT_DATA)
elif st.session_state.data_source == "gsheet" and st.session_state.gsheet_url:
    df, err = fetch_gsheet_cached(st.session_state.gsheet_url)
    if err:
        st.sidebar.error(err); df = pd.DataFrame(DEFAULT_DATA)
    else:
        st.sidebar.success(f"✅ Google Sheets · {df.shape[0]} agents")
        st.sidebar.caption("🔄 Actualisation automatique 60 s")
else:
    df = pd.DataFrame(DEFAULT_DATA)
    st.sidebar.info("📌 Données par défaut")

name_col  = df.columns[0]
note_cols = get_note_cols(df)
agents    = df[name_col].tolist()

with st.sidebar:
    st.markdown("### 🗓️ Session active")
    if st.session_state.session_active not in st.session_state.sessions_config:
        st.session_state.session_active = st.session_state.sessions_config[0]
    st.session_state.session_active = st.selectbox(
        "Session", st.session_state.sessions_config,
        index=st.session_state.sessions_config.index(st.session_state.session_active),
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### 🔍 Filtres (courbes)")
    selected_agents = st.multiselect("Agents", options=agents, default=agents[:5])
    note_range = st.slider("Filtre moyenne", 0.0, 20.0, (0.0, 20.0), 0.5)
    st.markdown("---")
    pres = st.session_state.presences
    nb_pts = len(pres)
    nb_sess = len(pres[pres["Session"]==st.session_state.session_active]["Agent"].unique()) if nb_pts>0 else 0
    st.metric("Pointages total", nb_pts)
    st.metric(f"Présents ({st.session_state.session_active[:6]}…)", nb_sess)

# ════════════════════════════════════════════════════════════════════════════
# EN-TÊTE
# ════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="main-title">📊 Formation — Notes & Présences</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">{len(agents)} agents · {len(note_cols)} évaluations · '
    f'Session : <b>{st.session_state.session_active}</b></div>',
    unsafe_allow_html=True)

all_vals = df[note_cols].values.flatten().astype(float)
df_stats = compute_stats(df, note_cols, name_col)

# KPI
k1,k2,k3,k4,k5,k6 = st.columns(6)
nb_presents_session = len(pres[pres["Session"]==st.session_state.session_active]["Agent"].unique()) if nb_pts>0 else 0
kpi_list = [
    (round(np.mean(all_vals),2), "Moyenne Générale","toutes notes"),
    (len(agents),                "Agents inscrits", "total"),
    (nb_presents_session,        "Présents",        f"session active"),
    (len(agents)-nb_presents_session,"Non pointés", "session active"),
    (int((df[note_cols]==20).sum().sum()), "Notes 20/20","parfaits"),
    (nb_pts,                     "Total pointages", "enregistrés"),
]
for col,(val,label,sub) in zip([k1,k2,k3,k4,k5,k6],kpi_list):
    col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
                 f'<div class="kpi-label">{label}</div><div class="kpi-sub">{sub}</div></div>',
                 unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# ONGLETS
# ════════════════════════════════════════════════════════════════════════════
(tab_scan, tab_qr, tab_pres, tab_croise,
 tab_notes, tab_tendance, tab_stats,
 tab_heatmap, tab_podium, tab_config) = st.tabs([
    "📷 Pointage",
    "🎫 QR Codes",
    "👥 Présences",
    "🔗 Notes × Présences",
    "📈 Courbes notes",
    "🌐 Tendance",
    "📋 Stats",
    "🔥 Heatmap",
    "🏆 Classement",
    "⚙️ Config & Admin",
])

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET POINTAGE
# ─────────────────────────────────────────────────────────────────────────────
with tab_scan:
    st.markdown('<div class="section-title">📷 Pointage — Scan QR Code</div>', unsafe_allow_html=True)
    st.markdown(f"**Session active :** `{st.session_state.session_active}`")

    col_cam, col_manual = st.columns([1, 1])

    with col_cam:
        st.markdown("**Mode automatique — Scan QR**")

        # Bouton Ouvrir / Fermer caméra
        if not st.session_state.camera_on:
            if st.button("📷 Ouvrir la caméra", type="primary", use_container_width=True):
                st.session_state.camera_on = True
                st.session_state.last_scan_agent = None
                st.rerun()
        else:
            if st.button("🔴 Fermer la caméra", type="secondary", use_container_width=True):
                st.session_state.camera_on = False
                st.rerun()

        if st.session_state.camera_on:
            # Affichage du dernier scan
            if st.session_state.last_scan_agent:
                agent_ok = st.session_state.last_scan_agent
                ml, mc = mention_info(df_stats[df_stats["Agent"]==agent_ok]["Moyenne"].values[0]
                                       if agent_ok in df_stats["Agent"].values else 0)
                st.markdown(f'''<div class="scan-success">
                    ✅ <b>{agent_ok}</b> pointé à {st.session_state.last_scan_time}<br>
                    <small>En attente du prochain QR code…</small>
                </div>''', unsafe_allow_html=True)
            else:
                st.markdown('<div class="scan-box">📸 Présentez un QR code devant la caméra</div>',
                            unsafe_allow_html=True)

            # Scanner QR continu
            if QR_LIVE_OK:
                qr_result = qrcode_scanner(key=f"scanner_{int(time.time()/3)}")
                if qr_result:
                    agent_found = key_to_agent(qr_result)
                    if agent_found in agents:
                        deja, heure_deja = is_already_pointed(agent_found, st.session_state.session_active)
                        if not deja:
                            add_presence(agent_found, st.session_state.session_active)
                            st.session_state.last_scan_agent = agent_found
                            st.session_state.last_scan_time  = datetime.datetime.now().strftime("%H:%M:%S")
                            st.rerun()
                        else:
                            st.warning(f"ℹ️ **{agent_found}** déjà pointé à {heure_deja}")
                    else:
                        st.error(f"❌ QR non reconnu : `{agent_found}`")
            else:
                # Fallback : photo manuelle avec pyzbar
                st.caption("Mode photo (scanner QR automatique non disponible)")
                cam = st.camera_input("Photo QR", label_visibility="collapsed")
                if cam and QR_PYZBAR_OK:
                    img = Image.open(cam)
                    try:
                        from pyzbar.pyzbar import decode as qr_decode
                        decoded = qr_decode(img)
                        if decoded:
                            agent_found = key_to_agent(decoded[0].data.decode("utf-8"))
                            if agent_found in agents:
                                deja, heure_deja = is_already_pointed(agent_found, st.session_state.session_active)
                                if not deja:
                                    add_presence(agent_found, st.session_state.session_active)
                                    st.session_state.last_scan_agent = agent_found
                                    st.session_state.last_scan_time  = datetime.datetime.now().strftime("%H:%M:%S")
                                    st.success(f"✅ **{agent_found}** pointé !")
                                else:
                                    st.warning(f"ℹ️ Déjà pointé à {heure_deja}")
                            else:
                                st.error(f"❌ Agent inconnu : `{agent_found}`")
                        else:
                            st.error("❌ QR code non reconnu dans l'image.")
                    except Exception as e:
                        st.error(f"Erreur décodage : {e}")

    with col_manual:
        st.markdown("**Mode manuel — Sélection directe**")
        with st.form("form_manual"):
            agent_sel  = st.selectbox("Agent", agents, key="manual_agent")
            statut_sel = st.selectbox("Statut", ["Présent","En retard","Excusé"])
            ok = st.form_submit_button("✅ Enregistrer", use_container_width=True)
            if ok:
                deja, heure_deja = is_already_pointed(agent_sel, st.session_state.session_active)
                if not deja:
                    add_presence(agent_sel, st.session_state.session_active, statut_sel)
                    st.success(f"✅ **{agent_sel}** — {statut_sel} ({datetime.datetime.now().strftime('%H:%M:%S')})")
                else:
                    st.info(f"ℹ️ Déjà pointé à {heure_deja}")

    # Journal du jour
    st.markdown('<div class="section-title">📋 Journal — aujourd\'hui</div>', unsafe_allow_html=True)
    today = datetime.date.today().strftime("%d/%m/%Y")
    pres_today = st.session_state.presences[
        (st.session_state.presences["Session"]==st.session_state.session_active) &
        (st.session_state.presences["Date"]==today)
    ].sort_values("Heure", ascending=False).reset_index(drop=True)

    if len(pres_today) > 0:
        st.dataframe(pres_today, use_container_width=True, hide_index=True, height=320)
        buf_j = io.BytesIO()
        pres_today.to_csv(buf_j, index=False, encoding="utf-8-sig")
        st.download_button("⬇️ Exporter journal session", buf_j.getvalue(),
            file_name=f"journal_{st.session_state.session_active[:10]}.csv", mime="text/csv")
    else:
        st.info("Aucun pointage pour cette session aujourd'hui.")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET QR CODES
# ─────────────────────────────────────────────────────────────────────────────
with tab_qr:
    st.markdown('<div class="section-title">🎫 Génération des QR Codes agents</div>', unsafe_allow_html=True)
    st.caption(f"{len(agents)} agents détectés · 1 QR par agent · Téléchargement ZIP")

    col_o1, col_o2 = st.columns([2,1])
    with col_o1:
        agents_qr_sel = st.multiselect("Agents à inclure (vide = tous)", options=agents,
                                        placeholder="Tous les agents")
    with col_o2:
        qr_size = st.selectbox("Taille", ["Petite","Normale","Grande"], index=1)
    qr_box = {"Petite":4,"Normale":6,"Grande":8}[qr_size]
    agents_to_gen = agents_qr_sel if agents_qr_sel else agents
    st.markdown(f"**{len(agents_to_gen)}** QR code(s) à générer")

    if st.button("🔄 Générer les QR Codes", type="primary", use_container_width=True):
        zip_buf = io.BytesIO()
        preview_data = []
        with zipfile.ZipFile(zip_buf,"w",zipfile.ZIP_DEFLATED) as zf:
            prog = st.progress(0, text="Génération…")
            for i, agent in enumerate(agents_to_gen):
                qr_obj = qrcode.QRCode(version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=qr_box, border=3)
                qr_obj.add_data(agent_to_qr_key(agent))
                qr_obj.make(fit=True)
                img = qr_obj.make_image(fill_color="#2c3e7a", back_color="white")
                buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
                raw = buf.getvalue()
                safe = agent.replace("/","_")[:60]
                zf.writestr(f"QR_Badges/{safe}.png", raw)
                preview_data.append({"name":agent,"b64":base64.b64encode(raw).decode()})
                prog.progress((i+1)/len(agents_to_gen), text=f"{i+1}/{len(agents_to_gen)} — {agent[:28]}…")
            prog.empty()
        zip_buf.seek(0)
        st.success(f"✅ {len(agents_to_gen)} QR codes générés !")
        st.download_button(
            f"⬇️ Télécharger ZIP ({len(agents_to_gen)} badges)",
            data=zip_buf.getvalue(), file_name="QR_Badges_Formation.zip",
            mime="application/zip", use_container_width=True)

        html_grid = '<div class="qr-grid">'
        for item in preview_data:
            html_grid += (f'<div class="qr-item">'
                          f'<img src="data:image/png;base64,{item["b64"]}" '
                          f'style="width:100%;border-radius:5px">'
                          f'<div class="qr-name">{item["name"][:35]}</div></div>')
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)

    with st.expander("💡 Mode d'emploi"):
        st.markdown("""
1. Cliquez **Générer les QR Codes** → téléchargez le ZIP
2. Imprimez chaque PNG (1 badge par agent) ou envoyez par **WhatsApp / email**
3. Le jour J : superviseur ouvre **📷 Pointage** → ouvre la caméra
4. Agent présente son badge → détection automatique → pointage enregistré
5. La caméra reste ouverte pour le prochain agent jusqu'à ce que vous la fermiez
""")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET PRÉSENCES
# ─────────────────────────────────────────────────────────────────────────────
with tab_pres:
    st.markdown('<div class="section-title">👥 Statistiques de présence</div>', unsafe_allow_html=True)

    if len(st.session_state.presences) == 0:
        st.info("Aucun pointage enregistré. Utilisez l'onglet **📷 Pointage** pour commencer.")
    else:
        pres_all = st.session_state.presences
        df_pres = presence_stats_only_pointed(agents)

        nb_pointes = len(df_pres[df_pres["Présences"]>0])
        taux_moy   = round(df_pres[df_pres["Présences"]>0]["Taux (%)"].mean(),1) if nb_pointes>0 else 0
        nb_assidus = len(df_pres[df_pres["Statut"]=="Assidu"])

        pa,pb,pc,pd_ = st.columns(4)
        for col,(val,label,sub) in zip([pa,pb,pc,pd_],[
            (f"{taux_moy}%","Taux moyen","agents pointés"),
            (nb_pointes,   "Agents pointés","au moins 1 session"),
            (nb_assidus,   "Assidus (≥80%)","agents"),
            (len(pres_all),"Pointages total","enregistrés"),
        ]):
            col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
                         f'<div class="kpi-label">{label}</div><div class="kpi-sub">{sub}</div></div>',
                         unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Barre taux (uniquement agents pointés)
        df_sorted = df_pres[df_pres["Présences"]>0].sort_values("Taux (%)", ascending=True)
        if len(df_sorted) > 0:
            colors_p = ["#27ae60" if t>=80 else "#f39c12" if t>=50 else "#e74c3c"
                        for t in df_sorted["Taux (%)"]]
            fig_p = go.Figure(go.Bar(
                x=df_sorted["Taux (%)"], y=df_sorted["Agent"], orientation="h",
                marker=dict(color=colors_p, line=dict(color="white",width=0.5)),
                text=[f"{v}%" for v in df_sorted["Taux (%)"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x}%<extra></extra>"))
            fig_p.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="DM Sans",color="#2c3e7a"),
                xaxis=dict(title="Taux de présence (%)",range=[0,118],gridcolor="#f0f4ff"),
                yaxis=dict(tickfont=dict(size=10),autorange="reversed"),
                height=max(360, len(df_sorted)*30),
                margin=dict(t=20,b=40,l=230,r=60),showlegend=False,
                shapes=[dict(type="line",xref="x",x0=80,x1=80,yref="paper",y0=0,y1=1,
                             line=dict(color="#27ae60",width=1.5,dash="dot"))])
            st.plotly_chart(fig_p, use_container_width=True)

        # Tableau
        def style_pres_row(row):
            styles=[]
            for col in row.index:
                if col=="Taux (%)":
                    v=row[col]
                    if v>=80:   styles.append("background-color:#e6f4ea;color:#1e7e34")
                    elif v>=50: styles.append("background-color:#fef3c7;color:#92400e")
                    elif v>0:   styles.append("background-color:#fee2e2;color:#b91c1c")
                    else:       styles.append("background-color:#f9fafb;color:#9ca3af")
                else: styles.append("")
            return styles

        st.dataframe(
            df_pres.sort_values("Taux (%)", ascending=False).reset_index(drop=True)
            .style.apply(style_pres_row, axis=1).format({"Taux (%)":"{:.1f}%"}),
            use_container_width=True, height=420)

        # Par session
        st.markdown('<div class="section-title">Présences par session</div>', unsafe_allow_html=True)
        sc = pres_all.groupby("Session")["Agent"].nunique().reset_index()
        sc.columns=["Session","Nb présents"]
        sc["Taux (%)"]=round(sc["Nb présents"]/len(agents)*100,1)
        fig_sc = go.Figure(go.Bar(
            x=sc["Session"], y=sc["Nb présents"],
            marker=dict(color="#4a6cf7",line=dict(color="white",width=0.5)),
            text=[f"{v}<br>({t}%)" for v,t in zip(sc["Nb présents"],sc["Taux (%)"])],
            textposition="outside"))
        fig_sc.update_layout(paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(gridcolor="#f0f4ff"),
            yaxis=dict(title="Agents présents",range=[0,len(agents)*1.3],gridcolor="#f0f4ff"),
            height=340,margin=dict(t=20,b=60,l=60,r=20),showlegend=False)
        st.plotly_chart(fig_sc, use_container_width=True)

        # Export
        buf_p = io.BytesIO()
        with pd.ExcelWriter(buf_p, engine="openpyxl") as w:
            pres_all.to_excel(w, sheet_name="Pointages", index=False)
            df_pres.to_excel(w, sheet_name="Stats présences", index=False)
        st.download_button("⬇️ Exporter présences (Excel)", buf_p.getvalue(),
            file_name="presences_formation.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET CROISEMENT
# ─────────────────────────────────────────────────────────────────────────────
with tab_croise:
    st.markdown('<div class="section-title">🔗 Croisement Notes × Présences</div>', unsafe_allow_html=True)
    if len(st.session_state.presences) == 0:
        st.info("Enregistrez des présences pour activer cette analyse.")
    else:
        df_ps = presence_stats_only_pointed(agents)
        df_cx = df_stats.merge(df_ps[["Agent","Taux (%)","Présences","Statut"]], on="Agent", how="left")
        df_cx["Taux (%)"] = df_cx["Taux (%)"].fillna(0)
        df_cx["Présences"] = df_cx["Présences"].fillna(0).astype(int)
        df_cx["Statut présence"] = df_cx["Statut"].fillna("Non pointé")

        color_map = {"Assidu":"#27ae60","Moyen":"#f39c12","Faible":"#e74c3c","Non pointé":"#9ca3af"}
        fig_sc2 = go.Figure()
        for st_val, color in color_map.items():
            sub = df_cx[df_cx["Statut présence"]==st_val]
            if len(sub) > 0:
                fig_sc2.add_trace(go.Scatter(
                    x=sub["Taux (%)"], y=sub["Moyenne"],
                    mode="markers+text", name=st_val,
                    marker=dict(size=12,color=color,opacity=0.8,line=dict(color="white",width=1.5)),
                    text=sub["Agent"].str.split().str[0],
                    textposition="top center", textfont=dict(size=9),
                    hovertemplate="<b>%{text}</b><br>Présence : %{x}%<br>Moy : %{y:.2f}/20<extra></extra>"))
        # tendance
        pts_real = df_cx[df_cx["Taux (%)"]>0]
        if len(pts_real) > 3:
            try:
                z = np.polyfit(pts_real["Taux (%)"], pts_real["Moyenne"], 1)
                p = np.poly1d(z)
                xl = np.linspace(0, 100, 50)
                fig_sc2.add_trace(go.Scatter(x=xl, y=p(xl), mode="lines", name="Tendance",
                    line=dict(color="#4a6cf7",width=2,dash="dash"), hoverinfo="skip"))
            except Exception: pass
        fig_sc2.update_layout(
            title="Présence (%) vs Moyenne des notes",
            paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Taux de présence (%)",range=[-5,110],gridcolor="#f0f4ff"),
            yaxis=dict(title="Moyenne /20",range=[0,21],gridcolor="#f0f4ff"),
            legend=dict(bgcolor="rgba(255,255,255,.95)",bordercolor="#dce4f5",borderwidth=1),
            height=480,margin=dict(t=50,b=40,l=50,r=20))
        st.plotly_chart(fig_sc2, use_container_width=True)

        if len(pts_real) > 3:
            corr = round(pts_real["Taux (%)"].corr(pts_real["Moyenne"]), 3)
            interp = ("forte positive" if corr>0.6 else "modérée positive" if corr>0.3
                      else "faible" if corr>0 else "négative ou nulle")
            st.info(f"**Corrélation présence / notes : {corr}** — corrélation {interp}")

        st.dataframe(df_cx[["Agent","Moyenne","Mention","Taux (%)","Présences","Statut présence"]]
            .sort_values("Moyenne",ascending=False).reset_index(drop=True)
            .style.apply(lambda r: [
                ("background-color:#e6f4ea;color:#1e7e34" if r["Moyenne"]>=16 else
                 "background-color:#dbeafe;color:#1a56db" if r["Moyenne"]>=14 else
                 "background-color:#fef3c7;color:#92400e" if r["Moyenne"]>=10 else
                 "background-color:#fee2e2;color:#b91c1c") if c=="Moyenne" else ""
                for c in r.index], axis=1)
            .format({"Moyenne":"{:.2f}","Taux (%)":"{:.1f}%"}),
            use_container_width=True, height=440)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLETS NOTES (Courbes / Tendance / Stats / Heatmap / Classement)
# ─────────────────────────────────────────────────────────────────────────────
with tab_notes:
    st.markdown('<div class="section-title">📈 Évolution individuelle</div>', unsafe_allow_html=True)
    if not selected_agents:
        st.info("👈 Sélectionnez des agents dans le panneau latéral.")
    else:
        palette = (px.colors.qualitative.Pastel+px.colors.qualitative.Safe
                   +px.colors.qualitative.Vivid+px.colors.qualitative.Dark24)
        fig = go.Figure()
        for i, agent in enumerate(selected_agents):
            row = df[df[name_col]==agent].iloc[0]
            notes = [float(row[c]) for c in note_cols]
            c = palette[i%len(palette)]
            fig.add_trace(go.Scatter(x=note_cols,y=notes,mode="lines+markers+text",name=agent,
                line=dict(color=c,width=2.5,shape="spline"),
                marker=dict(size=9,color=c,line=dict(color="white",width=1.5)),
                text=[str(int(n)) for n in notes],textposition="top center",
                textfont=dict(size=9,color=c),
                hovertemplate=f"<b>{agent}</b><br>%{{x}} : <b>%{{y}}</b>/20<extra></extra>"))
        fig.update_layout(paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Évaluation",gridcolor="#f0f4ff"),
            yaxis=dict(title="Note /20",range=[-0.5,21],gridcolor="#f0f4ff"),
            legend=dict(bgcolor="rgba(255,255,255,.95)",bordercolor="#dce4f5",borderwidth=1,font=dict(size=10)),
            hovermode="x unified",height=480,margin=dict(t=30,b=40,l=50,r=80),
            shapes=[dict(type="line",xref="paper",x0=0,x1=1,yref="y",y0=10,y1=10,
                         line=dict(color="#e74c3c",width=1.5,dash="dot")),
                    dict(type="line",xref="paper",x0=0,x1=1,yref="y",y0=14,y1=14,
                         line=dict(color="#27ae60",width=1.5,dash="dot"))],
            annotations=[dict(xref="paper",x=1.01,yref="y",y=10,text="Seuil 10",
                               showarrow=False,font=dict(size=9,color="#e74c3c"),xanchor="left"),
                         dict(xref="paper",x=1.01,yref="y",y=14,text="Seuil 14",
                               showarrow=False,font=dict(size=9,color="#27ae60"),xanchor="left")])
        st.plotly_chart(fig,use_container_width=True)

with tab_tendance:
    st.markdown('<div class="section-title">🌐 Tendance globale</div>',unsafe_allow_html=True)
    df_fl=df[note_cols].astype(float)
    moy_e=df_fl.mean().values; med_e=df_fl.median().values
    max_e=df_fl.max().values; min_e=df_fl.min().values; std_e=df_fl.std().values
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=list(note_cols)+list(reversed(note_cols)),
        y=list(max_e)+list(reversed(min_e)),fill="toself",fillcolor="rgba(74,108,247,0.07)",
        line=dict(color="rgba(0,0,0,0)"),hoverinfo="skip",name="Zone Min–Max"))
    fig2.add_trace(go.Scatter(x=list(note_cols)+list(reversed(note_cols)),
        y=list(moy_e+std_e)+list(reversed(moy_e-std_e)),fill="toself",
        fillcolor="rgba(74,108,247,0.12)",line=dict(color="rgba(0,0,0,0)"),hoverinfo="skip",name="±1σ"))
    fig2.add_trace(go.Scatter(x=note_cols,y=med_e,mode="lines+markers",name="Médiane",
        line=dict(color="#7b5ea7",width=2,dash="dash",shape="spline"),marker=dict(size=7,color="#7b5ea7"),
        hovertemplate="Médiane %{x} : <b>%{y:.2f}</b>/20<extra></extra>"))
    fig2.add_trace(go.Scatter(x=note_cols,y=moy_e,mode="lines+markers+text",name="Moyenne",
        line=dict(color="#4a6cf7",width=3,shape="spline"),
        marker=dict(size=10,color="#4a6cf7",line=dict(color="white",width=2)),
        text=[f"{v:.1f}" for v in moy_e],textposition="top center",textfont=dict(size=10,color="#2c3e7a"),
        hovertemplate="Moyenne %{x} : <b>%{y:.2f}</b>/20<extra></extra>"))
    fig2.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(title="Évaluation",gridcolor="#f0f4ff"),
        yaxis=dict(title="Note /20",range=[-0.5,21],gridcolor="#f0f4ff"),
        legend=dict(bgcolor="rgba(255,255,255,.95)",bordercolor="#dce4f5",borderwidth=1),
        hovermode="x unified",height=420,margin=dict(t=30,b=40,l=50,r=20))
    st.plotly_chart(fig2,use_container_width=True)
    st.dataframe(pd.DataFrame({"Évaluation":note_cols,"Moyenne":[round(v,2) for v in moy_e],
        "Médiane":[round(v,2) for v in med_e],"Max":[int(v) for v in max_e],
        "Min":[int(v) for v in min_e],"Écart-type":[round(v,2) for v in std_e]}),
        use_container_width=True,hide_index=True)

with tab_stats:
    st.markdown('<div class="section-title">📋 Stats par agent</div>',unsafe_allow_html=True)
    df_f=df_stats[(df_stats["Moyenne"]>=note_range[0])&(df_stats["Moyenne"]<=note_range[1])]\
         .sort_values("Moyenne",ascending=False).reset_index(drop=True)
    df_f.index+=1
    st.dataframe(df_f.style.apply(style_row,axis=1).format(
        {"Moyenne":"{:.2f}","Médiane":"{:.2f}","Écart-type":"{:.2f}","Max":"{:.0f}","Min":"{:.0f}"}),
        use_container_width=True,height=500)

with tab_heatmap:
    st.markdown('<div class="section-title">🔥 Carte de chaleur</div>',unsafe_allow_html=True)
    heat=df.set_index(name_col)[note_cols].astype(float)
    fig5=go.Figure(go.Heatmap(z=heat.values,x=note_cols,y=heat.index.tolist(),
        colorscale=[[0,"#fee2e2"],[0.001,"#fecaca"],[0.3,"#bfdbfe"],[0.6,"#4a6cf7"],[1,"#1a237e"]],
        text=heat.values.astype(int),texttemplate="%{text}",textfont=dict(size=10,color="#1a1a2e"),
        hovertemplate="<b>%{y}</b><br>%{x} : <b>%{z}</b>/20<extra></extra>",
        colorbar=dict(title="Note /20"),zmin=0,zmax=20))
    fig5.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(side="top"),yaxis=dict(autorange="reversed"),
        height=max(400,len(agents)*28),margin=dict(t=50,b=20,l=240,r=20))
    st.plotly_chart(fig5,use_container_width=True)

with tab_podium:
    st.markdown('<div class="section-title">🏆 Classement</div>',unsafe_allow_html=True)
    df_rk=df_stats.sort_values("Moyenne",ascending=False).reset_index(drop=True)
    df_rk.index+=1
    if len(df_rk)>=3:
        p2,p1,p3=st.columns([1,1.2,1])
        for col,rank,medal,bg in [(p1,1,"🥇","#FFF9C4"),(p2,2,"🥈","#F5F5F5"),(p3,3,"🥉","#FBE9E7")]:
            r=df_rk.iloc[rank-1]; ml,mc=mention_info(r["Moyenne"])
            col.markdown(f'''<div style="background:{bg};border-radius:16px;padding:16px;
                text-align:center;box-shadow:0 4px 16px rgba(0,0,0,.07);">
                <div style="font-size:2rem;">{medal}</div>
                <div style="font-weight:700;color:#2c3e7a;font-size:.9rem;margin-top:4px;">{r["Agent"]}</div>
                <div style="font-size:1.8rem;font-weight:700;color:#4a6cf7;">{r["Moyenne"]:.2f}</div>
                <div style="font-size:.75rem;color:#6b7db3;">/ 20</div>
                <span class="{mc}">{ml}</span>
            </div>''',unsafe_allow_html=True)
    colors_b=["#2d6a4f" if m>=16 else "#1a56db" if m>=14 else "#92400e" if m>=10 else "#b91c1c"
              for m in df_rk["Moyenne"]]
    fig_b=go.Figure(go.Bar(x=df_rk["Moyenne"],y=df_rk["Agent"],orientation="h",
        marker=dict(color=colors_b,line=dict(color="white",width=0.5)),
        text=[f"{v:.2f}" for v in df_rk["Moyenne"]],textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.2f}/20<extra></extra>"))
    fig_b.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(title="Moyenne /20",range=[0,23],gridcolor="#f0f4ff"),
        yaxis=dict(autorange="reversed",tickfont=dict(size=10)),
        height=max(400,len(agents)*28),margin=dict(t=20,b=40,l=230,r=60),showlegend=False,
        shapes=[dict(type="line",xref="x",x0=10,x1=10,yref="paper",y0=0,y1=1,
                     line=dict(color="#e74c3c",width=1.5,dash="dot")),
                dict(type="line",xref="x",x0=14,x1=14,yref="paper",y0=0,y1=1,
                     line=dict(color="#27ae60",width=1.5,dash="dot"))])
    st.plotly_chart(fig_b,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET CONFIG & ADMIN
# ─────────────────────────────────────────────────────────────────────────────
with tab_config:
    # ── LOGIN ADMIN ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🔐 Espace Administrateur</div>', unsafe_allow_html=True)

    if not st.session_state.admin_logged_in:
        st.markdown('<div class="admin-box">', unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe admin", type="password", placeholder="Entrez le mot de passe")
        if st.button("🔓 Se connecter", use_container_width=True):
            if pwd == get_admin_password():
                st.session_state.admin_logged_in = True
                st.success("✅ Connecté en tant qu'administrateur")
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
        st.markdown('</div>', unsafe_allow_html=True)
        st.info("🔒 Les fonctions d'import, de configuration des sessions et de gestion des données nécessitent un accès administrateur.")
    else:
        st.success("✅ Connecté en tant qu'administrateur")
        if st.button("🚪 Se déconnecter"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.markdown("---")

        # ── SESSIONS CONFIG ───────────────────────────────────────────────
        st.markdown('<div class="section-title">🗓️ Configuration des sessions</div>', unsafe_allow_html=True)
        sessions_txt = st.text_area("Sessions (1 par ligne)",
            value="\n".join(st.session_state.sessions_config), height=180)
        if st.button("💾 Sauvegarder les sessions"):
            new_s = [s.strip() for s in sessions_txt.split("\n") if s.strip()]
            if new_s:
                st.session_state.sessions_config = new_s
                st.success(f"✅ {len(new_s)} sessions configurées.")
            else:
                st.error("Liste vide.")

        st.markdown("---")

        # ── IMPORT POINTAGES (ADMIN SEULEMENT) ───────────────────────────
        st.markdown('<div class="section-title">📥 Import pointages (admin)</div>', unsafe_allow_html=True)
        st.caption("Importez un CSV de pointages exporté depuis cette application ou d'un autre poste.")
        csv_import = st.file_uploader("Charger un CSV de pointages", type=["csv"], key="import_pres_admin")
        if csv_import:
            try:
                df_imp = pd.read_csv(csv_import)
                required = {"Agent","Date","Heure","Session","Statut"}
                if required.issubset(set(df_imp.columns)):
                    before = len(st.session_state.presences)
                    st.session_state.presences = pd.concat(
                        [st.session_state.presences, df_imp], ignore_index=True
                    ).drop_duplicates(subset=["Agent","Date","Session"])
                    after = len(st.session_state.presences)
                    st.success(f"✅ {after - before} nouveaux pointages importés ({after} au total).")
                    st.rerun()
                else:
                    st.error(f"Colonnes requises : {required}")
            except Exception as e:
                st.error(str(e))

        st.markdown('<div class="section-title">🔗 Synchronisation Google Sheets (pointages partagés)</div>',
                    unsafe_allow_html=True)
        st.markdown("""
**Comment partager les pointages entre plusieurs postes :**
1. Exportez les pointages via le bouton ci-dessous (CSV)
2. Ouvrez votre Google Sheets → importez le CSV dans une feuille "Pointages"
3. Partagez le lien public du Google Sheets avec les autres admins
4. Les autres postes importent depuis cette URL via **Source des données**

> 💡 Une synchronisation automatique via API Google est possible —
> contactez votre administrateur système pour configurer les credentials.
        """)

        # ── GESTION POINTAGES ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="section-title">🗂️ Gestion des pointages enregistrés</div>',
                    unsafe_allow_html=True)
        if len(st.session_state.presences) > 0:
            st.dataframe(st.session_state.presences, use_container_width=True, height=280)
            cola, colb = st.columns(2)
            with cola:
                buf_all = io.BytesIO()
                with pd.ExcelWriter(buf_all, engine="openpyxl") as w:
                    st.session_state.presences.to_excel(w, sheet_name="Pointages", index=False)
                st.download_button("⬇️ Export Excel", buf_all.getvalue(),
                    file_name="pointages_complets.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            with colb:
                csv_exp = st.session_state.presences.to_csv(
                    index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button("⬇️ Export CSV (partage)", csv_exp,
                    file_name="pointages_partage.csv", mime="text/csv",
                    use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Effacer TOUS les pointages", type="secondary"):
                st.session_state.presences = pd.DataFrame(
                    columns=["Agent","Date","Heure","Session","Statut"])
                st.success("Pointages effacés."); st.rerun()
        else:
            st.info("Aucun pointage enregistré.")

# ── EXPORT GLOBAL ─────────────────────────────────────────────────────────────
st.markdown("---")
buf_final = io.BytesIO()
with pd.ExcelWriter(buf_final, engine="openpyxl") as w:
    df.to_excel(w, sheet_name="Données brutes", index=False)
    df_stats.to_excel(w, sheet_name="Stats notes", index=False)
    df_stats.sort_values("Moyenne",ascending=False).to_excel(w,sheet_name="Classement",index=True)
    if len(st.session_state.presences) > 0:
        st.session_state.presences.to_excel(w, sheet_name="Pointages", index=False)
        presence_stats_only_pointed(agents).to_excel(w, sheet_name="Stats présences", index=False)
st.download_button("⬇️ Export complet (Excel — toutes feuilles)", buf_final.getvalue(),
    file_name="tableau_bord_formation.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.caption("Plateforme Formation · Notes & Présences · QR Code · v4.0")
