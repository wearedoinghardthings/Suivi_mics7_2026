import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import io, qrcode, datetime, zipfile, base64

try:
    from streamlit_qrcode_scanner import qrcode_scanner
    QR_OK = True
except Exception:
    QR_OK = False

# ════════════════════════════════════════════════════════════════════════════
# ÉTAT PARTAGÉ — même objet pour TOUS les utilisateurs
# ════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_shared():
    return {
        "notes": None,
        "notes_label": "Données par défaut",
        "presences": [],
        "sessions_config": ["Jour 1 - Matin","Jour 1 - Après-midi",
                            "Jour 2 - Matin","Jour 2 - Après-midi","Jour 3 - Matin"],
    }
shared = get_shared()

# ════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Formation — Notes & Présences",
                   page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;background:#fff!important;color:#1a1a2e!important;}
.main,.block-container{background:#fff!important;padding-top:.8rem!important;}
section[data-testid="stSidebar"]{background:linear-gradient(160deg,#f0f4ff,#e8f0fe)!important;border-right:1px solid #dce4f5;}
section[data-testid="stSidebar"] *{color:#1a1a2e!important;}
.main-title{font-family:'DM Serif Display',serif;font-size:clamp(1.4rem,4vw,2rem);color:#2c3e7a;}
.sub-title{font-size:clamp(.78rem,2.5vw,.9rem);color:#6b7db3;margin-bottom:1rem;}
.kpi-card{background:#fff;border:1px solid #e0e8ff;border-radius:14px;
  padding:clamp(10px,2vw,16px);text-align:center;box-shadow:0 2px 10px rgba(44,62,122,.06);margin-bottom:6px;}
.kpi-value{font-size:clamp(1.2rem,3.5vw,1.7rem);font-weight:700;color:#2c3e7a;line-height:1.1;}
.kpi-label{font-size:clamp(.6rem,1.8vw,.72rem);color:#7a8db3;margin-top:4px;
  text-transform:uppercase;letter-spacing:.6px;font-weight:500;}
.kpi-sub{font-size:.67rem;color:#a0aec0;margin-top:2px;}
.section-title{font-family:'DM Serif Display',serif;font-size:clamp(.95rem,3vw,1.2rem);
  color:#2c3e7a;margin-top:1.2rem;margin-bottom:.4rem;border-left:4px solid #4a6cf7;padding-left:11px;}
.stTabs [data-baseweb="tab-list"]{background:#f0f4ff;border-radius:10px;padding:4px;gap:3px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:500;color:#2c3e7a;
  padding:5px 10px;font-size:clamp(.68rem,2vw,.82rem);white-space:nowrap;}
.stTabs [aria-selected="true"]{background:#fff!important;color:#4a6cf7!important;
  box-shadow:0 1px 6px rgba(74,108,247,.15);}
.stDownloadButton>button{background:linear-gradient(135deg,#4a6cf7,#7b5ea7)!important;
  color:#fff!important;border:none!important;border-radius:8px!important;font-weight:600!important;min-height:42px;}
.stButton>button{border-radius:8px!important;min-height:42px;}
.badge-tb{background:#e6f4ea;color:#1e7e34;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-b{background:#dbeafe;color:#1a56db;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-ab{background:#fef3c7;color:#92400e;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.badge-in{background:#fee2e2;color:#b91c1c;padding:2px 9px;border-radius:20px;font-size:.76rem;font-weight:600;}
.qr-grid{display:flex;flex-wrap:wrap;gap:10px;}
.qr-item{background:#fff;border:1px solid #e0e8ff;border-radius:10px;padding:8px;
  text-align:center;width:clamp(110px,22vw,140px);box-shadow:0 1px 6px rgba(44,62,122,.06);}
.qr-name{font-size:clamp(.6rem,1.8vw,.72rem);color:#2c3e7a;font-weight:600;
  margin-top:5px;line-height:1.3;word-break:break-word;}
.shared-banner{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
  padding:10px 14px;margin-bottom:8px;font-size:.84rem;color:#166534;}
.scan-ok{background:#f0fdf4;border:2px solid #86efac;border-radius:12px;
  padding:14px;text-align:center;margin:8px 0;}
/* ── Agrandir l'iframe du scanner QR ── */
iframe[title="streamlit_qrcode_scanner.qrcode_scanner"]{
  width:100%!important;min-height:360px!important;border-radius:12px;
  border:2px dashed #4a6cf7!important;
}
div[data-testid="stCustomComponentV1"]{width:100%!important;}
@media(max-width:768px){
  .block-container{padding:.4rem .5rem 2rem!important;}
  iframe[title="streamlit_qrcode_scanner.qrcode_scanner"]{min-height:280px!important;}
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

# ════════════════════════════════════════════════════════════════════════════
# FONCTIONS
# ════════════════════════════════════════════════════════════════════════════
def get_notes_df():
    if shared["notes"] is not None:
        return pd.DataFrame(shared["notes"])
    return pd.DataFrame(DEFAULT_DATA)

def get_presences_df():
    if shared["presences"]:
        return pd.DataFrame(shared["presences"])
    return pd.DataFrame(columns=["Agent","Date","Heure","Session","Statut"])

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
    now=datetime.datetime.now()
    shared["presences"].append({
        "Agent":agent,"Date":now.strftime("%d/%m/%Y"),
        "Heure":now.strftime("%H:%M:%S"),"Session":session,"Statut":statut,
    })

def is_already_pointed(agent, session):
    today=datetime.date.today().strftime("%d/%m/%Y")
    for p in shared["presences"]:
        if p["Agent"]==agent and p["Session"]==session and p["Date"]==today:
            return True, p["Heure"]
    return False, None

def presence_stats(agents):
    pres_df=get_presences_df(); sessions=shared["sessions_config"]
    rows=[]
    for agent in agents:
        ap=pres_df[pres_df["Agent"]==agent] if len(pres_df)>0 else pd.DataFrame()
        nb=len(ap["Session"].unique()) if len(ap)>0 else 0
        taux=round(nb/len(sessions)*100,1) if sessions else 0
        rows.append({"Agent":agent,"Présences":nb,"Sessions totales":len(sessions),
                     "Taux (%)":taux,
                     "Statut":("Assidu" if taux>=80 else "Moyen" if taux>=50 else
                               "Faible" if nb>0 else "Non pointé")})
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
# SESSION STATE
# ════════════════════════════════════════════════════════════════════════════
for k,v in {
    "camera_on":False,"last_scan_agent":None,"last_scan_time":None,
    "admin_logged_in":False,
    "session_active":shared["sessions_config"][0],
}.items():
    if k not in st.session_state: st.session_state[k]=v

# ════════════════════════════════════════════════════════════════════════════
# CHARGEMENT
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
    st.markdown(f'<div class="shared-banner">📡 <b>{shared["notes_label"]}</b><br>'
                f'<small>{len(agents)} agents · {len(note_cols)} évaluations</small></div>',
                unsafe_allow_html=True)
    if st.session_state.session_active not in shared["sessions_config"]:
        st.session_state.session_active = shared["sessions_config"][0]
    st.markdown("### 🗓️ Session active")
    st.session_state.session_active = st.selectbox(
        "Session", shared["sessions_config"],
        index=shared["sessions_config"].index(st.session_state.session_active),
        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### 🔍 Filtres")
    selected_agents = st.multiselect("Agents (courbes)", options=agents, default=agents[:5])
    note_range = st.slider("Filtre moyenne", 0.0, 20.0, (0.0,20.0), 0.5)
    st.markdown("---")
    nb_pts=len(pres_df)
    nb_sess=len(pres_df[pres_df["Session"]==st.session_state.session_active]["Agent"].unique()) if nb_pts>0 else 0
    st.metric("Total pointages", nb_pts)
    st.metric("Présents session", nb_sess)

# ════════════════════════════════════════════════════════════════════════════
# EN-TÊTE
# ════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="main-title">📊 Formation — Notes & Présences</div>',unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">{len(agents)} agents · {len(note_cols)} évaluations · '
            f'<b>{shared["notes_label"]}</b> · Session : <b>{st.session_state.session_active}</b></div>',
            unsafe_allow_html=True)

# ── KPI — 9 indicateurs ─────────────────────────────────────────────────────
moy_gen   = round(np.mean(all_vals), 2)
moy_max_a = round(df[note_cols].astype(float).max(axis=1).mean(), 2)
moy_min_a = round(df[note_cols].astype(float).min(axis=1).mean(), 2)
nb_20     = int((df[note_cols]==20).sum().sum())
nb_zero   = int((df[note_cols]==0).sum().sum())
nb_tb     = len(df_stats[df_stats["Mention"]=="Très Bien"])
nb_insuf  = len(df_stats[df_stats["Mention"]=="Insuffisant"])

row1 = st.columns(5)
row2 = st.columns(4)
kpi_r1 = [
    (moy_gen,   "Moyenne Générale",  "toutes notes"),
    (moy_max_a, "Moy. Max/Agent",    "meilleur score moyen"),
    (moy_min_a, "Moy. Min/Agent",    "score le plus bas moyen"),
    (nb_20,     "Notes 20/20",       "scores parfaits"),
    (nb_zero,   "Notes = 0",         "zéros obtenus"),
]
kpi_r2 = [
    (nb_tb,    "Très Bien",      f"sur {len(agents)} agents"),
    (len(df_stats[df_stats["Mention"]=="Bien"]), "Bien", f"sur {len(agents)} agents"),
    (len(df_stats[df_stats["Mention"]=="Assez Bien"]), "Assez Bien", f"sur {len(agents)} agents"),
    (nb_insuf, "Insuffisant",   f"sur {len(agents)} agents"),
]
for col,(val,label,sub) in zip(row1,kpi_r1):
    col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
                 f'<div class="kpi-label">{label}</div><div class="kpi-sub">{sub}</div></div>',
                 unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)
for col,(val,label,sub) in zip(row2,kpi_r2):
    col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
                 f'<div class="kpi-label">{label}</div><div class="kpi-sub">{sub}</div></div>',
                 unsafe_allow_html=True)
st.markdown("<br>",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# ONGLETS
# ════════════════════════════════════════════════════════════════════════════
(tab_pres, tab_croise, tab_notes, tab_tendance,
 tab_stats, tab_heatmap, tab_podium, tab_admin) = st.tabs([
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
# PRÉSENCES
# ─────────────────────────────────────────────────────────────────────────────
with tab_pres:
    st.markdown('<div class="section-title">👥 Statistiques de présence</div>',unsafe_allow_html=True)
    pres_v=get_presences_df()
    if len(pres_v)==0:
        st.info("Aucun pointage. L'administrateur peut pointer les présences dans l'onglet **🔐 Admin**.")
    else:
        df_ps=presence_stats(agents)
        nb_p=len(df_ps[df_ps["Présences"]>0])
        taux_m=round(df_ps[df_ps["Présences"]>0]["Taux (%)"].mean(),1) if nb_p>0 else 0
        pa,pb,pc,pd_=st.columns(4)
        for col,(val,lbl,sub) in zip([pa,pb,pc,pd_],[
            (f"{taux_m}%","Taux moyen","agents pointés"),
            (nb_p,"Agents pointés","≥ 1 session"),
            (len(df_ps[df_ps["Statut"]=="Assidu"]),"Assidus ≥80%","agents"),
            (len(pres_v),"Total pointages","enregistrés"),
        ]):
            col.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
                         f'<div class="kpi-label">{lbl}</div><div class="kpi-sub">{sub}</div></div>',
                         unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        df_s=df_ps[df_ps["Présences"]>0].sort_values("Taux (%)",ascending=True)
        if len(df_s)>0:
            cp=["#27ae60" if t>=80 else "#f39c12" if t>=50 else "#e74c3c" for t in df_s["Taux (%)"]]
            fig_p=go.Figure(go.Bar(x=df_s["Taux (%)"],y=df_s["Agent"],orientation="h",
                marker=dict(color=cp,line=dict(color="white",width=0.5)),
                text=[f"{v}%" for v in df_s["Taux (%)"]],textposition="outside"))
            fig_p.update_layout(paper_bgcolor="white",plot_bgcolor="white",
                font=dict(family="DM Sans",color="#2c3e7a"),
                xaxis=dict(range=[0,118],gridcolor="#f0f4ff"),
                yaxis=dict(autorange="reversed",tickfont=dict(size=10)),
                height=max(360,len(df_s)*30),margin=dict(t=20,b=40,l=230,r=60),showlegend=False,
                shapes=[dict(type="line",xref="x",x0=80,x1=80,yref="paper",y0=0,y1=1,
                             line=dict(color="#27ae60",width=1.5,dash="dot"))])
            st.plotly_chart(fig_p,use_container_width=True)
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
            pres_v.to_excel(w,sheet_name="Pointages",index=False)
            df_ps.to_excel(w,sheet_name="Stats présences",index=False)
        st.download_button("⬇️ Exporter présences",buf_p.getvalue(),
            file_name="presences.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# CROISEMENT
# ─────────────────────────────────────────────────────────────────────────────
with tab_croise:
    st.markdown('<div class="section-title">🔗 Croisement Notes × Présences</div>',unsafe_allow_html=True)
    pres_cx=get_presences_df()
    if len(pres_cx)==0:
        st.info("Aucune présence enregistrée.")
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
                    text=sub["Agent"].str.split().str[0],textposition="top center",textfont=dict(size=9),
                    hovertemplate="<b>%{text}</b><br>Présence:%{x}%<br>Moy:%{y:.2f}<extra></extra>"))
        pts_r=df_cx[df_cx["Taux (%)"]>0]
        if len(pts_r)>3:
            try:
                z=np.polyfit(pts_r["Taux (%)"],pts_r["Moyenne"],1); p=np.poly1d(z)
                xl=np.linspace(0,100,50)
                fig_sc.add_trace(go.Scatter(x=xl,y=p(xl),mode="lines",name="Tendance",
                    line=dict(color="#4a6cf7",width=2,dash="dash"),hoverinfo="skip"))
                corr=round(pts_r["Taux (%)"].corr(pts_r["Moyenne"]),3)
                interp=("forte positive" if corr>0.6 else "modérée" if corr>0.3 else "faible")
                st.info(f"**Corrélation présence / notes : {corr}** — {interp}")
            except: pass
        fig_sc.update_layout(paper_bgcolor="white",plot_bgcolor="white",
            font=dict(family="DM Sans",color="#2c3e7a"),
            xaxis=dict(title="Taux présence (%)",range=[-5,110],gridcolor="#f0f4ff"),
            yaxis=dict(title="Moyenne /20",range=[0,21],gridcolor="#f0f4ff"),
            height=460,margin=dict(t=40,b=40,l=50,r=20))
        st.plotly_chart(fig_sc,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# COURBES
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

# ─────────────────────────────────────────────────────────────────────────────
# TENDANCE
# ─────────────────────────────────────────────────────────────────────────────
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
    st.dataframe(pd.DataFrame({"Évaluation":note_cols,"Moyenne":[round(v,2) for v in moy_e],
        "Médiane":[round(v,2) for v in med_e],"Max":[int(v) for v in max_e],
        "Min":[int(v) for v in min_e],"Écart-type":[round(v,2) for v in std_e]}),
        use_container_width=True,hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────────────────────
with tab_stats:
    st.markdown('<div class="section-title">📋 Stats détaillées par agent</div>',unsafe_allow_html=True)
    df_f=df_stats[(df_stats["Moyenne"]>=note_range[0])&(df_stats["Moyenne"]<=note_range[1])]\
         .sort_values("Moyenne",ascending=False).reset_index(drop=True)
    df_f.index+=1
    st.dataframe(df_f.style.apply(style_note_row,axis=1).format(
        {"Moyenne":"{:.2f}","Médiane":"{:.2f}","Écart-type":"{:.2f}","Max":"{:.0f}","Min":"{:.0f}"}),
        use_container_width=True,height=500)
    buf_s=io.BytesIO()
    with pd.ExcelWriter(buf_s,engine="openpyxl") as w:
        df.to_excel(w,sheet_name="Notes brutes",index=False)
        df_stats.to_excel(w,sheet_name="Statistiques",index=False)
    st.download_button("⬇️ Exporter stats (Excel)",buf_s.getvalue(),
        file_name="stats_notes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ─────────────────────────────────────────────────────────────────────────────
# HEATMAP
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# CLASSEMENT
# ─────────────────────────────────────────────────────────────────────────────
with tab_podium:
    st.markdown('<div class="section-title">🏆 Classement général</div>',unsafe_allow_html=True)
    df_rk=df_stats.sort_values("Moyenne",ascending=False).reset_index(drop=True); df_rk.index+=1
    if len(df_rk)>=3:
        p2,p1,p3=st.columns([1,1.2,1])
        for col,rank,medal,bg in [(p1,1,"🥇","#FFF9C4"),(p2,2,"🥈","#F5F5F5"),(p3,3,"🥉","#FBE9E7")]:
            r=df_rk.iloc[rank-1]; ml,mc=mention_info(r["Moyenne"])
            col.markdown(f'<div style="background:{bg};border-radius:16px;padding:16px;'
                         f'text-align:center;box-shadow:0 4px 16px rgba(0,0,0,.07);">'
                         f'<div style="font-size:2rem;">{medal}</div>'
                         f'<div style="font-weight:700;color:#2c3e7a;font-size:.9rem;">{r["Agent"]}</div>'
                         f'<div style="font-size:1.8rem;font-weight:700;color:#4a6cf7;">{r["Moyenne"]:.2f}</div>'
                         f'<span class="{mc}">{ml}</span></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)
    cb=["#2d6a4f" if m>=16 else "#1a56db" if m>=14 else "#92400e" if m>=10 else "#b91c1c"
        for m in df_rk["Moyenne"]]
    fig_b=go.Figure(go.Bar(x=df_rk["Moyenne"],y=df_rk["Agent"],orientation="h",
        marker=dict(color=cb,line=dict(color="white",width=0.5)),
        text=[f"{v:.2f}" for v in df_rk["Moyenne"]],textposition="outside"))
    fig_b.update_layout(paper_bgcolor="white",plot_bgcolor="white",
        font=dict(family="DM Sans",color="#2c3e7a"),
        xaxis=dict(range=[0,23],gridcolor="#f0f4ff"),yaxis=dict(autorange="reversed",tickfont=dict(size=10)),
        height=max(400,len(agents)*28),margin=dict(t=20,b=40,l=230,r=60),showlegend=False)
    st.plotly_chart(fig_b,use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — tout en un
# ─────────────────────────────────────────────────────────────────────────────
with tab_admin:
    st.markdown('<div class="section-title">🔐 Espace Administrateur</div>',unsafe_allow_html=True)

    if not st.session_state.admin_logged_in:
        pwd=st.text_input("Mot de passe",type="password",placeholder="Entrez le mot de passe admin")
        if st.button("🔓 Se connecter",type="primary",use_container_width=True):
            if pwd==get_admin_pwd():
                st.session_state.admin_logged_in=True; st.rerun()
            else: st.error("❌ Mot de passe incorrect")
        st.caption("Mot de passe par défaut : `sans_dohi` (modifiable par Admin)")
    else:
        cola,colb=st.columns([2,1])
        with cola: st.success("✅ Connecté en tant qu'administrateur")
        with colb:
            if st.button("🚪 Déconnexion",use_container_width=True):
                st.session_state.admin_logged_in=False; st.rerun()

        st.markdown("---")

        # ── Sous-onglets admin ────────────────────────────────────────────
        a1,a2,a3,a4,a5 = st.tabs([
            "📊 Import notes",
            "📷 Pointage QR",
            "🎫 Générer QR",
            "🗓️ Sessions",
            "📋 Pointages",
        ])

        # ── A1 : Import notes ─────────────────────────────────────────────
        with a1:
            st.markdown('<div class="section-title">Importer les notes (visible par tous immédiatement)</div>',
                        unsafe_allow_html=True)
            src=st.radio("Source",["📁 Fichier Excel","🔗 Google Sheets"],horizontal=True)
            if "Excel" in src:
                fn=st.file_uploader("Fichier Excel des notes",type=["xlsx","xls"],key="adm_notes")
                if fn and st.button("✅ Publier pour tous",type="primary",use_container_width=True):
                    try:
                        df_new=pd.read_excel(fn); df_new.columns=df_new.columns.astype(str).str.strip()
                        shared["notes"]=df_new.to_dict("records")
                        shared["notes_label"]=f"Excel importé — {df_new.shape[0]} agents"
                        st.success(f"✅ {df_new.shape[0]} agents publiés pour tous les utilisateurs !"); st.rerun()
                    except Exception as e: st.error(str(e))
            else:
                url_gs=st.text_input("URL Google Sheets",placeholder="https://docs.google.com/spreadsheets/d/...")
                if st.button("✅ Publier pour tous",type="primary",use_container_width=True):
                    if url_gs:
                        df_new,err=load_gsheet(url_gs)
                        if err: st.error(err)
                        else:
                            shared["notes"]=df_new.to_dict("records")
                            shared["notes_label"]=f"Google Sheets — {df_new.shape[0]} agents"
                            st.success(f"✅ {df_new.shape[0]} agents depuis Google Sheets !"); st.rerun()
            if shared["notes"] is not None:
                st.markdown("---")
                if st.button("🔄 Revenir aux données par défaut"):
                    shared["notes"]=None; shared["notes_label"]="Données par défaut"; st.rerun()

        # ── A2 : Pointage QR ──────────────────────────────────────────────
        with a2:
            st.markdown('<div class="section-title">📷 Scan QR Code — Pointage</div>',unsafe_allow_html=True)
            st.markdown(f"**Session active :** `{st.session_state.session_active}`")

            c_scan,c_manual=st.columns([1.2,1])
            with c_scan:
                if not st.session_state.camera_on:
                    if st.button("📷 Ouvrir la caméra",type="primary",use_container_width=True):
                        st.session_state.camera_on=True
                        st.session_state.last_scan_agent=None
                        st.rerun()
                else:
                    if st.button("🔴 Fermer la caméra",type="secondary",use_container_width=True):
                        st.session_state.camera_on=False; st.rerun()
                    if st.session_state.last_scan_agent:
                        st.markdown(f'<div class="scan-ok">✅ <b>{st.session_state.last_scan_agent}</b>'
                                    f' pointé à {st.session_state.last_scan_time}<br>'
                                    f'<small>Prêt pour le prochain agent…</small></div>',
                                    unsafe_allow_html=True)
                    if QR_OK:
                        st.caption("📸 Présentez le badge QR devant la caméra — détection automatique")
                        qr_val=qrcode_scanner(key="admin_qr_scanner")
                        if qr_val:
                            agent_found=key_to_agent(str(qr_val))
                            if agent_found in agents:
                                deja,heure=is_already_pointed(agent_found,st.session_state.session_active)
                                if not deja:
                                    add_presence_shared(agent_found,st.session_state.session_active)
                                    st.session_state.last_scan_agent=agent_found
                                    st.session_state.last_scan_time=datetime.datetime.now().strftime("%H:%M:%S")
                                    st.rerun()
                                else:
                                    st.warning(f"ℹ️ **{agent_found}** déjà pointé à {heure}")
                            else:
                                st.error(f"❌ Agent non reconnu : `{agent_found}`\n\n"
                                         f"Vérifiez que ce QR a été généré depuis cet onglet **🎫 Générer QR**.")
                    else:
                        st.error("❌ Module `streamlit-qrcode-scanner` non installé. "
                                 "Vérifiez requirements.txt.")

            with c_manual:
                st.markdown("**Pointage manuel**")
                with st.form("form_manual_admin"):
                    ag=st.selectbox("Agent",agents)
                    stat=st.selectbox("Statut",["Présent","En retard","Excusé"])
                    ok=st.form_submit_button("✅ Enregistrer",use_container_width=True)
                    if ok:
                        deja,heure=is_already_pointed(ag,st.session_state.session_active)
                        if not deja:
                            add_presence_shared(ag,st.session_state.session_active,stat)
                            st.success(f"✅ **{ag}** — {stat}"); st.rerun()
                        else: st.info(f"ℹ️ Déjà pointé à {heure}")

            # Journal du jour
            st.markdown('<div class="section-title">Journal du jour</div>',unsafe_allow_html=True)
            today=datetime.date.today().strftime("%d/%m/%Y")
            pres_j=get_presences_df()
            jour_df=pres_j[(pres_j["Session"]==st.session_state.session_active)&
                           (pres_j["Date"]==today)].sort_values("Heure",ascending=False).reset_index(drop=True)
            if len(jour_df)>0:
                st.dataframe(jour_df,use_container_width=True,hide_index=True,height=280)
                bj=io.BytesIO(); jour_df.to_csv(bj,index=False,encoding="utf-8-sig")
                st.download_button("⬇️ Exporter journal",bj.getvalue(),
                    file_name=f"journal_{today.replace('/','_')}.csv",mime="text/csv")
            else: st.info("Aucun pointage aujourd'hui pour cette session.")

        # ── A3 : Générer QR ───────────────────────────────────────────────
        with a3:
            st.markdown('<div class="section-title">🎫 Générer les badges QR</div>',unsafe_allow_html=True)
            st.caption(f"{len(agents)} agents · 1 QR code unique par agent · Téléchargement ZIP")
            ags=st.multiselect("Agents (vide = tous)",options=agents,placeholder="Tous les agents")
            qsz=st.selectbox("Taille",["Petite","Normale","Grande"],index=1)
            qbox={"Petite":4,"Normale":6,"Grande":8}[qsz]
            agen_g=ags if ags else agents
            if st.button(f"🔄 Générer {len(agen_g)} QR Code(s)",type="primary",use_container_width=True):
                zb=io.BytesIO(); prev=[]
                with zipfile.ZipFile(zb,"w",zipfile.ZIP_DEFLATED) as zf:
                    prg=st.progress(0,text="Génération…")
                    for i,agent in enumerate(agen_g):
                        qo=qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_H,
                                          box_size=qbox,border=3)
                        qo.add_data(agent_to_qr_key(agent)); qo.make(fit=True)
                        img=qo.make_image(fill_color="#2c3e7a",back_color="white")
                        bf=io.BytesIO(); img.save(bf,format="PNG"); bf.seek(0); raw=bf.getvalue()
                        zf.writestr(f"QR_Badges/{agent[:60].replace('/','_')}.png",raw)
                        prev.append({"name":agent,"b64":base64.b64encode(raw).decode()})
                        prg.progress((i+1)/len(agen_g),text=f"{i+1}/{len(agen_g)} — {agent[:28]}…")
                    prg.empty()
                zb.seek(0)
                st.success(f"✅ {len(agen_g)} QR codes générés !")
                st.download_button(f"⬇️ Télécharger ZIP ({len(agen_g)} badges)",
                    data=zb.getvalue(),file_name="QR_Badges_Formation.zip",
                    mime="application/zip",use_container_width=True)
                hg='<div class="qr-grid">'
                for p in prev:
                    hg+=(f'<div class="qr-item"><img src="data:image/png;base64,{p["b64"]}" '
                         f'style="width:100%;border-radius:5px">'
                         f'<div class="qr-name">{p["name"][:35]}</div></div>')
                st.markdown(hg+'</div>',unsafe_allow_html=True)

        # ── A4 : Sessions ─────────────────────────────────────────────────
        with a4:
            st.markdown('<div class="section-title">🗓️ Configurer les sessions</div>',unsafe_allow_html=True)
            st.caption("Modifiez la liste des sessions de formation. Visible de tous.")
            txt=st.text_area("Sessions (1 par ligne)",
                value="\n".join(shared["sessions_config"]),height=180)
            if st.button("💾 Sauvegarder",type="primary",use_container_width=True):
                ns=[s.strip() for s in txt.split("\n") if s.strip()]
                if ns: shared["sessions_config"]=ns; st.success(f"✅ {len(ns)} sessions configurées."); st.rerun()
                else: st.error("Liste vide.")

        # ── A5 : Pointages ────────────────────────────────────────────────
        with a5:
            st.markdown('<div class="section-title">📋 Gestion des pointages</div>',unsafe_allow_html=True)
            pres_all=get_presences_df()
            if len(pres_all)>0:
                st.dataframe(pres_all,use_container_width=True,height=260)
                ca,cb,cc=st.columns(3)
                with ca:
                    bc=io.BytesIO(); pres_all.to_csv(bc,index=False,encoding="utf-8-sig")
                    st.download_button("⬇️ Export CSV",bc.getvalue(),file_name="pointages.csv",
                        mime="text/csv",use_container_width=True)
                with cb:
                    bx=io.BytesIO()
                    with pd.ExcelWriter(bx,engine="openpyxl") as w:
                        pres_all.to_excel(w,sheet_name="Pointages",index=False)
                    st.download_button("⬇️ Export Excel",bx.getvalue(),file_name="pointages.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)
                with cc:
                    if st.button("🗑️ Tout effacer",type="secondary",use_container_width=True):
                        shared["presences"].clear(); st.success("Effacé."); st.rerun()
            else: st.info("Aucun pointage enregistré.")
            st.markdown("**Importer un CSV de pointages (fusion)**")
            fi=st.file_uploader("CSV",type=["csv"],key="adm_pres")
            if fi and st.button("✅ Fusionner",use_container_width=True):
                try:
                    dfi=pd.read_csv(fi)
                    if {"Agent","Date","Heure","Session","Statut"}.issubset(set(dfi.columns)):
                        exist={(p["Agent"],p["Date"],p["Session"]) for p in shared["presences"]}
                        added=0
                        for _,row in dfi.iterrows():
                            k=(row["Agent"],row["Date"],row["Session"])
                            if k not in exist:
                                shared["presences"].append(row.to_dict()); exist.add(k); added+=1
                        st.success(f"✅ {added} pointages ajoutés."); st.rerun()
                    else: st.error("Colonnes manquantes.")
                except Exception as e: st.error(str(e))

# ── EXPORT GLOBAL ──────────────────────────────────────────────────────────
st.markdown("---")
buf_fin=io.BytesIO()
with pd.ExcelWriter(buf_fin,engine="openpyxl") as w:
    df.to_excel(w,sheet_name="Notes",index=False)
    df_stats.to_excel(w,sheet_name="Stats notes",index=False)
    pf=get_presences_df()
    if len(pf)>0:
        pf.to_excel(w,sheet_name="Pointages",index=False)
        presence_stats(agents).to_excel(w,sheet_name="Stats présences",index=False)
st.download_button("⬇️ Export complet (Excel — toutes feuilles)",buf_fin.getvalue(),
    file_name="formation_complet.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.caption("Plateforme Formation · v6.0 · Données partagées en temps réel · Admin intégré")
