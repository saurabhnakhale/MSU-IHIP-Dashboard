"""
MSU · IDSP Disease Surveillance Report
Power BI-style live dashboard built with Streamlit.

Data flow
---------
- Reads published Google Sheet directly (with local CSV fallback).
- Interactive tabs for Daily, Weekly, and Monthly breakdown of P-Form and L-Form cases.
- Dynamic Top Reported Conditions breakdown across Daily, Weekly, and Monthly aggregations.
"""

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

PALETTE = {
    "blue": "#118DFF", "blue_dk": "#12239E", "orange": "#E66C37", "purple": "#6B007B",
    "pink": "#E044A7", "violet": "#744EC2", "mustard": "#D9B300", "red": "#D64550",
    "green": "#107C10",
}
SERIES_COLORS = [
    PALETTE["blue"], PALETTE["orange"], PALETTE["violet"], PALETTE["pink"],
    PALETTE["mustard"], PALETTE["purple"], PALETTE["red"], PALETTE["green"]
]

REQUIRED_COLUMNS = [
    "Date", "Disease", "P Form", "L Form", "Tested Cases", "NMC",
    "Outside", "Positivity Rate", "Visit Status", "Year", "Month", "Total"
]

st.set_page_config(
    page_title="MSU IDSP Disease Surveillance Report",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------------
# Power BI-style CSS
# ----------------------------------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] { font-family: "Segoe UI", -apple-system, Arial, sans-serif; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px; }
#MainMenu, footer, header {visibility: hidden;}

.titlebar {
  background:#1B1A19; color:#fff; padding:8px 18px; border-radius:4px;
  display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;
  font-size:12.5px;
}
.titlebar .brand { display:flex; align-items:center; gap:8px; }
.titlebar .dot { width:7px; height:7px; border-radius:50%; background:#107C10; display:inline-block; margin-right:5px; }

.pbi-card {
  background:#FFFFFF; border:1px solid #E1DFDD; border-radius:4px;
  box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.10);
  padding:14px 16px; margin-bottom:6px;
}
.kpi-label { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.4px; color:#605E5C; }
.kpi-value { font-size:28px; font-weight:700; color:#252423; letter-spacing:-0.5px; margin-top:4px; }
.kpi-accent { height:3px; border-radius:2px; margin-bottom:8px; }

.badge-ok { background:#DFF6DD; color:#0B6A0B; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:700; }
.badge-warn { background:#FDE7E9; color:#A80000; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:700; }

.section-title { font-size:13px; font-weight:700; color:#252423; margin: 4px 0 6px 2px; }
hr { margin: 0.6rem 0; }
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

    # Standardize Datetime Column for Daily/Monthly Grouping
    df["Date_dt"] = pd.to_datetime(df["Date"], errors="coerce")

    sums = {
        "pform": df["P Form"].fillna(0).sum(),
        "lform": df["L Form"].fillna(0).sum(),
        "tested": df["Tested Cases"].fillna(0).sum(),
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

with st.sidebar:
    st.markdown("### 🔄 Data Source")
    if st.button("Refresh data", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.session_state.cache_bust += 1
        st.session_state.last_refreshed = datetime.now()
        st.rerun()

    uploaded = st.file_uploader("…or upload a local CSV", type=["csv"], help="Overrides Google Sheets for this session only.")
    st.markdown("---")

# ----------------------------------------------------------------------------
# Load Execution
# ----------------------------------------------------------------------------
if uploaded is not None:
    raw_df = load_csv(io.BytesIO(uploaded.getvalue()), cache_key=f"upload-{uploaded.name}-{uploaded.size}")
    source_label = f"Uploaded: {uploaded.name}"
else:
    try:
        raw_df = load_csv(GOOGLE_SHEET_CSV_URL, cache_key=f"gsheet-{st.session_state.cache_bust}")
        source_label = "Google Sheets (Live)"
    except Exception:
        st.sidebar.warning("Could not reach Google Sheets. Loading local backup file.")
        raw_df = load_csv(DATA_PATH, cache_key=f"repo-{st.session_state.cache_bust}")
        source_label = f"Local Fallback: {DATA_PATH.name}"

df, meta = validate_and_clean(raw_df)

if not meta["ok"]:
    st.error(f"Could not load data — missing required columns: {', '.join(meta['missing'])}")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.markdown("### 🔎 Filters")
    weeks = sorted(df["Week"].dropna().unique().tolist())
    sel_weeks = st.multiselect("Epi Week", weeks, default=[])

    statuses = sorted(df["Visit Status"].dropna().unique().tolist())
    sel_status = st.multiselect("Visit Status", statuses, default=[])

    disease_totals = (df.groupby("Disease")[["P Form", "L Form"]].sum().sum(axis=1).sort_values(ascending=False))
    search = st.text_input("Search disease")
    disease_options = [d for d in disease_totals.index if search.lower() in d.lower()]
    sel_diseases = st.multiselect("Disease", disease_options, default=[])

    if st.button("Clear all filters", use_container_width=True):
        st.rerun()

filtered = df.copy()
if sel_weeks:
    filtered = filtered[filtered["Week"].isin(sel_weeks)]
if sel_status:
    filtered = filtered[filtered["Visit Status"].isin(sel_status)]
if sel_diseases:
    filtered = filtered[filtered["Disease"].isin(sel_diseases)]

# ----------------------------------------------------------------------------
# Header / Title bar
# ----------------------------------------------------------------------------
badge = ('<span class="badge-ok">✓ Reconciled</span>' if meta["reconciles"] else '<span class="badge-warn">⚠ Check totals</span>')
st.markdown(f"""
<div class="titlebar">
  <div class="brand"><span class="dot"></span> MSU · IDSP Disease Surveillance Report — Nagpur</div>
  <div>Source: <b>{source_label}</b> &nbsp;·&nbsp; {meta['rows']:,} rows &nbsp;·&nbsp;
       Refreshed {st.session_state.last_refreshed.strftime('%d %b %Y, %H:%M')} &nbsp;·&nbsp; {badge}</div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------------
total_pform = filtered["P Form"].fillna(0).sum()
total_lform = filtered["L Form"].fillna(0).sum()
total_tested = filtered["Tested Cases"].fillna(0).sum()
pos_rows = filtered["Positivity Rate"].dropna()
avg_positivity = pos_rows.mean() if len(pos_rows) else 0
active_diseases = filtered.loc[(filtered["P Form"].fillna(0) + filtered["L Form"].fillna(0)) > 0, "Disease"].nunique()

kpis = [
    ("Total P-Form Cases", f"{total_pform:,.0f}", PALETTE["blue"]),
    ("Lab-Confirmed (L-Form)", f"{total_lform:,.0f}", PALETTE["violet"]),
    ("Samples Tested", f"{total_tested:,.0f}", PALETTE["orange"]),
    ("Avg Lab Positivity", f"{avg_positivity:.1f}%", PALETTE["red"]),
    ("Diseases Reporting", f"{active_diseases:,}", PALETTE["green"]),
]
cols = st.columns(5)
for col, (label, value, color) in zip(cols, kpis):
    with col:
        st.markdown(f"""
        <div class="pbi-card">
          <div class="kpi-accent" style="background:{color}"></div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Helper layout function for charts
def pbi_layout(fig, height=320, legend=True):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Segoe UI, Arial", size=11, color="#605E5C"),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5) if legend else None,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EDEBE9", zeroline=False)
    return fig


# ----------------------------------------------------------------------------
# Dynamic Graphs Section: Case Trends & Top Conditions
# ----------------------------------------------------------------------------
c_left, c_right = st.columns([1.3, 1])

with c_left:
    st.markdown('<div class="section-title">Case Trends (P-Form vs L-Form)</div>', unsafe_allow_html=True)
    tab_daily, tab_weekly, tab_monthly = st.tabs(["📅 Daily", "🗓️ Weekly", "📆 Monthly"])

    # 1. Daily View
    with tab_daily:
        daily_df = filtered.groupby("Date_dt")[["P Form", "L Form"]].sum().sort_index()
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Scatter(x=daily_df.index, y=daily_df["P Form"], name="P-Form (Daily)", line=dict(color=PALETTE["blue"], width=2)))
        fig_daily.add_trace(go.Scatter(x=daily_df.index, y=daily_df["L Form"], name="L-Form (Daily)", line=dict(color=PALETTE["violet"], width=2)))
        st.plotly_chart(pbi_layout(fig_daily), use_container_width=True, config={"displayModeBar": False})

    # 2. Weekly View
    with tab_weekly:
        weekly_df = filtered.groupby("Week")[["P Form", "L Form"]].sum().sort_index()
        fig_weekly = go.Figure()
        fig_weekly.add_bar(x=[f"W{int(w)}" for w in weekly_df.index if pd.notna(w)], y=weekly_df["P Form"], name="P-Form (Weekly)", marker_color=PALETTE["blue"])
        fig_weekly.add_bar(x=[f"W{int(w)}" for w in weekly_df.index if pd.notna(w)], y=weekly_df["L Form"], name="L-Form (Weekly)", marker_color=PALETTE["violet"])
        fig_weekly.update_layout(barmode="group")
        st.plotly_chart(pbi_layout(fig_weekly), use_container_width=True, config={"displayModeBar": False})

    # 3. Monthly View
    with tab_monthly:
        monthly_df = filtered.groupby("Month")[["P Form", "L Form"]].sum()
        fig_monthly = go.Figure()
        fig_monthly.add_bar(x=monthly_df.index, y=monthly_df["P Form"], name="P-Form (Monthly)", marker_color=PALETTE["blue"])
        fig_monthly.add_bar(x=monthly_df.index, y=monthly_df["L Form"], name="L-Form (Monthly)", marker_color=PALETTE["violet"])
        fig_monthly.update_layout(barmode="group")
        st.plotly_chart(pbi_layout(fig_monthly), use_container_width=True, config={"displayModeBar": False})

with c_right:
    st.markdown('<div class="section-title">Top Reported Conditions</div>', unsafe_allow_html=True)
    t_top_daily, t_top_weekly, t_top_monthly = st.tabs(["📅 Daily Avg", "🗓️ Weekly Total", "📆 Monthly Total"])

    # Daily Avg Top Conditions
    with t_top_daily:
        num_days = filtered["Date_dt"].nunique() or 1
        top_daily = (filtered.groupby("Disease")[["P Form", "L Form"]].sum().sum(axis=1) / num_days).sort_values(ascending=False).head(8).sort_values()
        fig_top_d = go.Figure(go.Bar(x=top_daily.values, y=top_daily.index, orientation="h", marker_color=PALETTE["orange"]))
        fig_top_d.update_layout(xaxis_title="Avg Cases / Day")
        st.plotly_chart(pbi_layout(fig_top_d, legend=False), use_container_width=True, config={"displayModeBar": False})

    # Weekly Total Top Conditions
    with t_top_weekly:
        num_weeks = filtered["Week"].nunique() or 1
        top_weekly = (filtered.groupby("Disease")[["P Form", "L Form"]].sum().sum(axis=1) / num_weeks).sort_values(ascending=False).head(8).sort_values()
        fig_top_w = go.Figure(go.Bar(x=top_weekly.values, y=top_weekly.index, orientation="h", marker_color=PALETTE["pink"]))
        fig_top_w.update_layout(xaxis_title="Avg Cases / Week")
        st.plotly_chart(pbi_layout(fig_top_w, legend=False), use_container_width=True, config={"displayModeBar": False})

    # Monthly Total Top Conditions
    with t_top_monthly:
        top_monthly = filtered.groupby("Disease")[["P Form", "L Form"]].sum().sum(axis=1).sort_values(ascending=False).head(8).sort_values()
        fig_top_m = go.Figure(go.Bar(x=top_monthly.values, y=top_monthly.index, orientation="h", marker_color=PALETTE["mustard"]))
        fig_top_m.update_layout(xaxis_title="Total Cases")
        st.plotly_chart(pbi_layout(fig_top_m, legend=False), use_container_width=True, config={"displayModeBar": False})

# ----------------------------------------------------------------------------
# Row 2: Visit Donut + Lab Positivity
# ----------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
c_v1, c_v2 = st.columns(2)

with c_v1:
    st.markdown('<div class="section-title">Field Visit Status</div>', unsafe_allow_html=True)
    vc = filtered["Visit Status"].value_counts()
    colors_map = {"Traced": PALETTE["green"], "Visited": PALETTE["blue"], "Untraced": PALETTE["red"]}
    fig_visit = go.Figure(go.Pie(
        labels=vc.index, values=vc.values, hole=0.6,
        marker_colors=[colors_map.get(k, "#8A8886") for k in vc.index]
    ))
    st.plotly_chart(pbi_layout(fig_visit, height=260, legend=True), use_container_width=True, config={"displayModeBar": False})

with c_v2:
    st.markdown('<div class="section-title">Lab Positivity Rate</div>', unsafe_allow_html=True)
    pos = filtered.dropna(subset=["Positivity Rate"]).groupby("Disease")["Positivity Rate"].mean()
    pos = pos.sort_values(ascending=False).head(8)
    fig_pos = go.Figure(go.Bar(x=pos.index, y=pos.values, marker_color=PALETTE["red"]))
    fig_pos.update_yaxes(ticksuffix="%")
    st.plotly_chart(pbi_layout(fig_pos, height=260, legend=False), use_container_width=True, config={"displayModeBar": False})

# ----------------------------------------------------------------------------
# Summary Table
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">Disease-wise Summary Matrix</div>', unsafe_allow_html=True)
grp = filtered.groupby("Disease").agg(
    **{"P-Form": ("P Form", "sum"), "L-Form": ("L Form", "sum"),
       "Tested": ("Tested Cases", "sum"), "Avg Positivity %": ("Positivity Rate", "mean")}
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
        "Tested": st.column_config.NumberColumn(format="%.0f"),
        "Avg Positivity %": st.column_config.NumberColumn(format="%.1f%%"),
        "Share of Total %": st.column_config.ProgressColumn(
            format="%.1f%%", min_value=0, max_value=float(grp["Share of Total %"].max() or 1)
        ),
    },
    height=380,
)

st.caption(
    f"Source: {source_label} · {meta['rows']:,} rows · "
    f"P-Form Σ {meta['sums']['pform']:,.0f} · L-Form Σ {meta['sums']['lform']:,.0f} · "
    f"Tested Σ {meta['sums']['tested']:,.0f} · numbers reconciled against source Total column on every refresh."
)
