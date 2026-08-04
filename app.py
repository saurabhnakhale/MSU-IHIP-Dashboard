"""
MSU · IDSP Disease Surveillance Report — Nagpur
Executive Power BI-Style Streamlit Dashboard.

Features:
- Dual Logo Header (NCDC.png Left, NMC.png Right with enlarged dimensions).
- Cohesive Soft Ice/Slate Full-Dashboard Background Theme.
- Live Google Sheets Sync with local CSV backup fallback.
- Large Custom Signages on KPI Cards.
- Sequential/Cascading Filters (Dropdowns update based on previous selections).
- Linked Analysis: Form & Time selections dynamically update BOTH left and right panels.
- Standalone NMC vs Outside Cases Section with search box.
"""

import base64
import io
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Config & Data Sources
# ----------------------------------------------------------------------------
GOOGLE_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/1NOtov-_mTp-KLWQ9RUjgm2T4ku3U3xSHZfMzoR_IuCc/export?format=csv"
)

DATA_PATH = Path(__file__).parent / "data" / "MSU_IDSP_Disease_Surveillance.csv"

# Updated Logo File Names matching your GitHub Repository
NCDC_LOGO_PATH = Path(__file__).parent / "NCDC.png"
NMC_LOGO_PATH = Path(__file__).parent / "NMC.png"

# Professional Color Palette
PALETTE = {
    "primary": "#1E40AF",     # Executive Blue
    "secondary": "#6D28D9",   # Deep Purple
    "teal": "#0D9488",        # Vibrant Teal
    "amber": "#D97706",       # Deep Amber
    "rose": "#BE123C",        # Crimson Rose
    "emerald": "#047857",     # Deep Emerald
    "bg_main": "#F1F5F9",     # Soft Slate Background
}

REQUIRED_COLUMNS = [
    "Date", "Disease", "P Form", "L Form", "Tested Cases", "NMC",
    "Outside", "Positivity Rate", "Visit Status", "Year", "Month", "Total"
]

