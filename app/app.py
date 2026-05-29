"""
app.py — Irish Gig Economy Streamlit App
"Are you a hidden worker?"

Run locally: streamlit run app/app.py
Deploy free: streamlit.io/cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Ireland's Hidden Workers",
    page_icon="🇮🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────
BASE  = Path(__file__).parent.parent
CLEAN = BASE / "data" / "clean"

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    master  = pd.read_csv(CLEAN / "county_master.csv")
    wrc     = pd.read_csv(CLEAN / "wrc_cases_clean.csv")
    trends  = pd.read_csv(CLEAN / "trends_clean.csv")
    model   = pd.read_csv(CLEAN / "model_results.csv")
    trends["date"] = pd.to_datetime(trends["date"])
    return master, wrc, trends, model

master, wrc, trends, model_results = load_data()
latest = master[master["year"] == master["year"].max()].copy()
COUNTIES = sorted(master["county"].unique().tolist())

# ── Colour scheme ─────────────────────────────────────────────
TEAL   = "#1D9E75"
CORAL  = "#D85A30"
PURPLE = "#7F77DD"
AMBER  = "#EF9F27"

RISK_COLOURS = {
    "Critical": "#D85A30",
    "High":     "#EF9F27",
    "Medium":   "#1D9E75",
    "Low":      "#378ADD",
}

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 600; }
  .risk-badge {
      display: inline-block; padding: 4px 14px; border-radius: 20px;
      font-weight: 600; font-size: 1rem;
  }
  .stTabs [data-baseweb="tab"] { font-size: 0.95rem; }
  h1 { color: #1a1a1a; }
  .insight-box {
      background: #f0faf6; border-left: 4px solid #1D9E75;
      padding: 12px 16px; border-radius: 0 8px 8px 0;
      margin: 10px 0;
  }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════
st.title("🇮🇪 Ireland's Hidden Workers")
st.markdown(
    "**Gen Z & the Gig Economy** — Ireland counts 2.8 million people 'in employment', "
    "but how many under-27s doing Deliveroo runs, Fiverr gigs and zero-hour shifts "
    "are invisible to official statistics?"
)
st.caption("Data: CSO Labour Force Survey · Revenue.ie · WRC · Pobal Deprivation Index · Google Trends (2018–2025)")

st.divider()

# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Am I a hidden worker?",
    "📊 National overview",
    "🗺️ County explorer",
    "⚖️ WRC cases",
    "📈 Trends",
])


# ───────────────────────────────────────────────────────────────
# TAB 1: Personal calculator
# ───────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Find out if you're counted")
    st.markdown(
        "Official employment stats use ILO definitions. If you work through a platform, "
        "on a zero-hours contract, or as a 'self-employed' contractor — you might be statistically invisible."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        county = st.selectbox("Your county", COUNTIES, index=COUNTIES.index("Galway") if "Galway" in COUNTIES else 0)
        age    = st.selectbox("Your age group", ["15–19","20–24","25–29","30–34"])
        work_type = st.selectbox("Your main work", [
            "Regular employee (full-time)",
            "Regular employee (part-time)",
            "Zero-hours contract",
            "Platform delivery (Deliveroo, JustEat, etc.)",
            "Freelance online (Fiverr, Upwork, etc.)",
            "Ride-hailing / Bolt driver",
            "Airbnb host / home rental",
            "Gig cleaning / care work",
            "Multiple platform jobs",
        ])
        hours = st.slider("Approximate weekly hours worked", 1, 60, 25)

    with col2:
        # Classify the user
        precarious = work_type not in [
            "Regular employee (full-time)", "Regular employee (part-time)"
        ]
        county_data = latest[latest["county"] == county].iloc[0]
        risk_cat = county_data["risk_category"]
        gap_pct  = county_data["hidden_work_gap_pct"]

        if precarious:
            st.markdown(f"""
            <div style='background:#fff4f0;border:1.5px solid #D85A30;border-radius:12px;padding:20px;'>
                <p style='font-size:1.1rem;font-weight:600;color:#D85A30;margin:0 0 8px'>
                    You are likely a hidden worker.
                </p>
                <p style='color:#444;margin:0;font-size:0.95rem;'>
                    Your work type (<b>{work_type}</b>) is typically classified as
                    "self-employed" or "independent contractor" in Ireland —
                    meaning you are often excluded from core employment protections.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background:#f0faf6;border:1.5px solid #1D9E75;border-radius:12px;padding:20px;'>
                <p style='font-size:1.1rem;font-weight:600;color:#1D9E75;margin:0 0 8px'>
                    You appear in the official stats.
                </p>
                <p style='color:#444;margin:0;font-size:0.95rem;'>
                    Your work type is captured under standard ILO employment definitions.
                    But {gap_pct:.1f}% of under-27s in {county} are estimated to be in uncounted gig work.
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"**{county} — {risk_cat} risk county**")
        col_a, col_b = st.columns(2)
        col_a.metric("Hidden work gap", f"{gap_pct:.1f}%",
                     help="Estimated % of under-27s in gig work not captured by official stats")
        col_b.metric("Deprivation score", f"{county_data['deprivation_score']:.1f}",
                     help="Pobal HP Deprivation Index (higher = more deprived)")

        st.markdown("---")
        st.markdown("**What the EU Directive means for you (Dec 2026)**")
        rights = {
            "Platform delivery (Deliveroo, JustEat, etc.)": [
                "Presumption of employment relationship",
                "Right to minimum wage", "Holiday pay entitlement",
                "Right to organise collectively",
            ],
            "Ride-hailing / Bolt driver": [
                "Platform must prove you're self-employed",
                "Access to social protection",
                "Protection against unfair deactivation",
            ],
            "Freelance online (Fiverr, Upwork, etc.)": [
                "If >50% income from one platform: employment presumed",
                "Transparency on algorithmic management",
                "Right to human review of automated decisions",
            ],
        }
        bullet_rights = rights.get(work_type, [
            "Enhanced transparency on work allocation algorithms",
            "Right to explanation if account is deactivated",
            "Collective bargaining protections",
        ])
        for r in bullet_rights:
            st.markdown(f"✓ {r}")

        if precarious:
            st.info(
                f"💡 **You can file a WRC claim now.** If you believe you're misclassified as "
                f"self-employed, the Workplace Relations Commission can adjudicate. "
                f"Workers win {county_data.get('worker_win_rate', 38):.0f}% of misclassification claims in Ireland."
            )


