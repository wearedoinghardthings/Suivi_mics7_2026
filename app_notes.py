import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io, qrcode, datetime, zipfile, base64
from PIL import Image

try:
    from pyzbar.pyzbar import decode as qr_decode
    QR_SCAN_OK = True
except Exception:
    QR_SCAN_OK = False

# ════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Tableau de Bord — Notes & Présences",
    page_icon="📊", layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;background:#fff!important;color:#1a1a2e;}
.main,.block-container{background:#fff!important;padding-top:1rem;}
section[data-testid="stSidebar"]{background:linear-gradient(160deg,#f0f4ff,#e8f0fe);border-right:1px solid #dce4f5;}
.main-title{font-family:'DM Serif Display',serif;font-size:2rem;color:#2c3e7a;margin-bottom:.1rem;}
.sub-title{font-size:.9rem;color:#6b7db3;margin-bottom:1rem;}
.kpi-card{background:#fff;border:1px solid #e0e8ff;border-radius:14px;padding:14px 16px;text-align:center;box-shadow:0 2px 10px rgba(44,62,122,.06);}
.kpi-value{font-size:1.7rem;font-weight:700;color:#2c3e7a;line-height:1;}
.kpi-label{font-size:.74rem;color:#7a8db3;margin-top:4px;text-transform:uppercase;letter-spacing:.7px;font-weight:500;}
.kpi-sub{font-size:.68rem;color:#a0aec0;margin-top:2px;}
.section-title{font-family:'DM Serif Display',serif;font-size:1.2rem;color:#2c3e7a;margin-top:1.3rem;margin-bottom:.4rem;border-left:4px solid #4a6cf7;padding-left:11px;}
.stTabs [data-baseweb="tab-list"]{background:#f0f4ff;border-radius:10px;padding:4px;gap:3px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:500;color:#2c3e7a;padding:6px 13px;font-size:.83rem;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#4a6cf7!important;box-shadow:0 1px 6px rgba(74,108,247,.15);}
.stDownloadButton>button{background:linear-gradient(135deg,#4a6cf7,#7b5ea7);color:#fff;border:none;border-radius:8px;font-weight:600;padding:8px 16px;}
.badge-tb{background:#e6f4ea;color:#1e7e34;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-b{background:#dbeafe;color:#1a56db;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-ab{background:#fef3c7;color:#92400e;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-in{background:#fee2e2;color:#b91c1c;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.scan-box{background:#f8faff;border:2px dashed #4a6cf7;border-radius:14px;padding:20px;text-align:center;margin:10px 0;}
.success-point{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:14px;text-align:center;margin:8px 0;}
.qr-grid{display:flex;flex-wrap:wrap;gap:12px;justify-content:flex-start;}
.qr-item{background:#fff;border:1px solid #e0e8ff;border-radius:10px;padding:10px;text-align:center;width:140px;box-shadow:0 1px 6px rgba(44,62,122,.06);}
.qr-name{font-size:.72rem;color:#2c3e7a;font-weight:600;margin-top:6px;line-height:1.3;word-break:break-word;}
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
        "presences": pd.DataFrame(columns=["Agent","Date","Heure","Session","Statut"]),
        "data_source": "default",
        "gsheet_url": "",
        "sessions_config": ["Jour 1 - Matin","Jour 1 - Après-midi","Jour 2 - Matin",
                            "Jour 2 - Après-midi","Jour 3 - Matin"],
        "session_active": "Jour 1 - Matin",
        "last_scan": None,
        "scan_message": "",
        "df_cache": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# ════════════════════════════════════════════════════════════════════════════
# FONCTIONS
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
        moy=round(np.mean(vals),2)
        ml,_=mention_info(moy)
        rows.append({"Agent":row[name_col],"Moyenne":moy,"Max":max(vals),
                     "Min":min(vals),"Médiane":round(np.median(vals),2),
                     "Écart-type":round(np.std(vals),2),"Nb notes":len(vals),"Mention":ml})
    return pd.DataFrame(rows)

def style_row(row):
    styles=[]
    for col in row.index:
        if col in ["Moyenne","Max","Min","Médiane"]:
            v=row[col]
            if v>=16:   styles.append("background-color:#e6f4ea;color:#1e7e34")
            elif v>=14: styles.append("background-color:#dbeafe;color:#1a56db")
            elif v>=10: styles.append("background-color:#fef3c7;color:#92400e")
            else:       styles.append("background-color:#fee2e2;color:#b91c1c")
        else: styles.append("")
    return styles

def make_qr_bytes(text):
    qr=qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=6,border=3)
    qr.add_data(text); qr.make(fit=True)
    img=qr.make_image(fill_color="#2c3e7a",back_color="white")
    buf=io.BytesIO(); img.save(buf,format="PNG"); buf.seek(0)
    return buf.getvalue()

def agent_to_qr_key(name):
    """Encode stable dans le QR : préfixe + nom."""
    return f"AGENT::{name}"

def key_to_agent(key):
    if "::" in key:
        return key.split("::",1)[1]
    return key

def decode_qr_from_image(pil_image):
    if not QR_SCAN_OK:
        return None
    try:
        decoded=qr_decode(pil_image)
        if decoded:
            return key_to_agent(decoded[0].data.decode("utf-8"))
    except Exception:
        pass
    return None

def add_presence(agent, session, statut="Présent"):
    now=datetime.datetime.now()
    new_row=pd.DataFrame([{
        "Agent":agent,
        "Date":now.strftime("%d/%m/%Y"),
        "Heure":now.strftime("%H:%M:%S"),
        "Session":session,
        "Statut":statut,
    }])
    st.session_state.presences=pd.concat(
        [st.session_state.presences,new_row],ignore_index=True)

def load_gsheet(url):
    try:
        if "spreadsheets/d/" in url:
            sid=url.split("spreadsheets/d/")[1].split("/")[0]
            csv_url=f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
        else:
            csv_url=url
        df=pd.read_csv(csv_url)
        df.columns=df.columns.astype(str).str.strip()
        return df,None
    except Exception as e:
        return None,str(e)

def presence_stats(agents):
    pres=st.session_state.presences
    sessions=st.session_state.sessions_config
    rows=[]
    for agent in agents:
        ap=pres[pres["Agent"]==agent]
        sessions_done=ap["Session"].unique().tolist()
        nb_present=len(sessions_done)
        nb_total=len(sessions)
        taux=round(nb_present/nb_total*100,1) if nb_total>0 else 0
        rows.append({
            "Agent":agent,
            "Présences":nb_present,
            "Sessions totales":nb_total,
            "Taux (%)":taux,
            "Statut":"Assidu" if taux>=80 else ("Moyen" if taux>=50 else "Absent"),
        })
    return pd.DataFrame(rows)

# ════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DONNÉES
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Source des données")
    source_choice=st.radio("Source",["📌 Données par défaut","📁 Fichier Excel","🔗 Google Sheets"],
        label_visibility="collapsed")
    uploaded_file=None
    if "Excel" in source_choice:
        st.session_state.data_source="excel"
        uploaded_file=st.file_uploader("Excel",type=["xlsx","xls"],label_visibility="collapsed")
    elif "Google" in source_choice:
        st.session_state.data_source="gsheet"
        st.session_state.gsheet_url=st.text_input(
            "URL Google Sheets",value=st.session_state.gsheet_url,
            placeholder="https://docs.google.com/spreadsheets/d/...")
    else:
        st.session_state.data_source="default"
    st.markdown("---")

@st.cache_data(ttl=60)
def fetch_gsheet(url): return load_gsheet(url)

if st.session_state.data_source=="excel" and uploaded_file:
    try:
        df=pd.read_excel(uploaded_file)
        df.columns=df.columns.astype(str).str.strip()
        st.sidebar.success(f"✅ {df.shape[0]} agents · {df.shape[1]-1} notes")
    except Exception as e:
        st.sidebar.error(str(e)); df=pd.DataFrame(DEFAULT_DATA)
elif st.session_state.data_source=="gsheet" and st.session_state.gsheet_url:
    df,err=fetch_gsheet(st.session_state.gsheet_url)
    if err:
        st.sidebar.error(err); df=pd.DataFrame(DEFAULT_DATA)
    else:
        st.sidebar.success(f"✅ Google Sheets : {df.shape[0]} agents · {df.shape[1]-1} notes")
        st.sidebar.caption("🔄 Données actualisées automatiquement toutes les 60 s")
else:
    df=pd.DataFrame(DEFAULT_DATA)
    st.sidebar.info("📌 Données par défaut")

name_col=df.columns[0]
note_cols=get_note_cols(df)
agents=df[name_col].tolist()

with st.sidebar:
    st.markdown("### 🗓️ Session active")
    st.session_state.session_active=st.selectbox(
        "Session de pointage",st.session_state.sessions_config,
        index=st.session_state.sessions_config.index(st.session_state.session_active)
              if st.session_state.session_active in st.session_state.sessions_config else 0,
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### 🔍 Filtres (notes)")
    selected_agents=st.multiselect("Agents — courbes",options=agents,default=agents[:5])
    note_range=st.slider("Filtre moyenne",0.0,20.0,(0.0,20.0),0.5)
    st.markdown("---")
    nb_pointages=len(st.session_state.presences)
    st.metric("Pointages enregistrés",nb_pointages)

# ════════════════════════════════════════════════════════════════════════════
# EN-TÊTE
# ════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="main-title">📊 Notes & Présences — Tableau de Bord</div>',unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{len(agents)} agents · {len(note_cols)} évaluations · Session active : <b>{st.session_state.session_active}</b></div>',unsafe_allow_html=True)

all_vals=df[note_cols].values.flatten().astype(float)
df_stats=compute_stats(df,note_cols,name_col)

# KPI
k1,k2,k3,k4,k5,k6=st.columns(6)
pres=st.session_state.presences
nb_presents_session=len(pres[pres["Session"]==st.session_state.session_active]["Agent"].unique()) if len(pres)>0 else 0
kpi_data=[
    (round(np.mean(all_vals),2),"Moyenne Générale","toutes notes"),
    (int((df[note_cols]==20).sum().sum()),"Notes 20/20","parfaits"),
    (len(agents),"Agents total","inscrits"),
    (nb_presents_session,"Présents",f"session active"),
    (len(agents)-nb_presents_session,"Absents",f"session active"),
    (len(pres),"Total pointages","tous enregistrés"),
]
for col,(val,label,sub) in zip([k1,k2,k3,k4,k5,k6],kpi_data):
    col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">{label}</div><div class="kpi-sub">{sub}</div></div>',unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# ONGLETS
# ════════════════════════════════════════════════════════════════════════════
tab_scan,tab_qr,tab_pres,tab_croise,tab_notes,tab_tendance,tab_stats,tab_heatmap,tab_podium,tab_config=st.tabs([
    "📷 Pointage",
    "🎫 QR Codes agents",
    "👥 Présences",
    "🔗 Notes × Présences",
    "📈 Courbes notes",
    "🌐 Tendance globale",
    "📋 Tableau stats",
    "🔥 Heatmap",
    "🏆 Classement",
    "⚙️ Configuration",
])

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : POINTAGE
# ─────────────────────────────────────────────────────────────────────────────
with tab_scan:
    st.markdown('<div class="section-title">📷 Pointage des présences</div>',unsafe_allow_html=True)
    col_scan,col_manual=st.columns([1,1])

    with col_scan:
        st.markdown(f"**Session :** `{st.session_state.session_active}`")
        st.markdown("**Mode 1 — Scan QR par caméra** _(superviseur scanne le badge agent)_")

        if not QR_SCAN_OK:
            st.warning("⚠️ Module pyzbar non disponible. Utilisez le mode manuel ci-dessous.")
        else:
            st.markdown('<div class="scan-box">📸 Pointez la caméra vers le QR code de l\'agent</div>',
                        unsafe_allow_html=True)
            cam=st.camera_input("Capturer le QR code",label_visibility="collapsed")
            if cam:
                img=Image.open(cam)
                agent_found=decode_qr_from_image(img)
                if agent_found and agent_found in agents:
                    # Vérif doublon sur cette session
                    pres=st.session_state.presences
                    deja=pres[(pres["Agent"]==agent_found)&
                              (pres["Session"]==st.session_state.session_active)&
                              (pres["Date"]==datetime.date.today().strftime("%d/%m/%Y"))]
                    if len(deja)==0:
                        add_presence(agent_found,st.session_state.session_active)
                        st.success(f"✅ **{agent_found}** pointé à {datetime.datetime.now().strftime('%H:%M:%S')}")
                    else:
                        heure_deja=deja.iloc[0]["Heure"]
                        st.info(f"ℹ️ **{agent_found}** déjà pointé à {heure_deja} pour cette session.")
                elif agent_found:
                    st.error(f"❌ Agent '{agent_found}' non trouvé dans la liste.")
                else:
                    st.error("❌ QR code non reconnu. Vérifiez que le badge est bien un QR généré par cette application.")

    with col_manual:
        st.markdown("**Mode 2 — Pointage manuel**")
        with st.form("form_manual_pointage"):
            agent_sel=st.selectbox("Sélectionner l'agent",agents)
            statut_sel=st.selectbox("Statut",["Présent","En retard","Excusé"])
            submitted=st.form_submit_button("✅ Enregistrer le pointage",use_container_width=True)
            if submitted:
                pres=st.session_state.presences
                deja=pres[(pres["Agent"]==agent_sel)&
                          (pres["Session"]==st.session_state.session_active)&
                          (pres["Date"]==datetime.date.today().strftime("%d/%m/%Y"))]
                if len(deja)==0:
                    add_presence(agent_sel,st.session_state.session_active,statut_sel)
                    st.success(f"✅ **{agent_sel}** → {statut_sel} — {datetime.datetime.now().strftime('%H:%M:%S')}")
                else:
                    st.info(f"ℹ️ Déjà pointé à {deja.iloc[0]['Heure']}")

    # Journal de la session
    st.markdown('<div class="section-title">📋 Journal — Session active</div>',unsafe_allow_html=True)
    pres_session=st.session_state.presences[
        (st.session_state.presences["Session"]==st.session_state.session_active)&
        (st.session_state.presences["Date"]==datetime.date.today().strftime("%d/%m/%Y"))
    ].sort_values("Heure",ascending=False).reset_index(drop=True)

    if len(pres_session)>0:
        st.dataframe(pres_session,use_container_width=True,hide_index=True)
        buf_j=io.BytesIO()
        pres_session.to_csv(buf_j,index=False,encoding="utf-8-sig")
        st.download_button("⬇️ Exporter journal session",buf_j.getvalue(),
            file_name=f"journal_{st.session_state.session_active.replace(' ','_')}.csv",
            mime="text/csv")
    else:
        st.info("Aucun pointage pour cette session aujourd'hui.")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : QR CODES
# ─────────────────────────────────────────────────────────────────────────────
with tab_qr:
    st.markdown('<div class="section-title">🎫 Génération des QR Codes agents</div>',unsafe_allow_html=True)
    st.caption(f"Un QR code unique par agent · {len(agents)} agents détectés · Format PNG · Téléchargement ZIP")

    col_opt1,col_opt2=st.columns([2,1])
    with col_opt1:
        agents_qr_sel=st.multiselect(
            "Agents à inclure (laisser vide = tous)",
            options=agents,default=[],
            placeholder="Tous les agents par défaut")
    with col_opt2:
        qr_size=st.selectbox("Taille QR",["Petite (120px)","Normale (180px)","Grande (240px)"],index=1)
    qr_box_size={"Petite (120px)":4,"Normale (180px)":6,"Grande (240px)":8}[qr_size]

    agents_to_gen=agents_qr_sel if agents_qr_sel else agents
    st.markdown(f"**{len(agents_to_gen)} QR code(s) à générer**")

    if st.button("🔄 Générer tous les QR Codes",type="primary",use_container_width=True):
        zip_buf=io.BytesIO()
        preview_data=[]
        with zipfile.ZipFile(zip_buf,"w",zipfile.ZIP_DEFLATED) as zf:
            progress=st.progress(0,text="Génération en cours...")
            for i,agent in enumerate(agents_to_gen):
                qr=qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_H,
                                  box_size=qr_box_size,border=3)
                qr.add_data(agent_to_qr_key(agent))
                qr.make(fit=True)
                img=qr.make_image(fill_color="#2c3e7a",back_color="white")
                buf=io.BytesIO(); img.save(buf,format="PNG"); buf.seek(0)
                qr_bytes=buf.getvalue()
                safe_name=agent.replace("/","_").replace("\\","_")[:60]
                zf.writestr(f"QR_Badges/{safe_name}.png",qr_bytes)
                preview_data.append({"name":agent,"b64":base64.b64encode(qr_bytes).decode()})
                progress.progress((i+1)/len(agents_to_gen),
                    text=f"Génération {i+1}/{len(agents_to_gen)} — {agent[:30]}...")
            progress.empty()

        zip_buf.seek(0)
        st.success(f"✅ {len(agents_to_gen)} QR codes générés avec succès !")
        st.download_button(
            label=f"⬇️ Télécharger tous les QR Codes (ZIP — {len(agents_to_gen)} fichiers)",
            data=zip_buf.getvalue(),
            file_name="QR_Badges_Agents.zip",
            mime="application/zip",
            use_container_width=True,
        )

        # Prévisualisation grille
        st.markdown('<div class="section-title">Aperçu des QR Codes</div>',unsafe_allow_html=True)
        html_grid='<div class="qr-grid">'
        for item in preview_data:
            short=item["name"].split()[0]+" "+item["name"].split()[-1] if len(item["name"].split())>1 else item["name"]
            html_grid+=f'''<div class="qr-item">
                <img src="data:image/png;base64,{item["b64"]}" width="110" style="border-radius:6px"/>
                <div class="qr-name">{item["name"][:35]}</div>
            </div>'''
        html_grid+='</div>'
        st.markdown(html_grid,unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**💡 Comment utiliser les QR Codes ?**")
    st.markdown("""
1. Cliquez **Générer tous les QR Codes** → téléchargez le ZIP
2. Imprimez chaque PNG (1 page par agent) ou envoyez-le par **WhatsApp/email**
3. Le jour de la formation, chaque agent présente son badge QR
4. Le superviseur ouvre l'onglet **📷 Pointage** et scanne le badge
5. L'heure et le nom sont enregistrés automatiquement
    """)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : PRÉSENCES
# ─────────────────────────────────────────────────────────────────────────────
with tab_pres:
    st.markdown('<div class="section-title">👥 Statistiques de présence</div>',unsafe_allow_html=True)

    if len(st.session_state.presences)==0:
        st.info("Aucun pointage enregistré. Utilisez l'onglet **📷 Pointage** pour commencer.")
    else:
        pres_all=st.session_state.presences
        df_pres_stats=presence_stats(agents)

        # KPI présences
        pa,pb,pc,pd_=st.columns(4)
        taux_moyen=round(df_pres_stats["Taux (%)"].mean(),1)
        nb_assidus=len(df_pres_stats[df_pres_stats["Statut"]=="Assidu"])
        nb_absents_tot=len(df_pres_stats[df_pres_stats["Présences"]==0])
        for col,(val,label,sub) in zip([pa,pb,pc,pd_],[
            (f"{taux_moyen}%","Taux moyen","de présence"),
            (nb_assidus,"Assidus (≥80%)","agents"),
            (nb_absents_tot,"Absents","0 présence"),
            (len(pres_all),"Total pointages","enregistrés"),
        ]):
            col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">{label}</div><div class="kpi-sub">{sub}</div></div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)

        # Graphique barres taux présence
        df_sorted=df_pres_stats.sort_values("Taux (%)",ascending=True)
        colors_pres=[("#27ae60" if t>=80 else "#f39c12" if t>=50 else "#e74c3c")
                     for t in df_sorted["Taux (%)"]]
        fig_pres=go.Figure(go.Bar(
            x=df_sorted["Taux (%)"],y=df_sorted["Agent"],orientation="h",
            marker=dict(color=colors_pres,line=dict(color="white",width=0.5)),
            text=[f"{v}%" for v in df_sorted["Taux (%)"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Taux : <b>%{x}%</b><extra></extra>",
        ))
        fig_pres.update_layout(
            paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Taux de présence (%)",range=[0,115],gridcolor="#f0f4ff"),
            yaxis=dict(tickfont=dict(size=10),autorange="reversed"),
            height=max(400,len(agents)*28),
            margin=dict(t=20,b=40,l=230,r=60),showlegend=False,
            shapes=[dict(type="line",xref="x",x0=80,x1=80,yref="paper",y0=0,y1=1,
                         line=dict(color="#27ae60",width=1.5,dash="dot"))],
        )
        st.plotly_chart(fig_pres,use_container_width=True)

        # Tableau détaillé
        st.markdown('<div class="section-title">Tableau détaillé des présences</div>',unsafe_allow_html=True)

        def style_pres(row):
            styles=[]
            for col in row.index:
                if col=="Taux (%)":
                    v=row[col]
                    if v>=80:   styles.append("background-color:#e6f4ea;color:#1e7e34")
                    elif v>=50: styles.append("background-color:#fef3c7;color:#92400e")
                    else:       styles.append("background-color:#fee2e2;color:#b91c1c")
                else: styles.append("")
            return styles

        st.dataframe(
            df_pres_stats.sort_values("Taux (%)",ascending=False).reset_index(drop=True)
            .style.apply(style_pres,axis=1)
            .format({"Taux (%)":"{:.1f}%"}),
            use_container_width=True,height=420,
        )

        # Présence par session
        st.markdown('<div class="section-title">Présences par session</div>',unsafe_allow_html=True)
        session_counts=pres_all.groupby("Session")["Agent"].nunique().reset_index()
        session_counts.columns=["Session","Nb présents"]
        session_counts["Taux (%)"]=round(session_counts["Nb présents"]/len(agents)*100,1)
        fig_sess=go.Figure(go.Bar(
            x=session_counts["Session"],y=session_counts["Nb présents"],
            marker=dict(color="#4a6cf7",line=dict(color="white",width=0.5)),
            text=[f"{v} agents<br>({t}%)" for v,t in zip(session_counts["Nb présents"],session_counts["Taux (%)"])],
            textposition="outside",
        ))
        fig_sess.update_layout(
            paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Session",gridcolor="#f0f4ff"),
            yaxis=dict(title="Nb agents présents",range=[0,len(agents)*1.25],gridcolor="#f0f4ff"),
            height=360,margin=dict(t=20,b=60,l=60,r=20),showlegend=False,
        )
        st.plotly_chart(fig_sess,use_container_width=True)

        # Heatmap présences agents × sessions
        sessions_list=sorted(pres_all["Session"].unique())
        heat_data=[]
        for agent in agents:
            row_data=[]
            for sess in sessions_list:
                present=len(pres_all[(pres_all["Agent"]==agent)&(pres_all["Session"]==sess)])>0
                row_data.append(1 if present else 0)
            heat_data.append(row_data)

        fig_heat_p=go.Figure(go.Heatmap(
            z=heat_data,x=sessions_list,y=agents,
            colorscale=[[0,"#fee2e2"],[1,"#e6f4ea"]],
            text=[["✓" if v else "✗" for v in row] for row in heat_data],
            texttemplate="%{text}",textfont=dict(size=12),
            hovertemplate="<b>%{y}</b><br>%{x} : <b>%{text}</b><extra></extra>",
            showscale=False,zmin=0,zmax=1,
        ))
        fig_heat_p.update_layout(
            paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(side="top"),yaxis=dict(autorange="reversed"),
            height=max(400,len(agents)*28),
            margin=dict(t=50,b=20,l=230,r=20),
        )
        st.plotly_chart(fig_heat_p,use_container_width=True)

        # Export
        buf_p=io.BytesIO()
        with pd.ExcelWriter(buf_p,engine="openpyxl") as w:
            pres_all.to_excel(w,sheet_name="Tous les pointages",index=False)
            df_pres_stats.to_excel(w,sheet_name="Stats présences",index=False)
        st.download_button("⬇️ Exporter présences (Excel)",buf_p.getvalue(),
            file_name="presences_formation.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : CROISEMENT NOTES × PRÉSENCES
# ─────────────────────────────────────────────────────────────────────────────
with tab_croise:
    st.markdown('<div class="section-title">🔗 Croisement Notes × Présences</div>',unsafe_allow_html=True)

    if len(st.session_state.presences)==0:
        st.info("Enregistrez des présences pour activer cette analyse.")
    else:
        df_pres_stats2=presence_stats(agents)
        df_croise=df_stats.merge(df_pres_stats2[["Agent","Taux (%)","Présences","Statut"]],on="Agent",how="left")
        df_croise["Taux (%)"]=df_croise["Taux (%)"].fillna(0)
        df_croise["Présences"]=df_croise["Présences"].fillna(0).astype(int)
        df_croise["Statut présence"]=df_croise["Statut"].fillna("Absent")

        # Scatter notes vs présence
        color_map={"Assidu":"#27ae60","Moyen":"#f39c12","Absent":"#e74c3c"}
        fig_scatter=go.Figure()
        for statut,color in color_map.items():
            sub=df_croise[df_croise["Statut présence"]==statut]
            if len(sub)>0:
                fig_scatter.add_trace(go.Scatter(
                    x=sub["Taux (%)"],y=sub["Moyenne"],
                    mode="markers+text",name=statut,
                    marker=dict(size=12,color=color,opacity=0.8,
                                line=dict(color="white",width=1.5)),
                    text=sub["Agent"].str.split().str[0],
                    textposition="top center",textfont=dict(size=9),
                    hovertemplate="<b>%{text}</b><br>Présence : %{x}%<br>Moyenne : %{y:.2f}/20<extra></extra>",
                ))
        # Ligne de tendance
        if len(df_croise)>3:
            x_t=df_croise["Taux (%)"].values
            y_t=df_croise["Moyenne"].values
            try:
                z=np.polyfit(x_t,y_t,1)
                p=np.poly1d(z)
                x_line=np.linspace(0,100,50)
                fig_scatter.add_trace(go.Scatter(
                    x=x_line,y=p(x_line),mode="lines",name="Tendance",
                    line=dict(color="#4a6cf7",width=2,dash="dash"),
                    hoverinfo="skip",
                ))
            except Exception: pass

        fig_scatter.update_layout(
            title="Relation Taux de présence × Moyenne des notes",
            paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Taux de présence (%)",range=[-5,110],gridcolor="#f0f4ff"),
            yaxis=dict(title="Moyenne /20",range=[0,21],gridcolor="#f0f4ff"),
            legend=dict(bgcolor="rgba(255,255,255,.95)",bordercolor="#dce4f5",borderwidth=1),
            height=500,margin=dict(t=50,b=40,l=50,r=20),
        )
        st.plotly_chart(fig_scatter,use_container_width=True)

        # Corrélation
        corr_val=round(df_croise["Taux (%)"].corr(df_croise["Moyenne"]),3)
        interp=("forte positive" if corr_val>0.6 else
                "modérée positive" if corr_val>0.3 else
                "faible" if corr_val>0 else "négative")
        st.info(f"**Corrélation présence / notes : {corr_val}** — corrélation {interp}")

        # Tableau croisé
        st.markdown('<div class="section-title">Tableau croisé complet</div>',unsafe_allow_html=True)
        df_croise_show=df_croise[["Agent","Moyenne","Mention","Taux (%)","Présences","Statut présence"]]\
            .sort_values("Moyenne",ascending=False).reset_index(drop=True)
        df_croise_show.index+=1

        def style_croise(row):
            styles=[]
            for col in row.index:
                if col=="Moyenne":
                    v=row[col]
                    if v>=16:   styles.append("background-color:#e6f4ea;color:#1e7e34")
                    elif v>=14: styles.append("background-color:#dbeafe;color:#1a56db")
                    elif v>=10: styles.append("background-color:#fef3c7;color:#92400e")
                    else:       styles.append("background-color:#fee2e2;color:#b91c1c")
                elif col=="Taux (%)":
                    v=row[col]
                    if v>=80:   styles.append("background-color:#e6f4ea;color:#1e7e34")
                    elif v>=50: styles.append("background-color:#fef3c7;color:#92400e")
                    else:       styles.append("background-color:#fee2e2;color:#b91c1c")
                else: styles.append("")
            return styles

        st.dataframe(df_croise_show.style.apply(style_croise,axis=1)
                     .format({"Moyenne":"{:.2f}","Taux (%)":"{:.1f}%"}),
                     use_container_width=True,height=460)

        buf_c=io.BytesIO()
        with pd.ExcelWriter(buf_c,engine="openpyxl") as w:
            df_croise.to_excel(w,sheet_name="Croisement",index=False)
        st.download_button("⬇️ Exporter croisement (Excel)",buf_c.getvalue(),
            file_name="croisement_notes_presences.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : COURBES NOTES
# ─────────────────────────────────────────────────────────────────────────────
with tab_notes:
    st.markdown('<div class="section-title">📈 Évolution individuelle des notes</div>',unsafe_allow_html=True)
    if not selected_agents:
        st.info("👈 Sélectionnez des agents dans le panneau latéral.")
    else:
        palette=(px.colors.qualitative.Pastel+px.colors.qualitative.Safe
                 +px.colors.qualitative.Vivid+px.colors.qualitative.Dark24)
        fig=go.Figure()
        for i,agent in enumerate(selected_agents):
            row=df[df[name_col]==agent].iloc[0]
            notes=[float(row[c]) for c in note_cols]
            c=palette[i%len(palette)]
            fig.add_trace(go.Scatter(x=note_cols,y=notes,mode="lines+markers+text",name=agent,
                line=dict(color=c,width=2.5,shape="spline"),
                marker=dict(size=9,color=c,line=dict(color="white",width=1.5)),
                text=[str(int(n)) for n in notes],textposition="top center",
                textfont=dict(size=9,color=c),
                hovertemplate=f"<b>{agent}</b><br>%{{x}} : <b>%{{y}}</b>/20<extra></extra>"))
        fig.update_layout(
            paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Évaluation",gridcolor="#f0f4ff",linecolor="#dce4f5"),
            yaxis=dict(title="Note /20",range=[-0.5,21],gridcolor="#f0f4ff",linecolor="#dce4f5"),
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

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : TENDANCE GLOBALE
# ─────────────────────────────────────────────────────────────────────────────
with tab_tendance:
    st.markdown('<div class="section-title">🌐 Tendance globale</div>',unsafe_allow_html=True)
    df_fl=df[note_cols].astype(float)
    moy_e=df_fl.mean().values; med_e=df_fl.median().values
    max_e=df_fl.max().values;  min_e=df_fl.min().values
    std_e=df_fl.std().values
    fig2=go.Figure()
    fig2.add_trace(go.Scatter(x=list(note_cols)+list(reversed(note_cols)),
        y=list(max_e)+list(reversed(min_e)),fill="toself",fillcolor="rgba(74,108,247,0.07)",
        line=dict(color="rgba(0,0,0,0)"),hoverinfo="skip",name="Zone Min–Max"))
    fig2.add_trace(go.Scatter(x=list(note_cols)+list(reversed(note_cols)),
        y=list(moy_e+std_e)+list(reversed(moy_e-std_e)),fill="toself",
        fillcolor="rgba(74,108,247,0.12)",line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",name="Zone ±1σ"))
    fig2.add_trace(go.Scatter(x=note_cols,y=med_e,mode="lines+markers",name="Médiane",
        line=dict(color="#7b5ea7",width=2,dash="dash",shape="spline"),
        marker=dict(size=7,color="#7b5ea7"),
        hovertemplate="Médiane %{x} : <b>%{y:.2f}</b>/20<extra></extra>"))
    fig2.add_trace(go.Scatter(x=note_cols,y=moy_e,mode="lines+markers+text",name="Moyenne",
        line=dict(color="#4a6cf7",width=3,shape="spline"),
        marker=dict(size=10,color="#4a6cf7",line=dict(color="white",width=2)),
        text=[f"{v:.1f}" for v in moy_e],textposition="top center",
        textfont=dict(size=10,color="#2c3e7a"),
        hovertemplate="Moyenne %{x} : <b>%{y:.2f}</b>/20<extra></extra>"))
    fig2.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(title="Évaluation",gridcolor="#f0f4ff",linecolor="#dce4f5"),
        yaxis=dict(title="Note /20",range=[-0.5,21],gridcolor="#f0f4ff",linecolor="#dce4f5"),
        legend=dict(bgcolor="rgba(255,255,255,.95)",bordercolor="#dce4f5",borderwidth=1),
        hovermode="x unified",height=430,margin=dict(t=30,b=40,l=50,r=20))
    st.plotly_chart(fig2,use_container_width=True)
    recap=pd.DataFrame({"Évaluation":note_cols,"Moyenne":[round(v,2) for v in moy_e],
        "Médiane":[round(v,2) for v in med_e],"Max":[int(v) for v in max_e],
        "Min":[int(v) for v in min_e],"Écart-type":[round(v,2) for v in std_e]})
    st.dataframe(recap,use_container_width=True,hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : TABLEAU STATS
# ─────────────────────────────────────────────────────────────────────────────
with tab_stats:
    st.markdown('<div class="section-title">📋 Statistiques par agent</div>',unsafe_allow_html=True)
    df_f=df_stats[(df_stats["Moyenne"]>=note_range[0])&
                  (df_stats["Moyenne"]<=note_range[1])]\
         .sort_values("Moyenne",ascending=False).reset_index(drop=True)
    df_f.index+=1
    st.dataframe(df_f.style.apply(style_row,axis=1)
        .format({"Moyenne":"{:.2f}","Médiane":"{:.2f}","Écart-type":"{:.2f}",
                 "Max":"{:.0f}","Min":"{:.0f}"}),
        use_container_width=True,height=500)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : HEATMAP
# ─────────────────────────────────────────────────────────────────────────────
with tab_heatmap:
    st.markdown('<div class="section-title">🔥 Carte de chaleur des notes</div>',unsafe_allow_html=True)
    heat=df.set_index(name_col)[note_cols].astype(float)
    fig5=go.Figure(go.Heatmap(
        z=heat.values,x=note_cols,y=heat.index.tolist(),
        colorscale=[[0,"#fee2e2"],[0.001,"#fecaca"],[0.3,"#bfdbfe"],[0.6,"#4a6cf7"],[1,"#1a237e"]],
        text=heat.values.astype(int),texttemplate="%{text}",
        textfont=dict(size=10,color="#1a1a2e"),
        hovertemplate="<b>%{y}</b><br>%{x} : <b>%{z}</b>/20<extra></extra>",
        colorbar=dict(title="Note /20"),zmin=0,zmax=20))
    fig5.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(side="top"),yaxis=dict(autorange="reversed"),
        height=max(400,len(agents)*28),margin=dict(t=50,b=20,l=240,r=20))
    st.plotly_chart(fig5,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : CLASSEMENT
# ─────────────────────────────────────────────────────────────────────────────
with tab_podium:
    st.markdown('<div class="section-title">🏆 Classement général</div>',unsafe_allow_html=True)
    df_ranked=df_stats.sort_values("Moyenne",ascending=False).reset_index(drop=True)
    df_ranked.index+=1
    if len(df_ranked)>=3:
        p2,p1,p3=st.columns([1,1.2,1])
        for col,rank,medal,bg in [(p1,1,"🥇","#FFF9C4"),(p2,2,"🥈","#F5F5F5"),(p3,3,"🥉","#FBE9E7")]:
            r=df_ranked.iloc[rank-1]
            ml,mc=mention_info(r["Moyenne"])
            col.markdown(f'''<div style="background:{bg};border-radius:16px;padding:18px;text-align:center;
                box-shadow:0 4px 16px rgba(0,0,0,.07);margin-bottom:10px;">
                <div style="font-size:2.2rem;">{medal}</div>
                <div style="font-weight:700;color:#2c3e7a;font-size:.95rem;margin-top:5px;">{r["Agent"]}</div>
                <div style="font-size:1.9rem;font-weight:700;color:#4a6cf7;margin-top:3px;">{r["Moyenne"]:.2f}</div>
                <div style="font-size:.78rem;color:#6b7db3;">/ 20</div>
                <div style="margin-top:5px;"><span class="{mc}">{ml}</span></div>
            </div>''',unsafe_allow_html=True)
    colors_bar=["#2d6a4f" if m>=16 else "#1a56db" if m>=14 else "#92400e" if m>=10 else "#b91c1c"
                for m in df_ranked["Moyenne"]]
    fig_bar=go.Figure(go.Bar(
        x=df_ranked["Moyenne"],y=df_ranked["Agent"],orientation="h",
        marker=dict(color=colors_bar,line=dict(color="white",width=0.5)),
        text=[f"{v:.2f}" for v in df_ranked["Moyenne"]],textposition="outside",
        hovertemplate="<b>%{y}</b><br>Moyenne : <b>%{x:.2f}</b>/20<extra></extra>"))
    fig_bar.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(title="Moyenne /20",range=[0,23],gridcolor="#f0f4ff"),
        yaxis=dict(autorange="reversed",tickfont=dict(size=10)),
        height=max(400,len(agents)*28),margin=dict(t=20,b=40,l=230,r=60),showlegend=False,
        shapes=[dict(type="line",xref="x",x0=10,x1=10,yref="paper",y0=0,y1=1,
                     line=dict(color="#e74c3c",width=1.5,dash="dot")),
                dict(type="line",xref="x",x0=14,x1=14,yref="paper",y0=0,y1=1,
                     line=dict(color="#27ae60",width=1.5,dash="dot"))])
    st.plotly_chart(fig_bar,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ONGLET : CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
with tab_config:
    st.markdown('<div class="section-title">⚙️ Configuration des sessions</div>',unsafe_allow_html=True)
    sessions_text=st.text_area(
        "Sessions de formation (1 par ligne)",
        value="\n".join(st.session_state.sessions_config),
        height=200,help="Modifiez la liste des sessions ici")
    if st.button("💾 Sauvegarder les sessions"):
        new_sessions=[s.strip() for s in sessions_text.split("\n") if s.strip()]
        if new_sessions:
            st.session_state.sessions_config=new_sessions
            st.success(f"✅ {len(new_sessions)} sessions configurées.")
        else:
            st.error("Liste vide.")

    st.markdown('<div class="section-title">🗑️ Gestion des pointages</div>',unsafe_allow_html=True)
    if len(st.session_state.presences)>0:
        st.dataframe(st.session_state.presences,use_container_width=True,height=300)
        buf_all=io.BytesIO()
        with pd.ExcelWriter(buf_all,engine="openpyxl") as w:
            st.session_state.presences.to_excel(w,sheet_name="Pointages",index=False)
        st.download_button("⬇️ Exporter tous les pointages",buf_all.getvalue(),
            file_name="pointages_complets.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if st.button("🗑️ Effacer tous les pointages",type="secondary"):
            st.session_state.presences=pd.DataFrame(
                columns=["Agent","Date","Heure","Session","Statut"])
            st.success("Pointages effacés.")
            st.rerun()
    else:
        st.info("Aucun pointage enregistré.")

    st.markdown('<div class="section-title">📥 Importer des pointages existants (CSV)</div>',unsafe_allow_html=True)
    csv_import=st.file_uploader("Charger un CSV de pointages",type=["csv"],key="import_pres")
    if csv_import:
        try:
            df_imp=pd.read_csv(csv_import)
            required={"Agent","Date","Heure","Session","Statut"}
            if required.issubset(set(df_imp.columns)):
                st.session_state.presences=pd.concat(
                    [st.session_state.presences,df_imp],ignore_index=True).drop_duplicates()
                st.success(f"✅ {len(df_imp)} pointages importés.")
                st.rerun()
            else:
                st.error(f"Colonnes requises : {required}")
        except Exception as e:
            st.error(str(e))

# ── EXPORT GLOBAL ─────────────────────────────────────────────────────────────
st.markdown("---")
col_exp1,col_exp2=st.columns(2)
with col_exp1:
    buf_final=io.BytesIO()
    with pd.ExcelWriter(buf_final,engine="openpyxl") as w:
        df.to_excel(w,sheet_name="Données brutes",index=False)
        df_stats.to_excel(w,sheet_name="Stats notes",index=False)
        df_stats.sort_values("Moyenne",ascending=False).to_excel(w,sheet_name="Classement",index=True)
        if len(st.session_state.presences)>0:
            st.session_state.presences.to_excel(w,sheet_name="Pointages",index=False)
            presence_stats(agents).to_excel(w,sheet_name="Stats présences",index=False)
    st.download_button("⬇️ Export complet Excel (toutes feuilles)",buf_final.getvalue(),
        file_name="tableau_bord_complet.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)
with col_exp2:
    if len(st.session_state.presences)>0:
        csv_exp=st.session_state.presences.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button("⬇️ Export pointages CSV (sauvegarde)",csv_exp,
            file_name="pointages_sauvegarde.csv",mime="text/csv",use_container_width=True)

st.caption("Plateforme Formation · Notes & Présences · QR Code · v3.0")