st.set_page_config(
    page_title="MSU IDSP Disease Surveillance Report — Nagpur",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Function to encode local images to Base64 for inline HTML embedding
def get_image_base64(path):
    if path.exists():
        with open(path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return ""

ncdc_logo_b64 = get_image_base64(NCDC_LOGO_PATH)
nmc_logo_b64 = get_image_base64(NMC_LOGO_PATH)

# ----------------------------------------------------------------------------
# Custom CSS (Full Dashboard Background + Dual Logo Banner)
# ----------------------------------------------------------------------------
st.markdown(f"""
<style>
/* Full Page Background */
.stApp {{
  background-color: #F1F5F9;
  font-family: "Segoe UI", -apple-system, Arial, sans-serif;
}}

/* Expand dashboard to screen edges by removing max-width and overriding side paddings */
.block-container {{ 
  padding-top: 1rem !important; 
  padding-bottom: 2rem !important; 
  padding-left: 1.5rem !important; 
  padding-right: 1.5rem !important; 
  max-width: 100% !important; 
}}

/* AGGRESSIVELY REDUCE SIDEBAR TOP PADDING */
[data-testid="stSidebarHeader"] {{
  padding-top: 1rem !important;
  padding-bottom: 0rem !important;
  min-height: auto !important;
}}
[data-testid="stSidebarUserContent"] {{
  padding-top: 0rem !important;
}}
/* Remove margin from the very first h3 tag in sidebar to push it even higher */
[data-testid="stSidebarUserContent"] h3:first-of-type {{
  margin-top: 0rem !important;
  padding-top: 0rem !important;
}}

/* Keep the Streamlit header transparent so it doesn't block the pushed-up content */
[data-testid="stHeader"] {{
  background-color: transparent !important;
}}

/* Autohide the top-right toolbar (Fork, Menu, GitHub) to free up visual space */
[data-testid="stToolbar"] {{
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
  z-index: 9999;
}}
[data-testid="stToolbar"]:hover {{
  opacity: 1;
}}

/* Hide default menus and footer */
#MainMenu, footer {{visibility: hidden;}}

/* Executive Dual-Logo Banner */
.titlebar {{
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  color: #FFFFFF;
  padding: 16px 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}
.titlebar .brand-container {{
  display: flex;
  align-items: center;
  gap: 16px;
  text-align: center;
}}
.titlebar .brand-title {{
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.3px;
  color: #FFFFFF;
  line-height: 1.2;
}}
.titlebar .subtext {{
  font-size: 11px;
  color: #94A3B8;
  font-weight: 500;
  margin-top: 4px;
}}

/* Increased Logo Dimensions */
.header-logo {{
  height: 85px;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 2px 5px rgba(0,0,0,0.4));
}}

/* 3D Dynamic KPI Cards */
.pbi-card {{
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
  padding: 14px 16px;
  margin-bottom: 8px;
}}
.kpi-label {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #64748B; }}
.kpi-value-container {{ display: flex; align-items: center; justify-content: space-between; margin-top: 6px; }}
.kpi-value {{ font-size: 26px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px; }}
.kpi-signage {{ font-size: 32px; line-height: 1; margin-left: 8px; }}
.kpi-accent {{ height: 4px; border-radius: 2px; margin-bottom: 8px; }}

.badge-ok {{ background: #DCFCE7; color: #15803D; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700; }}
.badge-warn {{ background: #FEE2E2; color: #B91C1C; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 700; }}

.section-title {{ font-size: 14px; font-weight: 800; color: #0F172A; margin: 8px 0 8px 2px; text-transform: uppercase; letter-spacing: 0.4px; }}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Data loading + validation
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=60)
def load_csv(path_or_url_or_buffer, cache_key: str) -> pd.DataFrame:
    df = pd.read_csv(path_or_url_or_buffer)
    df.columns = [c.strip() for c in df.columns]
    return df


def validate_and_clean(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return None, {"ok": False, "missing": missing}

    numeric_cols = ["P Form", "L Form", "Tested Cases", "NMC", "Outside", "Positivity Rate", "Total"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    week_col = "Week " if "Week " in df.columns else "Week"
    df = df.rename(columns={week_col: "Week"})
    df["Disease"] = df["Disease"].astype(str).str.strip()
    df = df[df["Disease"].notna() & (df["Disease"] != "") & (df["Disease"] != "nan")]

    df["Date_dt"] = pd.to_datetime(df["Date"], errors="coerce")

    sums = {
        "pform": df["P Form"].fillna(0).sum(),
        "lform": df["L Form"].fillna(0).sum(),
        "tested": df["Tested Cases"].fillna(0).sum(),
        "nmc": df["NMC"].fillna(0).sum(),
        "outside": df["Outside"].fillna(0).sum(),
        "total": df["Total"].fillna(0).sum(),
    }
    expected_total = sums["pform"] + sums["lform"]
    reconciles = abs(expected_total - sums["total"]) < max(1, len(df) * 0.5)

    meta = {"ok": True, "rows": len(df), "sums": sums, "reconciles": reconciles}
    return df, meta


# ----------------------------------------------------------------------------
# Sidebar setup
# ----------------------------------------------------------------------------
if "cache_bust" not in st.session_state:
    st.session_state.cache_bust = 0
if "last_refreshed" not in st.session_state:
    st.session_state.last_refreshed = datetime.now()
# Session state key to reset filters
if "filter_key" not in st.session_state:
    st.session_state.filter_key = 0

with st.sidebar:
    st.markdown("### 🔄 Data Source Controls")
    if st.button("Refresh Live Data", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.session_state.cache_bust += 1
        st.session_state.last_refreshed = datetime.now()
        st.rerun()

    uploaded = st.file_uploader("Upload Override CSV", type=["csv"], help="Overrides Google Sheet data for this session.")
    st.markdown("---")

# ----------------------------------------------------------------------------
# Data Loading Execution
# ----------------------------------------------------------------------------
if uploaded is not None:
    raw_df = load_csv(io.BytesIO(uploaded.getvalue()), cache_key=f"upload-{uploaded.name}-{uploaded.size}")
    source_label = f"Uploaded File: {uploaded.name}"
else:
    try:
        raw_df = load_csv(GOOGLE_SHEET_CSV_URL, cache_key=f"gsheet-{st.session_state.cache_bust}")
        source_label = "Google Sheets (Live Sync)"
    except Exception:
        st.sidebar.warning("Could not sync with Google Sheets. Loading local backup file.")
        raw_df = load_csv(DATA_PATH, cache_key=f"repo-{st.session_state.cache_bust}")
        source_label = f"Local Backup: {DATA_PATH.name}"

df, meta = validate_and_clean(raw_df)

if not meta["ok"]:
    st.error(f"Could not load data — missing required columns: {', '.join(meta['missing'])}")
    st.stop()

# ----------------------------------------------------------------------------
# Sidebar Cascading Slicers (Dynamically Linked)
# ----------------------------------------------------------------------------
with st.sidebar:
    
    c_title, c_reset = st.columns([2, 1])
    with c_title:
        st.markdown("<h3 style='margin-bottom: 0px;'>Filters 🔍</h3>", unsafe_allow_html=True)
    with c_reset:
        if st.button("Reset", use_container_width=True):
            st.session_state.filter_key += 1 
            st.rerun()

    min_date = df["Date_dt"].min().date() if df["Date_dt"].notna().any() else datetime.today().date()
    max_date = df["Date_dt"].max().date() if df["Date_dt"].notna().any() else datetime.today().date()
    
    st.markdown("<div style='font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 0px; margin-top: 10px;'>Date Window</div>", unsafe_allow_html=True)
    col_start, col_end = st.columns(2)
    with col_start:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY", key=f"start_{st.session_state.filter_key}")
    with col_end:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY", key=f"end_{st.session_state.filter_key}")

    temp_df = df.copy()
    temp_df = temp_df[(temp_df["Date_dt"].dt.date >= start_date) & (temp_df["Date_dt"].dt.date <= end_date)]

    available_months = sorted(temp_df["Month"].dropna().unique().tolist())
    sel_months = st.multiselect("Month", available_months, default=[], key=f"month_{st.session_state.filter_key}")
    
    if sel_months:
        temp_df = temp_df[temp_df["Month"].isin(sel_months)]

    available_weeks = sorted(temp_df["Week"].dropna().unique().tolist())
    sel_weeks = st.multiselect("Epi Week", available_weeks, default=[], key=f"week_{st.session_state.filter_key}")
    
    if sel_weeks:
        temp_df = temp_df[temp_df["Week"].isin(sel_weeks)]

    available_status = sorted(temp_df["Visit Status"].dropna().unique().tolist())
    sel_status = st.multiselect("Visit Status", available_status, default=[], key=f"status_{st.session_state.filter_key}")
    
    if sel_status:
        temp_df = temp_df[temp_df["Visit Status"].isin(sel_status)]

    disease_totals = (temp_df.groupby("Disease")[["P Form", "L Form"]].sum().sum(axis=1).sort_values(ascending=False))
    disease_options = disease_totals.index.tolist()
    sel_diseases = st.multiselect("Select Disease", disease_options, default=[], key=f"disease_{st.session_state.filter_key}")

    if sel_diseases:
        temp_df = temp_df[temp_df["Disease"].isin(sel_diseases)]

filtered = temp_df.copy()

# ----------------------------------------------------------------------------
# Dual Logo Header Title Bar
# ----------------------------------------------------------------------------
badge = ('<span class="badge-ok">✓ Reconciled</span>' if meta["reconciles"] else '<span class="badge-warn">⚠ Check Totals</span>')

st.markdown(f"""
<div class="titlebar">
  <div>
    <img src="{ncdc_logo_b64}" class="header-logo" alt="NCDC Logo"/>
  </div>
  <div class="brand-container">
    <div>
      <div class="brand-title">MSU · IDSP Disease Surveillance Report — Nagpur</div>
      <div class="subtext">
        Source: <b>{source_label}</b> &nbsp;·&nbsp; {meta['rows']:,} Records &nbsp;·&nbsp;
        Refreshed {st.session_state.last_refreshed.strftime('%d %b %Y, %H:%M')} &nbsp;·&nbsp; {badge}
      </div>
    </div>
  </div>
  <div>
    <img src="{nmc_logo_b64}" class="header-logo" alt="NMC Logo"/>
  </div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# KPI Cards
# ----------------------------------------------------------------------------
total_pform = filtered["P Form"].fillna(0).sum()
total_lform = filtered["L Form"].fillna(0).sum()
total_tested = filtered["Tested Cases"].fillna(0).sum()
pos_rows = filtered["Positivity Rate"].dropna()
avg_positivity = pos_rows.mean() if len(pos_rows) else 0
active_diseases = filtered.loc[(filtered["P Form"].fillna(0) + filtered["L Form"].fillna(0)) > 0, "Disease"].nunique()

kpis = [
    ("Total P-Form Cases", f"{total_pform:,.0f}", PALETTE["primary"], "💊"),
    ("Total L-Form Cases", f"{total_lform:,.0f}", PALETTE["secondary"], "🧪"),
    ("Samples Tested", f"{total_tested:,.0f}", PALETTE["amber"], "🔬"),
    ("Avg Lab Positivity", f"{avg_positivity:.1f}%", PALETTE["rose"], "🥼"),
    ("Diseases Reporting", f"{active_diseases:,}", PALETTE["emerald"], "📊"),
]

cols = st.columns(5)
for col, (label, value, color, signage) in zip(cols, kpis):
    with col:
        st.markdown(f"""
        <div class="pbi-card">
          <div class="kpi-accent" style="background:{color}"></div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value-container">
             <div class="kpi-value">{value}</div>
             <div class="kpi-signage">{signage}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Plotly Card Layout Helper
# ----------------------------------------------------------------------------
def apply_pbi_layout(fig, height=320, show_legend=False):
    fig.update_layout(
        height=height,
        margin=dict(l=15, r=15, t=15, b=15),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Segoe UI, Arial", size=11, color="#334155"),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5) if show_legend else None,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", zeroline=False)
    return fig


# ----------------------------------------------------------------------------
# Section 1: Visual Trends (Dynamically Linked Left & Right Panels)
# ----------------------------------------------------------------------------
c_left_panel, c_right_panel = st.columns([1.35, 1])

with c_left_panel:
    st.markdown('<div class="section-title">📊 Visual Trends & Lab Breakdowns</div>', unsafe_allow_html=True)
    
    # Master controls for both left and right charts
    c_form, c_time = st.columns([1.2, 1])
    with c_form:
        form_choice = st.radio(
            "Select Form Type:",
            ["📋 P-Form (Syndromic)", "🧪 L-Form (Lab Confirmed)"],
            horizontal=True,
            label_visibility="collapsed"
        )
    with c_time:
        time_choice = st.radio(
            "Select Time Granularity:",
            ["📅 Daily", "🗓️ Weekly", "📆 Monthly"],
            horizontal=True,
            label_visibility="collapsed"
        )

    # Dynamic variables based on selection
    is_pform = "P-Form" in form_choice
    target_col = "P Form" if is_pform else "L Form"
    trend_color = PALETTE["primary"] if is_pform else PALETTE["secondary"]
    fill_color = "rgba(30, 64, 175, 0.12)" if is_pform else "rgba(109, 40, 217, 0.12)"
    
    # Render Left Chart based on Master Time Toggle
    if "Daily" in time_choice:
        daily_data = filtered.groupby("Date_dt")[target_col].sum().sort_index() if not filtered.empty else pd.Series(dtype=float)
        fig = go.Figure(go.Scatter(
            x=daily_data.index, y=daily_data.values, mode="lines+markers",
            line=dict(color=trend_color, width=3),
            fill="tozeroy", fillcolor=fill_color
        ))
        st.plotly_chart(apply_pbi_layout(fig), use_container_width=True, config={"displayModeBar": False}, key="trend_daily")

    elif "Weekly" in time_choice:
        wk_data = filtered.groupby("Week")[target_col].sum().sort_index() if not filtered.empty else pd.Series(dtype=float)
        fig = go.Figure(go.Bar(
            x=[f"W{int(w)}" for w in wk_data.index if pd.notna(w)], y=wk_data.values,
            marker=dict(color=trend_color)
        ))
        st.plotly_chart(apply_pbi_layout(fig), use_container_width=True, config={"displayModeBar": False}, key="trend_weekly")

    elif "Monthly" in time_choice:
        mo_data = filtered.groupby("Month")[target_col].sum() if not filtered.empty else pd.Series(dtype=float)
        fig = go.Figure(go.Bar(
            x=mo_data.index, y=mo_data.values,
            marker=dict(color=trend_color)
        ))
        st.plotly_chart(apply_pbi_layout(fig), use_container_width=True, config={"displayModeBar": False}, key="trend_monthly")


with c_right_panel:
    # Right panel title dynamically reflects both Form and Time choices
    form_label = "P-Form" if is_pform else "L-Form"
    time_label = time_choice.split()[1] # Extracts "Daily", "Weekly", or "Monthly"
    metric_label = "Avg" if time_label != "Monthly" else "Total"
    
    st.markdown(f'<div class="section-title">🏆 Top Conditions ({form_label} - {time_label} {metric_label})</div>', unsafe_allow_html=True)
    
    # Spacer to align the top of this chart with the left chart (compensating for the height of the toggle buttons)
    st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True)

    # Render Right Chart based on Master Time Toggle
    if "Daily" in time_choice:
        n_days = filtered["Date_dt"].nunique() or 1
        top_d = (filtered.groupby("Disease")[target_col].sum() / n_days).sort_values(ascending=False).head(8).sort_values() if not filtered.empty else pd.Series(dtype=float)
        fig_td = go.Figure(go.Bar(
            x=top_d.values, y=top_d.index, orientation="h",
            marker=dict(color=PALETTE["teal"])
        ))
        st.plotly_chart(apply_pbi_layout(fig_td, height=360), use_container_width=True, config={"displayModeBar": False}, key="top_daily")

    elif "Weekly" in time_choice:
        n_wks = filtered["Week"].nunique() or 1
        top_w = (filtered.groupby("Disease")[target_col].sum() / n_wks).sort_values(ascending=False).head(8).sort_values() if not filtered.empty else pd.Series(dtype=float)
        fig_tw = go.Figure(go.Bar(
            x=top_w.values, y=top_w.index, orientation="h",
            marker=dict(color=PALETTE["rose"])
        ))
        st.plotly_chart(apply_pbi_layout(fig_tw, height=360), use_container_width=True, config={"displayModeBar": False}, key="top_weekly")

    elif "Monthly" in time_choice:
        top_m = filtered.groupby("Disease")[target_col].sum().sort_values(ascending=False).head(8).sort_values() if not filtered.empty else pd.Series(dtype=float)
        fig_tm = go.Figure(go.Bar(
            x=top_m.values, y=top_m.index, orientation="h",
            marker=dict(color=PALETTE["amber"])
        ))
        st.plotly_chart(apply_pbi_layout(fig_tm, height=360), use_container_width=True, config={"displayModeBar": False}, key="top_monthly")

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Section 2: Standalone NMC vs Outside Cases Visualization
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">📍 NMC vs Outside Regional Cases (L-Form Analysis)</div>', unsafe_allow_html=True)

col_search, _ = st.columns([1, 1])
with col_search:
    nmc_search = st.text_input("🔍 Search Disease for NMC/Outside Chart", key=f"standalone_nmc_search_{st.session_state.filter_key}")

nmc_df = filtered.groupby("Disease")[["NMC", "Outside"]].sum() if not filtered.empty else pd.DataFrame(columns=["NMC", "Outside"])
if nmc_search and not nmc_df.empty:
    nmc_df = nmc_df[nmc_df.index.str.lower().str.contains(nmc_search.lower())]

nmc_df = nmc_df[(nmc_df["NMC"] > 0) | (nmc_df["Outside"] > 0)].sort_values(by="NMC", ascending=True).tail(12)

if not nmc_df.empty:
    fig_nmc = go.Figure()
    fig_nmc.add_trace(go.Bar(
        y=nmc_df.index, x=nmc_df["NMC"], name="NMC Cases", orientation="h",
        marker=dict(color=PALETTE["teal"])
    ))
    fig_nmc.add_trace(go.Bar(
        y=nmc_df.index, x=nmc_df["Outside"], name="Outside Cases", orientation="h",
        marker=dict(color=PALETTE["amber"])
    ))
    fig_nmc.update_layout(barmode="group")
    st.plotly_chart(apply_pbi_layout(fig_nmc, height=350, show_legend=True), use_container_width=True, config={"displayModeBar": False}, key="nmc_vs_out_chart")
else:
    st.info("No matching records found for NMC / Outside disease analysis.")

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Section 3: Field Visit Status & Lab Positivity Rate
# ----------------------------------------------------------------------------
c_v1, c_v2 = st.columns(2)

with c_v1:
    st.markdown('<div class="section-title">Field Visit Status Breakdown</div>', unsafe_allow_html=True)
    vc = filtered["Visit Status"].value_counts() if not filtered.empty else pd.Series(dtype=float)
    colors_map = {"Traced": PALETTE["emerald"], "Visited": PALETTE["primary"], "Untraced": PALETTE["rose"]}
    fig_visit = go.Figure(go.Pie(
        labels=vc.index, values=vc.values, hole=0.55,
        marker=dict(colors=[colors_map.get(k, "#94A3B8") for k in vc.index])
    ))
    st.plotly_chart(apply_pbi_layout(fig_visit, height=270, show_legend=True), use_container_width=True, config={"displayModeBar": False}, key="visit_pie_chart")

with c_v2:
    st.markdown('<div class="section-title">Lab Positivity Rate (%)</div>', unsafe_allow_html=True)
    pos = filtered.dropna(subset=["Positivity Rate"]).groupby("Disease")["Positivity Rate"].mean() if not filtered.empty else pd.Series(dtype=float)
    pos = pos.sort_values(ascending=False).head(8)
    fig_pos = go.Figure(go.Bar(
        x=pos.index, y=pos.values,
        marker=dict(color=PALETTE["rose"])
    ))
    fig_pos.update_yaxes(ticksuffix="%")
    st.plotly_chart(apply_pbi_layout(fig_pos, height=270), use_container_width=True, config={"displayModeBar": False}, key="pos_bar_chart")

# ----------------------------------------------------------------------------
# Section 4: Comprehensive Disease Summary Table
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">📋 Comprehensive Disease Summary Matrix</div>', unsafe_allow_html=True)

if not filtered.empty:
    grp = filtered.groupby("Disease").agg(
        **{
            "P-Form": ("P Form", "sum"), 
            "L-Form": ("L Form", "sum"),
            "NMC": ("NMC", "sum"),
            "Outside": ("Outside", "sum"),
            "Tested": ("Tested Cases", "sum"), 
            "Avg Positivity %": ("Positivity Rate", "mean")
        }
    )
    grp = grp[(grp["P-Form"] + grp["L-Form"] + grp["Tested"]) > 0]
    grand_total = (grp["P-Form"] + grp["L-Form"]).sum() or 1
    grp["Share of Total %"] = (grp["P-Form"] + grp["L-Form"]) / grand_total * 100
    grp = grp.sort_values("P-Form", ascending=False).reset_index()

    st.dataframe(
        grp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "P-Form": st.column_config.NumberColumn(format="%.0f"),
            "L-Form": st.column_config.NumberColumn(format="%.0f"),
            "NMC": st.column_config.NumberColumn(format="%.0f"),
            "Outside": st.column_config.NumberColumn(format="%.0f"),
            "Tested": st.column_config.NumberColumn(format="%.0f"),
            "Avg Positivity %": st.column_config.NumberColumn(format="%.1f%%"),
            "Share of Total %": st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=float(grp["Share of Total %"].max() or 1)
            ),
        },
        height=380,
    )
else:
    st.info("No data available to display in the summary matrix for the selected filters.")

st.caption(
    f"Source: {source_label} · {meta['rows']:,} records · "
    f"P-Form Σ {meta['sums']['pform']:,.0f} · L-Form Σ {meta['sums']['lform']:,.0f} · "
    f"NMC Σ {meta['sums']['nmc']:,.0f} · Outside Σ {meta['sums']['outside']:,.0f}."
)
