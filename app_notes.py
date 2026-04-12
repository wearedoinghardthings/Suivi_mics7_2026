import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io, qrcode, datetime, zipfile, base64
from PIL import Image
import streamlit.components.v1 as components

# ════════════════════════════════════════════════════════════════════════════
# ÉTAT PARTAGÉ — même objet pour TOUS les utilisateurs connectés
# ════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_shared():
    """
    Retourne le MÊME dictionnaire mutable à tous les sessions.
    Quand l'admin modifie shared["notes"] ou shared["presences"],
    TOUS les utilisateurs voient la mise à jour immédiatement.
    """
    return {
        "notes": None,           # None = données par défaut
        "notes_label": "Données par défaut",
        "presences": [],         # liste de dicts {Agent, Date, Heure, Session, Statut}
        "sessions_config": ["Jour 1 - Matin","Jour 1 - Après-midi",
                            "Jour 2 - Matin","Jour 2 - Après-midi","Jour 3 - Matin"],
    }

shared = get_shared()

# ════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Formation — Notes & Présences",
                   page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ── CSS responsive ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;background:#fff!important;color:#1a1a2e!important;}
.main,.block-container{background:#fff!important;padding-top:.8rem!important;}
section[data-testid="stSidebar"]{background:linear-gradient(160deg,#f0f4ff,#e8f0fe)!important;border-right:1px solid #dce4f5;}
section[data-testid="stSidebar"] *{color:#1a1a2e!important;}
.main-title{font-family:'DM Serif Display',serif;font-size:clamp(1.4rem,4vw,2rem);color:#2c3e7a;margin-bottom:.1rem;}
.sub-title{font-size:clamp(.78rem,2.5vw,.9rem);color:#6b7db3;margin-bottom:1rem;}
.kpi-card{background:#fff;border:1px solid #e0e8ff;border-radius:14px;padding:clamp(10px,2vw,16px);
  text-align:center;box-shadow:0 2px 10px rgba(44,62,122,.06);margin-bottom:6px;}
.kpi-value{font-size:clamp(1.3rem,3.5vw,1.7rem);font-weight:700;color:#2c3e7a;line-height:1.1;}
.kpi-label{font-size:clamp(.62rem,1.8vw,.74rem);color:#7a8db3;margin-top:4px;
  text-transform:uppercase;letter-spacing:.6px;font-weight:500;}
.kpi-sub{font-size:.68rem;color:#a0aec0;margin-top:2px;}
.section-title{font-family:'DM Serif Display',serif;font-size:clamp(1rem,3vw,1.2rem);
  color:#2c3e7a;margin-top:1.3rem;margin-bottom:.4rem;border-left:4px solid #4a6cf7;padding-left:11px;}
.stTabs [data-baseweb="tab-list"]{background:#f0f4ff;border-radius:10px;padding:4px;gap:3px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:500;color:#2c3e7a;
  padding:5px 10px;font-size:clamp(.7rem,2vw,.82rem);white-space:nowrap;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#4a6cf7!important;
  box-shadow:0 1px 6px rgba(74,108,247,.15);}
.stDownloadButton>button{background:linear-gradient(135deg,#4a6cf7,#7b5ea7)!important;
  color:#fff!important;border:none!important;border-radius:8px!important;
  font-weight:600!important;min-height:44px;}
.stButton>button{border-radius:8px!important;min-height:42px;font-size:clamp(.8rem,2.5vw,.9rem)!important;}
.badge-tb{background:#e6f4ea;color:#1e7e34;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-b{background:#dbeafe;color:#1a56db;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-ab{background:#fef3c7;color:#92400e;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-in{background:#fee2e2;color:#b91c1c;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.qr-grid{display:flex;flex-wrap:wrap;gap:10px;}
.qr-item{background:#fff;border:1px solid #e0e8ff;border-radius:10px;padding:8px;
  text-align:center;width:clamp(110px,22vw,140px);box-shadow:0 1px 6px rgba(44,62,122,.06);}
.qr-name{font-size:clamp(.6rem,1.8vw,.72rem);color:#2c3e7a;font-weight:600;
  margin-top:5px;line-height:1.3;word-break:break-word;}
.admin-locked{background:#faf5ff;border:1px solid #e9d5ff;border-radius:12px;padding:16px;margin:8px 0;}
.shared-banner{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
  padding:10px 14px;margin-bottom:8px;font-size:.85rem;color:#166534;}
@media(max-width:768px){
  .block-container{padding:.5rem .6rem 2rem!important;}
  .kpi-value{font-size:1.3rem!important;}
  .stTabs [data-baseweb="tab"]{padding:4px 7px!important;font-size:.68rem!important;}
  .qr-item{width:calc(50% - 10px)!important;}
}
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

def get_notes_df():
    """Retourne les notes actives (partagées ou défaut)."""
    if shared["notes"] is not None:
        return pd.DataFrame(shared["notes"])
    return pd.DataFrame(DEFAULT_DATA)

def get_presences_df():
    """Retourne les présences partagées sous forme de DataFrame."""
    if shared["presences"]:
        return pd.DataFrame(shared["presences"])
    return pd.DataFrame(columns=["Agent","Date","Heure","Session","Statut"])

# ════════════════════════════════════════════════════════════════════════════
# SESSION STATE (par utilisateur — UI uniquement)
# ════════════════════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        "camera_on":       False,
        "last_scan_agent": None,
        "last_scan_time":  None,
        "admin_logged_in": False,
        "session_active":  shared["sessions_config"][0],
        "selected_agents": [],
        "note_range":      (0.0, 20.0),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_session()

# ════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ════════════════════════════════════════════════════════════════════════════
def mention_info(n):
    if n>=16:  return "Très Bien","badge-tb"
    elif n>=14: return "Bien","badge-b"
    elif n>=10: return "Assez Bien","badge-ab"
    else:       return "Insuffisant","badge-in"

def get_note_cols(df): return [c for c in df.columns if c!=df.columns[0]]

def compute_stats(df, note_cols, name_col):
    rows=[]
    for _,row in df.iterrows():
        vals=[float(row[c]) for c in note_cols]
        moy=round(np.mean(vals),2); ml,_=mention_info(moy)
        rows.append({"Agent":row[name_col],"Moyenne":moy,"Max":max(vals),
                     "Min":min(vals),"Médiane":round(np.median(vals),2),
                     "Écart-type":round(np.std(vals),2),"Nb notes":len(vals),"Mention":ml})
    return pd.DataFrame(rows)

def style_note_row(row):
    return [("background-color:#e6f4ea;color:#1e7e34" if row[c]>=16 else
             "background-color:#dbeafe;color:#1a56db" if row[c]>=14 else
             "background-color:#fef3c7;color:#92400e" if row[c]>=10 else
             "background-color:#fee2e2;color:#b91c1c") if c in ["Moyenne","Max","Min","Médiane"]
            else "" for c in row.index]

def agent_to_qr_key(name): return f"AGENT::{name}"
def key_to_agent(key): return key.split("::",1)[1] if "::" in key else key

def add_presence_shared(agent, session, statut="Présent"):
    now = datetime.datetime.now()
    shared["presences"].append({
        "Agent":agent, "Date":now.strftime("%d/%m/%Y"),
        "Heure":now.strftime("%H:%M:%S"), "Session":session, "Statut":statut,
    })

def is_already_pointed(agent, session):
    today = datetime.date.today().strftime("%d/%m/%Y")
    for p in shared["presences"]:
        if p["Agent"]==agent and p["Session"]==session and p["Date"]==today:
            return True, p["Heure"]
    return False, None

def presence_stats(agents):
    pres_df = get_presences_df()
    sessions = shared["sessions_config"]
    rows=[]
    for agent in agents:
        ap = pres_df[pres_df["Agent"]==agent] if len(pres_df)>0 else pd.DataFrame()
        nb = len(ap["Session"].unique()) if len(ap)>0 else 0
        taux = round(nb/len(sessions)*100,1) if sessions else 0
        statut = ("Assidu" if taux>=80 else "Moyen" if taux>=50 else
                  "Faible" if nb>0 else "Non pointé")
        rows.append({"Agent":agent,"Présences":nb,"Sessions totales":len(sessions),
                     "Taux (%)":taux,"Statut":statut})
    return pd.DataFrame(rows)

def get_admin_pwd():
    try: return st.secrets["admin"]["password"]
    except: return "formation2026"

def load_gsheet(url):
    try:
        if "spreadsheets/d/" in url:
            sid=url.split("spreadsheets/d/")[1].split("/")[0]
            url=f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
        df=pd.read_csv(url); df.columns=df.columns.astype(str).str.strip()
        return df,None
    except Exception as e: return None,str(e)

# ════════════════════════════════════════════════════════════════════════════
# COMPOSANT SCANNER QR — HTML+JS natif, grande fenêtre, détection continue
# ════════════════════════════════════════════════════════════════════════════
QR_SCANNER_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'DM Sans',sans-serif; }
  body { background:#fff; padding:8px; }
  #video-container {
    position:relative; width:100%; max-width:500px;
    margin:0 auto; border-radius:12px; overflow:hidden;
    border:2px dashed #4a6cf7; background:#f8faff;
  }
  video { width:100%; display:block; }
  canvas { display:none; }
  #overlay {
    position:absolute; top:0; left:0; width:100%; height:100%;
    pointer-events:none;
  }
  #scan-line {
    position:absolute; left:10%; width:80%; height:3px;
    background:linear-gradient(90deg,transparent,#4a6cf7,transparent);
    border-radius:2px; animation:scan 2s ease-in-out infinite;
  }
  @keyframes scan { 0%,100%{top:15%} 50%{top:80%} }
  #corner-tl,#corner-tr,#corner-bl,#corner-br {
    position:absolute; width:28px; height:28px; border-color:#4a6cf7; border-style:solid;
  }
  #corner-tl{top:10px;left:10px;border-width:3px 0 0 3px}
  #corner-tr{top:10px;right:10px;border-width:3px 3px 0 0}
  #corner-bl{bottom:10px;left:10px;border-width:0 0 3px 3px}
  #corner-br{bottom:10px;right:10px;border-width:0 3px 3px 0}
  #status {
    text-align:center; padding:10px; font-size:14px;
    font-weight:500; color:#2c3e7a; min-height:40px;
    display:flex; align-items:center; justify-content:center; gap:8px;
  }
  #result-box {
    display:none; background:#f0fdf4; border:2px solid #bbf7d0;
    border-radius:10px; padding:14px; margin-top:8px; text-align:center;
  }
  #result-name { font-size:1.1rem; font-weight:700; color:#166534; }
  #result-time { font-size:.85rem; color:#4ade80; margin-top:4px; }
  #error-box {
    display:none; background:#fef2f2; border:2px solid #fecaca;
    border-radius:10px; padding:12px; margin-top:8px; text-align:center;
    font-size:.9rem; color:#b91c1c;
  }
  .dot { display:inline-block; width:10px; height:10px;
    background:#4a6cf7; border-radius:50%; animation:pulse .8s ease-in-out infinite; }
  @keyframes pulse { 0%,100%{opacity:.3;transform:scale(.8)} 50%{opacity:1;transform:scale(1.1)} }
  #hidden-input { position:absolute; opacity:0; pointer-events:none; width:1px; height:1px; }
</style>
</head>
<body>
<div id="video-container">
  <video id="video" autoplay playsinline muted></video>
  <canvas id="canvas"></canvas>
  <div id="overlay">
    <div id="scan-line"></div>
    <div id="corner-tl"></div><div id="corner-tr"></div>
    <div id="corner-bl"></div><div id="corner-br"></div>
  </div>
</div>
<div id="status"><span class="dot"></span> Démarrage de la caméra…</div>
<div id="result-box">
  <div id="result-name"></div>
  <div id="result-time"></div>
</div>
<div id="error-box" id="error-msg"></div>
<input type="text" id="hidden-input" readonly>
<script>
const video   = document.getElementById('video');
const canvas  = document.getElementById('canvas');
const ctx     = canvas.getContext('2d');
const status  = document.getElementById('status');
const resultBox  = document.getElementById('result-box');
const resultName = document.getElementById('result-name');
const resultTime = document.getElementById('result-time');
const errorBox   = document.getElementById('error-box');
const hiddenInput = document.getElementById('hidden-input');

let lastSent = '';
let cooldown = false;
let scanning = true;

async function startCamera() {
  try {
    const constraints = {
      video: {
        facingMode: { ideal: 'environment' },
        width:  { ideal: 1280 },
        height: { ideal: 720 }
      }
    };
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = stream;
    video.onloadedmetadata = () => {
      canvas.width  = video.videoWidth  || 640;
      canvas.height = video.videoHeight || 480;
      status.innerHTML = '<span class="dot"></span> Caméra prête — présentez un QR code';
      requestAnimationFrame(tick);
    };
  } catch(e) {
    status.textContent = '❌ Accès caméra refusé';
    errorBox.style.display='block';
    errorBox.textContent = 'Autorisez l\'accès à la caméra dans votre navigateur.';
  }
}

function tick() {
  if (!scanning) return;
  if (video.readyState === video.HAVE_ENOUGH_DATA) {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert'
    });
    if (code && code.data && code.data !== lastSent && !cooldown) {
      lastSent = code.data;
      cooldown = true;
      const agentName = code.data.startsWith('AGENT::')
        ? code.data.slice(7) : code.data;
      const now = new Date().toLocaleTimeString('fr-FR');
      resultName.textContent = '✅ ' + agentName;
      resultTime.textContent  = 'Pointé à ' + now;
      resultBox.style.display = 'block';
      errorBox.style.display  = 'none';
      status.innerHTML = '⏳ Prêt pour le prochain QR code…';
      // Envoyer à Streamlit via Streamlit Components protocol
      window.parent.postMessage({
        type: 'streamlit:setComponentValue',
        value: code.data
      }, '*');
      // Réinitialiser après 3 secondes
      setTimeout(() => {
        lastSent = '';
        cooldown = false;
        resultBox.style.display = 'none';
        status.innerHTML = '<span class="dot"></span> En attente d\'un QR code…';
      }, 3000);
    }
  }
  requestAnimationFrame(tick);
}

startCamera();
</script>
</body>
</html>
"""

# ════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DONNÉES (lecture seule pour utilisateurs)
# ════════════════════════════════════════════════════════════════════════════
df        = get_notes_df()
name_col  = df.columns[0]
note_cols = get_note_cols(df)
agents    = df[name_col].tolist()
df_stats  = compute_stats(df, note_cols, name_col)
all_vals  = df[note_cols].values.flatten().astype(float)
pres_df   = get_presences_df()

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Bandeau source active
    st.markdown(f'<div class="shared-banner">📡 Source active : <b>{shared["notes_label"]}</b><br>'
                f'<small>{len(agents)} agents · {len(note_cols)} évaluations</small></div>',
                unsafe_allow_html=True)
    st.markdown("### 🗓️ Session active")
    if st.session_state.session_active not in shared["sessions_config"]:
        st.session_state.session_active = shared["sessions_config"][0]
    st.session_state.session_active = st.selectbox(
        "Session", shared["sessions_config"],
        index=shared["sessions_config"].index(st.session_state.session_active),
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### 🔍 Filtres")
    selected_agents = st.multiselect("Agents (courbes)", options=agents,
                                      default=agents[:5] if agents else [])
    note_range = st.slider("Filtre moyenne", 0.0, 20.0, (0.0,20.0), 0.5)
    st.markdown("---")
    nb_pts = len(pres_df)
    nb_sess = len(pres_df[pres_df["Session"]==st.session_state.session_active]["Agent"].unique()) if nb_pts>0 else 0
    st.metric("Total pointages", nb_pts)
    st.metric(f"Présents session", nb_sess)

# ════════════════════════════════════════════════════════════════════════════
# EN-TÊTE
# ════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="main-title">📊 Formation — Notes & Présences</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{len(agents)} agents · {len(note_cols)} évaluations · '
            f'Source : <b>{shared["notes_label"]}</b> · Session : <b>{st.session_state.session_active}</b></div>',
            unsafe_allow_html=True)

k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_list = [
    (round(np.mean(all_vals),2), "Moyenne Générale","toutes notes"),
    (len(agents),                "Agents inscrits","total"),
    (nb_sess,                    "Présents","session active"),
    (len(agents)-nb_sess,        "Non pointés","session active"),
    (int((df[note_cols]==20).sum().sum()),"Notes 20/20","parfaits"),
    (nb_pts,                     "Total pointages","enregistrés"),
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
 tab_heatmap, tab_podium, tab_admin) = st.tabs([
    "📷 Pointage",
    "🎫 QR Codes",
    "👥 Présences",
    "🔗 Notes × Présences",
    "📈 Courbes",
    "🌐 Tendance",
    "📋 Stats",
    "🔥 Heatmap",
    "🏆 Classement",
    "🔐 Admin",
])

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET POINTAGE
# ─────────────────────────────────────────────────────────────────────────────
with tab_scan:
    st.markdown('<div class="section-title">📷 Pointage des présences</div>', unsafe_allow_html=True)
    st.markdown(f"**Session :** `{st.session_state.session_active}`")

    col_cam, col_manual = st.columns([1.2, 1])

    with col_cam:
        st.markdown("**Scan QR Code — détection automatique**")

        # Bouton Ouvrir/Fermer
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
            # Afficher dernier scan réussi
            if st.session_state.last_scan_agent:
                st.success(f"✅ Dernier pointage : **{st.session_state.last_scan_agent}** "
                           f"à {st.session_state.last_scan_time}")

            # Scanner HTML natif — grande fenêtre
            qr_value = components.html(QR_SCANNER_HTML, height=420, scrolling=False)

            # Traitement du QR détecté
            if qr_value:
                agent_found = key_to_agent(str(qr_value))
                if agent_found in agents:
                    deja, heure = is_already_pointed(agent_found, st.session_state.session_active)
                    if not deja:
                        add_presence_shared(agent_found, st.session_state.session_active)
                        st.session_state.last_scan_agent = agent_found
                        st.session_state.last_scan_time  = datetime.datetime.now().strftime("%H:%M:%S")
                        st.rerun()
                    else:
                        st.info(f"ℹ️ **{agent_found}** déjà pointé à {heure}")
                else:
                    st.error(f"❌ Agent non reconnu : `{agent_found}`")

    with col_manual:
        st.markdown("**Pointage manuel**")
        with st.form("form_manual"):
            agent_sel  = st.selectbox("Agent", agents)
            statut_sel = st.selectbox("Statut", ["Présent","En retard","Excusé"])
            ok = st.form_submit_button("✅ Enregistrer", use_container_width=True)
            if ok:
                deja, heure = is_already_pointed(agent_sel, st.session_state.session_active)
                if not deja:
                    add_presence_shared(agent_sel, st.session_state.session_active, statut_sel)
                    st.success(f"✅ **{agent_sel}** — {statut_sel}")
                    st.rerun()
                else:
                    st.info(f"ℹ️ Déjà pointé à {heure}")

    # Journal du jour
    st.markdown('<div class="section-title">📋 Journal de la session</div>', unsafe_allow_html=True)
    today = datetime.date.today().strftime("%d/%m/%Y")
    pres_df2 = get_presences_df()
    jour_df = pres_df2[(pres_df2["Session"]==st.session_state.session_active) &
                        (pres_df2["Date"]==today)].sort_values("Heure",ascending=False).reset_index(drop=True)
    if len(jour_df) > 0:
        st.dataframe(jour_df, use_container_width=True, hide_index=True, height=300)
        buf_j = io.BytesIO()
        jour_df.to_csv(buf_j, index=False, encoding="utf-8-sig")
        st.download_button("⬇️ Exporter ce journal", buf_j.getvalue(),
            file_name=f"journal_{st.session_state.session_active[:10]}.csv", mime="text/csv")
    else:
        st.info("Aucun pointage pour cette session aujourd'hui.")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET QR CODES
# ─────────────────────────────────────────────────────────────────────────────
with tab_qr:
    st.markdown('<div class="section-title">🎫 Génération des badges QR</div>', unsafe_allow_html=True)
    st.caption(f"{len(agents)} agents · 1 QR code unique par agent")
    agents_sel = st.multiselect("Agents (vide = tous)", options=agents, placeholder="Tous les agents")
    qr_size = st.selectbox("Taille", ["Petite","Normale","Grande"], index=1)
    qr_box = {"Petite":4,"Normale":6,"Grande":8}[qr_size]
    agents_gen = agents_sel if agents_sel else agents

    if st.button(f"🔄 Générer {len(agents_gen)} QR Code(s)", type="primary", use_container_width=True):
        zip_buf = io.BytesIO()
        previews = []
        with zipfile.ZipFile(zip_buf,"w",zipfile.ZIP_DEFLATED) as zf:
            prog = st.progress(0, text="Génération…")
            for i, agent in enumerate(agents_gen):
                qr_obj = qrcode.QRCode(version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=qr_box, border=3)
                qr_obj.add_data(agent_to_qr_key(agent)); qr_obj.make(fit=True)
                img = qr_obj.make_image(fill_color="#2c3e7a", back_color="white")
                buf = io.BytesIO(); img.save(buf,format="PNG"); buf.seek(0); raw=buf.getvalue()
                zf.writestr(f"QR_Badges/{agent[:60].replace('/','_')}.png", raw)
                previews.append({"name":agent,"b64":base64.b64encode(raw).decode()})
                prog.progress((i+1)/len(agents_gen), text=f"{i+1}/{len(agents_gen)}")
            prog.empty()
        zip_buf.seek(0)
        st.success(f"✅ {len(agents_gen)} QR codes générés !")
        st.download_button(f"⬇️ Télécharger le ZIP ({len(agents_gen)} badges)",
            data=zip_buf.getvalue(), file_name="QR_Badges_Formation.zip",
            mime="application/zip", use_container_width=True)
        html_g='<div class="qr-grid">'
        for p in previews:
            html_g+=(f'<div class="qr-item"><img src="data:image/png;base64,{p["b64"]}" '
                     f'style="width:100%;border-radius:5px">'
                     f'<div class="qr-name">{p["name"][:35]}</div></div>')
        st.markdown(html_g+'</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET PRÉSENCES
# ─────────────────────────────────────────────────────────────────────────────
with tab_pres:
    st.markdown('<div class="section-title">👥 Statistiques de présence</div>', unsafe_allow_html=True)
    pres_df3 = get_presences_df()
    if len(pres_df3) == 0:
        st.info("Aucun pointage enregistré. Utilisez l'onglet **📷 Pointage**.")
    else:
        df_ps = presence_stats(agents)
        nb_p = len(df_ps[df_ps["Présences"]>0])
        taux_m = round(df_ps[df_ps["Présences"]>0]["Taux (%)"].mean(),1) if nb_p>0 else 0
        pa,pb,pc,pd_ = st.columns(4)
        for col,(val,label,sub) in zip([pa,pb,pc,pd_],[
            (f"{taux_m}%","Taux moyen","agents pointés"),
            (nb_p,"Agents pointés","au moins 1 fois"),
            (len(df_ps[df_ps["Statut"]=="Assidu"]),"Assidus ≥80%","agents"),
            (len(pres_df3),"Total pointages","enregistrés"),
        ]):
            col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
                         f'<div class="kpi-label">{label}</div><div class="kpi-sub">{sub}</div></div>',
                         unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        df_s = df_ps[df_ps["Présences"]>0].sort_values("Taux (%)",ascending=True)
        if len(df_s) > 0:
            colors_p = ["#27ae60" if t>=80 else "#f39c12" if t>=50 else "#e74c3c" for t in df_s["Taux (%)"]]
            fig_p = go.Figure(go.Bar(x=df_s["Taux (%)"],y=df_s["Agent"],orientation="h",
                marker=dict(color=colors_p,line=dict(color="white",width=0.5)),
                text=[f"{v}%" for v in df_s["Taux (%)"]],textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x}%<extra></extra>"))
            fig_p.update_layout(paper_bgcolor="white",plot_bgcolor="white",
                font=dict(family="DM Sans",color="#2c3e7a"),
                xaxis=dict(range=[0,118],gridcolor="#f0f4ff"),
                yaxis=dict(autorange="reversed",tickfont=dict(size=10)),
                height=max(360,len(df_s)*30),margin=dict(t=20,b=40,l=230,r=60),showlegend=False,
                shapes=[dict(type="line",xref="x",x0=80,x1=80,yref="paper",y0=0,y1=1,
                             line=dict(color="#27ae60",width=1.5,dash="dot"))])
            st.plotly_chart(fig_p, use_container_width=True)
        def spr(row):
            return [("background-color:#e6f4ea;color:#1e7e34" if row[c]>=80 else
                     "background-color:#fef3c7;color:#92400e" if row[c]>=50 else
                     "background-color:#fee2e2;color:#b91c1c" if row[c]>0 else
                     "background-color:#f9fafb;color:#9ca3af") if c=="Taux (%)" else ""
                    for c in row.index]
        st.dataframe(df_ps.sort_values("Taux (%)",ascending=False).reset_index(drop=True)
                     .style.apply(spr,axis=1).format({"Taux (%)":"{:.1f}%"}),
                     use_container_width=True,height=400)
        buf_p=io.BytesIO()
        with pd.ExcelWriter(buf_p,engine="openpyxl") as w:
            pres_df3.to_excel(w,sheet_name="Pointages",index=False)
            df_ps.to_excel(w,sheet_name="Stats présences",index=False)
        st.download_button("⬇️ Exporter présences (Excel)",buf_p.getvalue(),
            file_name="presences.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET CROISEMENT
# ─────────────────────────────────────────────────────────────────────────────
with tab_croise:
    st.markdown('<div class="section-title">🔗 Croisement Notes × Présences</div>',unsafe_allow_html=True)
    pres_df4 = get_presences_df()
    if len(pres_df4)==0:
        st.info("Enregistrez des présences pour activer cette analyse.")
    else:
        df_ps2=presence_stats(agents)
        df_cx=df_stats.merge(df_ps2[["Agent","Taux (%)","Présences","Statut"]],on="Agent",how="left")
        df_cx["Taux (%)"]=df_cx["Taux (%)"].fillna(0)
        df_cx["Statut présence"]=df_cx["Statut"].fillna("Non pointé")
        cm={"Assidu":"#27ae60","Moyen":"#f39c12","Faible":"#e74c3c","Non pointé":"#9ca3af"}
        fig_sc=go.Figure()
        for sv,color in cm.items():
            sub=df_cx[df_cx["Statut présence"]==sv]
            if len(sub)>0:
                fig_sc.add_trace(go.Scatter(x=sub["Taux (%)"],y=sub["Moyenne"],
                    mode="markers+text",name=sv,
                    marker=dict(size=12,color=color,opacity=0.8,line=dict(color="white",width=1.5)),
                    text=sub["Agent"].str.split().str[0],textposition="top center",
                    textfont=dict(size=9),
                    hovertemplate="<b>%{text}</b><br>Présence:%{x}%<br>Moy:%{y:.2f}<extra></extra>"))
        pts_r=df_cx[df_cx["Taux (%)"]>0]
        if len(pts_r)>3:
            try:
                z=np.polyfit(pts_r["Taux (%)"],pts_r["Moyenne"],1); p=np.poly1d(z)
                xl=np.linspace(0,100,50)
                fig_sc.add_trace(go.Scatter(x=xl,y=p(xl),mode="lines",name="Tendance",
                    line=dict(color="#4a6cf7",width=2,dash="dash"),hoverinfo="skip"))
                corr=round(pts_r["Taux (%)"].corr(pts_r["Moyenne"]),3)
                st.info(f"**Corrélation présence / notes : {corr}**")
            except: pass
        fig_sc.update_layout(paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Taux présence (%)",range=[-5,110],gridcolor="#f0f4ff"),
            yaxis=dict(title="Moyenne /20",range=[0,21],gridcolor="#f0f4ff"),
            height=460,margin=dict(t=40,b=40,l=50,r=20))
        st.plotly_chart(fig_sc,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLETS NOTES
# ─────────────────────────────────────────────────────────────────────────────
with tab_notes:
    st.markdown('<div class="section-title">📈 Évolution individuelle</div>',unsafe_allow_html=True)
    if not selected_agents:
        st.info("👈 Sélectionnez des agents dans le panneau latéral.")
    else:
        pal=(px.colors.qualitative.Pastel+px.colors.qualitative.Safe
             +px.colors.qualitative.Vivid+px.colors.qualitative.Dark24)
        fig=go.Figure()
        for i,agent in enumerate(selected_agents):
            row=df[df[name_col]==agent].iloc[0]
            notes=[float(row[c]) for c in note_cols]; c=pal[i%len(pal)]
            fig.add_trace(go.Scatter(x=note_cols,y=notes,mode="lines+markers+text",name=agent,
                line=dict(color=c,width=2.5,shape="spline"),
                marker=dict(size=9,color=c,line=dict(color="white",width=1.5)),
                text=[str(int(n)) for n in notes],textposition="top center",textfont=dict(size=9,color=c),
                hovertemplate=f"<b>{agent}</b><br>%{{x}} : <b>%{{y}}</b>/20<extra></extra>"))
        fig.update_layout(paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Évaluation",gridcolor="#f0f4ff"),
            yaxis=dict(title="Note /20",range=[-0.5,21],gridcolor="#f0f4ff"),
            legend=dict(bgcolor="rgba(255,255,255,.95)",bordercolor="#dce4f5",borderwidth=1),
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
    fig2.add_trace(go.Scatter(x=note_cols,y=med_e,mode="lines+markers",name="Médiane",
        line=dict(color="#7b5ea7",width=2,dash="dash",shape="spline"),marker=dict(size=7,color="#7b5ea7")))
    fig2.add_trace(go.Scatter(x=note_cols,y=moy_e,mode="lines+markers+text",name="Moyenne",
        line=dict(color="#4a6cf7",width=3,shape="spline"),
        marker=dict(size=10,color="#4a6cf7",line=dict(color="white",width=2)),
        text=[f"{v:.1f}" for v in moy_e],textposition="top center",textfont=dict(size=10,color="#2c3e7a")))
    fig2.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(title="Évaluation",gridcolor="#f0f4ff"),
        yaxis=dict(title="Note /20",range=[-0.5,21],gridcolor="#f0f4ff"),
        hovermode="x unified",height=420,margin=dict(t=30,b=40,l=50,r=20))
    st.plotly_chart(fig2,use_container_width=True)

with tab_stats:
    st.markdown('<div class="section-title">📋 Stats par agent</div>',unsafe_allow_html=True)
    df_f=df_stats[(df_stats["Moyenne"]>=note_range[0])&(df_stats["Moyenne"]<=note_range[1])]\
         .sort_values("Moyenne",ascending=False).reset_index(drop=True)
    df_f.index+=1
    st.dataframe(df_f.style.apply(style_note_row,axis=1).format(
        {"Moyenne":"{:.2f}","Médiane":"{:.2f}","Écart-type":"{:.2f}","Max":"{:.0f}","Min":"{:.0f}"}),
        use_container_width=True,height=500)

with tab_heatmap:
    st.markdown('<div class="section-title">🔥 Carte de chaleur</div>',unsafe_allow_html=True)
    heat=df.set_index(name_col)[note_cols].astype(float)
    fig5=go.Figure(go.Heatmap(z=heat.values,x=note_cols,y=heat.index.tolist(),
        colorscale=[[0,"#fee2e2"],[0.001,"#fecaca"],[0.3,"#bfdbfe"],[0.6,"#4a6cf7"],[1,"#1a237e"]],
        text=heat.values.astype(int),texttemplate="%{text}",textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>%{x} : <b>%{z}</b>/20<extra></extra>",
        colorbar=dict(title="Note"),zmin=0,zmax=20))
    fig5.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(side="top"),yaxis=dict(autorange="reversed"),
        height=max(400,len(agents)*28),margin=dict(t=50,b=20,l=240,r=20))
    st.plotly_chart(fig5,use_container_width=True)

with tab_podium:
    st.markdown('<div class="section-title">🏆 Classement</div>',unsafe_allow_html=True)
    df_rk=df_stats.sort_values("Moyenne",ascending=False).reset_index(drop=True); df_rk.index+=1
    if len(df_rk)>=3:
        p2,p1,p3=st.columns([1,1.2,1])
        for col,rank,medal,bg in [(p1,1,"🥇","#FFF9C4"),(p2,2,"🥈","#F5F5F5"),(p3,3,"🥉","#FBE9E7")]:
            r=df_rk.iloc[rank-1]; ml,mc=mention_info(r["Moyenne"])
            col.markdown(f'<div style="background:{bg};border-radius:16px;padding:16px;text-align:center;'
                         f'box-shadow:0 4px 16px rgba(0,0,0,.07);">'
                         f'<div style="font-size:2rem;">{medal}</div>'
                         f'<div style="font-weight:700;color:#2c3e7a;font-size:.9rem;margin-top:4px;">{r["Agent"]}</div>'
                         f'<div style="font-size:1.8rem;font-weight:700;color:#4a6cf7;">{r["Moyenne"]:.2f}</div>'
                         f'<span class="{mc}">{ml}</span></div>',unsafe_allow_html=True)
    colors_b=["#2d6a4f" if m>=16 else "#1a56db" if m>=14 else "#92400e" if m>=10 else "#b91c1c"
              for m in df_rk["Moyenne"]]
    fig_b=go.Figure(go.Bar(x=df_rk["Moyenne"],y=df_rk["Agent"],orientation="h",
        marker=dict(color=colors_b,line=dict(color="white",width=0.5)),
        text=[f"{v:.2f}" for v in df_rk["Moyenne"]],textposition="outside"))
    fig_b.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(range=[0,23],gridcolor="#f0f4ff"),yaxis=dict(autorange="reversed",tickfont=dict(size=10)),
        height=max(400,len(agents)*28),margin=dict(t=20,b=40,l=230,r=60),showlegend=False)
    st.plotly_chart(fig_b,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET ADMIN
# ─────────────────────────────────────────────────────────────────────────────
with tab_admin:
    st.markdown('<div class="section-title">🔐 Espace Administrateur</div>',unsafe_allow_html=True)

    if not st.session_state.admin_logged_in:
        st.markdown('<div class="admin-locked">',unsafe_allow_html=True)
        pwd = st.text_input("Mot de passe administrateur", type="password")
        if st.button("🔓 Se connecter", use_container_width=True):
            if pwd == get_admin_pwd():
                st.session_state.admin_logged_in = True
                st.success("✅ Connexion admin réussie"); st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
        st.markdown('</div>',unsafe_allow_html=True)
        st.info("🔒 Import des données, gestion des sessions et pointages : accès admin requis.")
    else:
        cola, colb = st.columns([1,1])
        with cola:
            st.markdown(f"✅ **Connecté en admin**")
        with colb:
            if st.button("🚪 Déconnexion", use_container_width=True):
                st.session_state.admin_logged_in = False; st.rerun()

        st.markdown("---")

        # ── IMPORT NOTES (devient source pour TOUS) ───────────────────────
        st.markdown('<div class="section-title">📊 Importer les notes (visible par tous)</div>',
                    unsafe_allow_html=True)
        st.caption("Une fois importé, TOUS les utilisateurs connectés verront ces données immédiatement.")

        src_admin = st.radio("Source", ["📁 Fichier Excel","🔗 Google Sheets"], horizontal=True)

        if "Excel" in src_admin:
            f_notes = st.file_uploader("Fichier Excel des notes", type=["xlsx","xls"], key="adm_notes")
            if f_notes and st.button("✅ Publier ces notes pour tous", type="primary", use_container_width=True):
                try:
                    df_new = pd.read_excel(f_notes)
                    df_new.columns = df_new.columns.astype(str).str.strip()
                    shared["notes"] = df_new.to_dict("records")
                    shared["notes_label"] = f"Excel importé par admin ({df_new.shape[0]} agents)"
                    st.success(f"✅ Données publiées ! {df_new.shape[0]} agents · {df_new.shape[1]-1} notes — visible par tous.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            url_admin = st.text_input("URL Google Sheets",
                placeholder="https://docs.google.com/spreadsheets/d/...")
            if st.button("✅ Publier ces notes pour tous", type="primary", use_container_width=True):
                if url_admin:
                    df_new, err = load_gsheet(url_admin)
                    if err:
                        st.error(err)
                    else:
                        shared["notes"] = df_new.to_dict("records")
                        shared["notes_label"] = f"Google Sheets ({df_new.shape[0]} agents)"
                        st.success(f"✅ Données Google Sheets publiées ! {df_new.shape[0]} agents.")
                        st.rerun()

        # Réinitialiser aux données par défaut
        if shared["notes"] is not None:
            if st.button("🔄 Revenir aux données par défaut", type="secondary"):
                shared["notes"] = None
                shared["notes_label"] = "Données par défaut"
                st.success("Données par défaut rétablies."); st.rerun()

        st.markdown("---")

        # ── SESSIONS ──────────────────────────────────────────────────────
        st.markdown('<div class="section-title">🗓️ Configuration des sessions</div>',unsafe_allow_html=True)
        sessions_txt = st.text_area("Sessions (1 par ligne)",
            value="\n".join(shared["sessions_config"]), height=160)
        if st.button("💾 Sauvegarder les sessions"):
            ns = [s.strip() for s in sessions_txt.split("\n") if s.strip()]
            if ns:
                shared["sessions_config"] = ns
                st.success(f"✅ {len(ns)} sessions configurées pour tous."); st.rerun()

        st.markdown("---")

        # ── POINTAGES ─────────────────────────────────────────────────────
        st.markdown('<div class="section-title">📋 Gestion des pointages partagés</div>',unsafe_allow_html=True)
        pres_adm = get_presences_df()
        if len(pres_adm) > 0:
            st.dataframe(pres_adm, use_container_width=True, height=260)
            ca, cb, cc = st.columns(3)
            with ca:
                buf_a = io.BytesIO()
                pres_adm.to_csv(buf_a, index=False, encoding="utf-8-sig")
                st.download_button("⬇️ Export CSV", buf_a.getvalue(),
                    file_name="pointages.csv", mime="text/csv", use_container_width=True)
            with cb:
                buf_b = io.BytesIO()
                with pd.ExcelWriter(buf_b, engine="openpyxl") as w:
                    pres_adm.to_excel(w, sheet_name="Pointages", index=False)
                st.download_button("⬇️ Export Excel", buf_b.getvalue(),
                    file_name="pointages.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            with cc:
                if st.button("🗑️ Effacer tout", type="secondary", use_container_width=True):
                    shared["presences"].clear()
                    st.success("Pointages effacés."); st.rerun()
        else:
            st.info("Aucun pointage.")

        # Import CSV pointages
        st.markdown("**Importer des pointages (CSV)**")
        f_pres = st.file_uploader("CSV de pointages", type=["csv"], key="adm_pres")
        if f_pres and st.button("✅ Fusionner ces pointages", use_container_width=True):
            try:
                df_pi = pd.read_csv(f_pres)
                required = {"Agent","Date","Heure","Session","Statut"}
                if required.issubset(set(df_pi.columns)):
                    before = len(shared["presences"])
                    existing = {(p["Agent"],p["Date"],p["Session"]) for p in shared["presences"]}
                    added = 0
                    for _, row in df_pi.iterrows():
                        key = (row["Agent"], row["Date"], row["Session"])
                        if key not in existing:
                            shared["presences"].append(row.to_dict())
                            existing.add(key); added += 1
                    st.success(f"✅ {added} nouveaux pointages ajoutés (total : {len(shared['presences'])}).")
                    st.rerun()
                else:
                    st.error(f"Colonnes requises : {required}")
            except Exception as e:
                st.error(str(e))

# ── EXPORT GLOBAL ─────────────────────────────────────────────────────────────
st.markdown("---")
buf_fin = io.BytesIO()
with pd.ExcelWriter(buf_fin, engine="openpyxl") as w:
    df.to_excel(w, sheet_name="Données notes", index=False)
    df_stats.to_excel(w, sheet_name="Stats notes", index=False)
    pres_f = get_presences_df()
    if len(pres_f)>0:
        pres_f.to_excel(w, sheet_name="Pointages", index=False)
        presence_stats(agents).to_excel(w, sheet_name="Stats présences", index=False)
st.download_button("⬇️ Export complet (Excel)", buf_fin.getvalue(),
    file_name="formation_complet.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.caption("Plateforme Formation · Notes & Présences · v5.0 · Données partagées en temps réel")