# ───────────────────────────────────────────────────────────────
# TAB 2: National overview
# ───────────────────────────────────────────────────────────────
with tab2:
    st.subheader("How big is the hidden workforce?")

    national = (master.groupby("year")
                .agg(total_gig=("estimated_true_gig_workers","sum"),
                     total_employed=("official_employed_u27","sum"),
                     avg_gap=("hidden_work_gap_pct","mean"))
                .reset_index())
    national["gap_pct"] = national["total_gig"] / national["total_employed"] * 100

    latest_year = master["year"].max()
    prev_year   = latest_year - 1
    gap_now   = national[national["year"] == latest_year]["gap_pct"].values[0]
    gap_prev  = national[national["year"] == prev_year]["gap_pct"].values[0]
    gig_total = national[national["year"] == latest_year]["total_gig"].values[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("National hidden gap", f"{gap_now:.1f}%", f"+{gap_now-gap_prev:.1f}pp vs last year")
    col2.metric("Estimated gig workers <27", f"{gig_total:,.0f}", help="Across all 26 counties")
    col3.metric("WRC cases filed (total)", f"{len(wrc):,}", f"{wrc[wrc['year']==latest_year].shape[0]} in {latest_year}")
    col4.metric("Growth since 2018", f"+{gap_now - national['gap_pct'].iloc[0]:.1f}pp")

    st.markdown("")

    # Trend chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=national["year"], y=national["gap_pct"],
        mode="lines+markers", name="Hidden work gap (%)",
        line=dict(color=TEAL, width=3),
        fill="tozeroy", fillcolor="rgba(29,158,117,0.1)",
    ))
    fig.add_vrect(x0=2020, x1=2021, fillcolor=CORAL, opacity=0.07,
                  annotation_text="Covid-19", annotation_position="top left",
                  annotation_font_color=CORAL)
    fig.add_vline(x=2026, line_dash="dash", line_color=PURPLE, opacity=0.6,
                  annotation_text="EU Directive deadline", annotation_font_color=PURPLE)
    fig.update_layout(
        title="National Hidden Work Gap — Under-27s 2018–2025",
        xaxis_title="Year", yaxis_title="Hidden work gap (%)",
        plot_bgcolor="white", paper_bgcolor="white",
        hovermode="x unified", height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class='insight-box'>
    <b>Key insight:</b> The hidden work gap has grown from 4.1% in 2018 to 9.5% in 2025 —
    more than doubling in 7 years. Covid-19 accelerated the shift as delivery platforms
    surged. Ireland must transpose the EU Platform Workers Directive by December 2026.
    </div>
    """, unsafe_allow_html=True)

    # Risk distribution
    col1, col2 = st.columns(2)
    with col1:
        risk_counts = latest["risk_category"].value_counts().reset_index()
        risk_counts.columns = ["risk_category","count"]
        risk_order = ["Critical","High","Medium","Low"]
        risk_counts["risk_category"] = pd.Categorical(risk_counts["risk_category"],
                                                       categories=risk_order, ordered=True)
        risk_counts = risk_counts.sort_values("risk_category")
        fig2 = px.bar(risk_counts, x="risk_category", y="count",
                      color="risk_category",
                      color_discrete_map=RISK_COLOURS,
                      title=f"Counties by Risk Category ({latest_year})",
                      labels={"count": "Number of counties", "risk_category": "Risk level"})
        fig2.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white", height=320)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        top5 = model_results.head(5)[["county","vulnerability_score","risk_category"]]
        st.markdown("**Top 5 most vulnerable counties post-EU Directive**")
        for _, row in top5.iterrows():
            colour = RISK_COLOURS.get(row["risk_category"], GRAY if "GRAY" in dir() else "#888")
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"padding:8px 0;border-bottom:1px solid #eee;'>"
                f"<span style='font-weight:500'>{row['county']}</span>"
                f"<span style='background:{colour};color:white;padding:3px 12px;"
                f"border-radius:20px;font-size:0.85rem;font-weight:500'>"
                f"{row['vulnerability_score']:.0f}/100</span></div>",
                unsafe_allow_html=True
            )


# ───────────────────────────────────────────────────────────────
# TAB 3: County explorer
# ───────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Explore by county")

    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox("Select a county", COUNTIES, key="county_explorer",
                                index=COUNTIES.index("Galway") if "Galway" in COUNTIES else 0)

    county_hist = master[master["county"] == selected].sort_values("year")
    county_latest = latest[latest["county"] == selected].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Hidden work gap", f"{county_latest['hidden_work_gap_pct']:.1f}%")
    col2.metric("Risk category", county_latest["risk_category"])
    col3.metric("Deprivation score", f"{county_latest['deprivation_score']:.1f}")

    # County trend vs national
    nat_line = national[["year","gap_pct"]].rename(columns={"gap_pct": "National avg"})
    county_line = county_hist[["year","hidden_work_gap_pct"]].rename(
        columns={"hidden_work_gap_pct": selected})

    merged = nat_line.merge(county_line, on="year")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=merged["year"], y=merged[selected],
                              name=selected, line=dict(color=TEAL, width=2.5),
                              mode="lines+markers"))
    fig3.add_trace(go.Scatter(x=merged["year"], y=merged["National avg"],
                              name="National avg", line=dict(color=GRAY if False else "#888780",
                              dash="dot", width=1.5), mode="lines"))
    fig3.update_layout(title=f"{selected} — Hidden Work Gap vs National Average",
                       xaxis_title="Year", yaxis_title="Hidden work gap (%)",
                       plot_bgcolor="white", paper_bgcolor="white", height=340)
    st.plotly_chart(fig3, use_container_width=True)

    # Scatter all counties
    st.markdown("**All counties — Deprivation vs Hidden Work Gap**")
    fig4 = px.scatter(latest, x="deprivation_score", y="hidden_work_gap_pct",
                      size="official_employed_u27", color="risk_category",
                      color_discrete_map=RISK_COLOURS,
                      hover_name="county", size_max=35,
                      labels={"deprivation_score": "Deprivation score",
                              "hidden_work_gap_pct": "Hidden work gap (%)"},
                      title="Deprivation vs Hidden Work Gap — All Counties")
    fig4.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="white")))
    # Highlight selected
    sel_row = latest[latest["county"] == selected]
    fig4.add_trace(go.Scatter(
        x=sel_row["deprivation_score"], y=sel_row["hidden_work_gap_pct"],
        mode="markers", marker=dict(size=18, color="gold", symbol="star",
                                    line=dict(width=2, color="black")),
        name=f"★ {selected}", showlegend=True,
    ))
    fig4.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400)
    st.plotly_chart(fig4, use_container_width=True)


# ───────────────────────────────────────────────────────────────
# TAB 4: WRC cases
# ───────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Workplace Relations Commission — platform worker disputes")
    st.markdown("Who is fighting back, and are they winning?")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total WRC cases (2018–2025)", f"{len(wrc):,}")
    win_rate = wrc["worker_won"].mean() * 100
    col2.metric("Overall worker win rate", f"{win_rate:.1f}%")
    misclass = (wrc["claim_type"] == "Misclassification").sum()
    col3.metric("Misclassification claims", f"{misclass:,}", f"{misclass/len(wrc)*100:.0f}% of all cases")

    col1, col2 = st.columns(2)
    with col1:
        sector_sum = (wrc.groupby("sector")
                      .agg(total=("case_id","count"), wins=("worker_won","sum"))
                      .reset_index())
        sector_sum["win_rate"] = (sector_sum["wins"] / sector_sum["total"] * 100).round(1)
        sector_sum = sector_sum.sort_values("total", ascending=True)
        fig5 = px.bar(sector_sum, y="sector", x="total", orientation="h",
                      color="win_rate", color_continuous_scale="RdYlGn",
                      title="WRC Cases by Sector",
                      labels={"total": "Number of cases", "win_rate": "Win rate (%)"})
        fig5.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=340)
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        yr_sum = (wrc.groupby("year")
                  .agg(total=("case_id","count"), wins=("worker_won","sum"))
                  .reset_index())
        yr_sum["win_rate"] = (yr_sum["wins"] / yr_sum["total"] * 100).round(1)
        fig6 = go.Figure()
        fig6.add_bar(x=yr_sum["year"], y=yr_sum["total"],
                     name="Total cases", marker_color=PURPLE, opacity=0.8)
        fig6.add_trace(go.Scatter(x=yr_sum["year"], y=yr_sum["win_rate"],
                                  name="Win rate (%)", yaxis="y2",
                                  line=dict(color=TEAL, width=2.5), mode="lines+markers"))
        fig6.update_layout(
            title="WRC Cases & Worker Win Rate by Year",
            yaxis=dict(title="Number of cases"),
            yaxis2=dict(title="Worker win rate (%)", overlaying="y", side="right",
                        range=[0,100]),
            plot_bgcolor="white", paper_bgcolor="white", height=340,
            hovermode="x unified",
        )
        st.plotly_chart(fig6, use_container_width=True)

    # Age breakdown
    age_type = (wrc.groupby(["claimant_age_band","claim_type"])
                .size().reset_index(name="count"))
    fig7 = px.bar(age_type, x="claimant_age_band", y="count", color="claim_type",
                  barmode="group",
                  color_discrete_sequence=[PURPLE, TEAL, CORAL, AMBER],
                  title="WRC Claims by Age Group and Claim Type",
                  labels={"count": "Cases", "claimant_age_band": "Age band",
                          "claim_type": "Claim type"},
                  category_orders={"claimant_age_band": ["Under 25","25-34","35-44","45+"]})
    fig7.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=350)
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("""
    <div class='insight-box'>
    <b>Key insight:</b> Under-25s file the highest proportion of misclassification claims —
    the exact issue the EU Platform Workers Directive targets. Workers win ~38% of
    misclassification claims overall, but rates vary significantly by sector.
    </div>
    """, unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────
# TAB 5: Trends
# ───────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Search trends — the digital footprint of precarious work")
    st.markdown(
        "Google Trends reveal how gig platform interest has evolved — "
        "often predicting official data 1-2 quarters ahead."
    )

    TERM_COLOURS = {
        "Deliveroo Ireland": TEAL,
        "Fiverr Ireland":    PURPLE,
        "side hustle Ireland": AMBER,
        "zero hours contract Ireland": CORAL,
        "gig work Ireland": "#888780",
    }

    selected_terms = st.multiselect(
        "Select search terms",
        list(TERM_COLOURS.keys()),
        default=["Deliveroo Ireland","side hustle Ireland","zero hours contract Ireland"],
    )

    if selected_terms:
        fig8 = go.Figure()
        for term in selected_terms:
            sub = trends[trends["term"] == term].sort_values("date")
            monthly = sub.set_index("date")["interest"].resample("QE").mean().reset_index()
            fig8.add_trace(go.Scatter(
                x=monthly["date"], y=monthly["interest"],
                name=term, line=dict(color=TERM_COLOURS[term], width=2),
                mode="lines",
            ))
        fig8.add_vrect(x0="2020-03-01", x1="2021-06-30",
                       fillcolor=CORAL, opacity=0.07,
                       annotation_text="Covid-19", annotation_font_color=CORAL)
        fig8.update_layout(
            title="Google Trends — Gig Economy Search Interest Ireland (2018–2025)",
            xaxis_title="Date", yaxis_title="Search interest (0–100)",
            plot_bgcolor="white", paper_bgcolor="white",
            hovermode="x unified", height=400,
        )
        st.plotly_chart(fig8, use_container_width=True)

    st.markdown("---")
    st.markdown("**Correlation: Search trends vs official self-employment filings**")
    national_trend = (trends[trends["term"] == "Deliveroo Ireland"]
                      .groupby("year")["interest"].mean().reset_index())
    nat_emp = (master.groupby("year")["official_self_emp_u27"].mean().reset_index())
    merged_t = national_trend.merge(nat_emp, on="year")

    fig9 = go.Figure()
    fig9.add_trace(go.Scatter(x=merged_t["year"], y=merged_t["interest"],
                              name="Deliveroo search interest", yaxis="y",
                              line=dict(color=TEAL, width=2.5), mode="lines+markers"))
    fig9.add_trace(go.Scatter(x=merged_t["year"], y=merged_t["official_self_emp_u27"],
                              name="Official self-employment u27", yaxis="y2",
                              line=dict(color=CORAL, width=2.5, dash="dot"), mode="lines+markers"))
    fig9.update_layout(
        title="Search Interest vs Official Self-Employment — Do Trends Predict Filings?",
        yaxis=dict(title="Search interest (0–100)"),
        yaxis2=dict(title="Avg self-employment count", overlaying="y", side="right"),
        plot_bgcolor="white", paper_bgcolor="white", height=360, hovermode="x unified",
    )
    st.plotly_chart(fig9, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<small>Built by Sanskruti Dwivedi · MSc Business Analytics, University of Galway · 2025 · "
    "Data: CSO, Revenue.ie, WRC, Pobal, Google Trends · "
    "EU Platform Workers Directive (EU) 2024/2831 must be transposed into Irish law by December 2026</small>",
    unsafe_allow_html=True,
)
