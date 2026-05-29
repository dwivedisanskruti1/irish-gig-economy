"""
eda_analysis.py
Exploratory Data Analysis — Irish Gen Z Gig Economy
Generates all charts saved to notebooks/outputs/

Run: python notebooks/eda_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ── Style ────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150,
    "figure.facecolor": "white",
    "axes.facecolor": "#fafafa",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
    "font.family": "DejaVu Sans",
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
})

TEAL   = "#1D9E75"
CORAL  = "#D85A30"
PURPLE = "#7F77DD"
AMBER  = "#EF9F27"
GRAY   = "#888780"

BASE = Path(__file__).parent.parent
CLEAN = BASE / "data" / "clean"
OUT   = BASE / "notebooks" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────
master   = pd.read_csv(CLEAN / "county_master.csv")
wrc      = pd.read_csv(CLEAN / "wrc_cases_clean.csv")
trends   = pd.read_csv(CLEAN / "trends_clean.csv")
trends["date"] = pd.to_datetime(trends["date"])

print(f"Master: {master.shape}  |  WRC: {wrc.shape}  |  Trends: {trends.shape}")

latest_year = master["year"].max()
latest = master[master["year"] == latest_year].copy()


# ═══════════════════════════════════════════════════════════════
# CHART 1: National Hidden Work Gap trend 2018-2025
# ═══════════════════════════════════════════════════════════════
national = (master.groupby("year")
            .agg(total_gig=("estimated_true_gig_workers","sum"),
                 total_employed=("official_employed_u27","sum"))
            .reset_index())
national["gap_pct"] = national["total_gig"] / national["total_employed"] * 100

fig, ax = plt.subplots(figsize=(10, 5))
ax.fill_between(national["year"], national["gap_pct"], alpha=0.15, color=TEAL)
ax.plot(national["year"], national["gap_pct"], color=TEAL, lw=2.5, marker="o", ms=6)

# Annotate Covid
ax.axvspan(2020, 2021, alpha=0.08, color=CORAL, label="Covid-19 period")
ax.annotate("Covid-19\ngig surge", xy=(2020.5, national.loc[national.year==2020,"gap_pct"].values[0]),
            xytext=(2020.5, national["gap_pct"].max() * 0.75),
            ha="center", fontsize=9, color=CORAL,
            arrowprops=dict(arrowstyle="->", color=CORAL, lw=1))

# EU Directive line
ax.axvline(2026, color=PURPLE, lw=1.5, linestyle="--", alpha=0.7)
ax.text(2026.05, national["gap_pct"].max() * 0.95, "EU Directive\ntransposed",
        color=PURPLE, fontsize=8.5, va="top")

ax.set_xlabel("Year")
ax.set_ylabel("Hidden Work Gap (% of official employed)")
ax.set_title("Ireland's Hidden Work Gap — Under-27s in Precarious Platform Work\n"
             "Share of youth in gig work NOT captured by official employment statistics")
ax.set_xlim(2017.5, 2026.5)
plt.tight_layout()
plt.savefig(OUT / "01_national_hidden_gap_trend.png", bbox_inches="tight")
plt.close()
print("Chart 1 saved")


# ═══════════════════════════════════════════════════════════════
# CHART 2: County-level Hidden Work Gap (latest year)
# ═══════════════════════════════════════════════════════════════
county_sorted = latest.sort_values("hidden_work_gap_pct", ascending=True)
colors = [CORAL if v >= county_sorted["hidden_work_gap_pct"].quantile(0.75)
          else TEAL if v <= county_sorted["hidden_work_gap_pct"].quantile(0.25)
          else AMBER for v in county_sorted["hidden_work_gap_pct"]]

fig, ax = plt.subplots(figsize=(10, 9))
bars = ax.barh(county_sorted["county"], county_sorted["hidden_work_gap_pct"],
               color=colors, height=0.7, edgecolor="none")
ax.set_xlabel("Hidden Work Gap (%)")
ax.set_title(f"Hidden Work Gap by County — {latest_year}\n"
             "Red = Critical risk | Green = Low risk")
# Value labels
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.1, bar.get_y() + bar.get_height()/2,
            f"{w:.1f}%", va="center", fontsize=8, color="#444")
plt.tight_layout()
plt.savefig(OUT / "02_county_hidden_gap_bar.png", bbox_inches="tight")
plt.close()
print("Chart 2 saved")


# ═══════════════════════════════════════════════════════════════
# CHART 3: Deprivation vs Hidden Work Gap scatter
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 6))
sc = ax.scatter(latest["deprivation_score"], latest["hidden_work_gap_pct"],
                s=latest["official_employed_u27"] / 30,
                c=latest["urbanisation_rate"], cmap="RdYlGn",
                alpha=0.8, edgecolors="white", lw=0.5)
plt.colorbar(sc, ax=ax, label="Urbanisation rate (%)")

# Regression line
m, b = np.polyfit(latest["deprivation_score"], latest["hidden_work_gap_pct"], 1)
x_line = np.linspace(latest["deprivation_score"].min(),
                     latest["deprivation_score"].max(), 100)
ax.plot(x_line, m * x_line + b, color=CORAL, lw=1.5, linestyle="--", alpha=0.7)

# Label notable counties
for _, row in latest.iterrows():
    if row["county"] in ["Dublin","Galway","Leitrim","Donegal","Cork","Mayo"]:
        ax.annotate(row["county"],
                    xy=(row["deprivation_score"], row["hidden_work_gap_pct"]),
                    xytext=(3, 3), textcoords="offset points", fontsize=8, color="#333")

ax.set_xlabel("Pobal Deprivation Score (higher = more deprived)")
ax.set_ylabel("Hidden Work Gap (%)")
ax.set_title("Deprivation vs Hidden Work Gap — Irish Counties\n"
             "Bubble size = youth employment count | Colour = urbanisation")
# Correlation
r = np.corrcoef(latest["deprivation_score"], latest["hidden_work_gap_pct"])[0,1]
ax.text(0.05, 0.95, f"r = {r:.2f}", transform=ax.transAxes,
        fontsize=10, color=CORAL, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
plt.tight_layout()
plt.savefig(OUT / "03_deprivation_vs_gap_scatter.png", bbox_inches="tight")
plt.close()
print("Chart 3 saved")


# ═══════════════════════════════════════════════════════════════
# CHART 4: WRC cases — sector breakdown and outcomes
# ═══════════════════════════════════════════════════════════════
sector_summary = (wrc.groupby("sector")
                  .agg(total=("case_id","count"),
                       wins=("worker_won","sum"))
                  .reset_index())
sector_summary["win_rate"] = sector_summary["wins"] / sector_summary["total"] * 100
sector_summary = sector_summary.sort_values("total", ascending=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Left: total cases
ax1.barh(sector_summary["sector"], sector_summary["total"],
         color=PURPLE, alpha=0.85, height=0.6, edgecolor="none")
ax1.set_xlabel("Number of WRC cases")
ax1.set_title("Platform Worker WRC Cases\nby Sector (2018–2025)")

# Right: win rate
colors_wr = [TEAL if w >= 40 else CORAL for w in sector_summary["win_rate"]]
ax2.barh(sector_summary["sector"], sector_summary["win_rate"],
         color=colors_wr, alpha=0.85, height=0.6, edgecolor="none")
ax2.axvline(50, color=GRAY, lw=1, linestyle="--", alpha=0.5)
ax2.set_xlabel("Worker win rate (%)")
ax2.set_title("Worker Win Rate by Sector\n(green = >40% wins)")

plt.suptitle("Workplace Relations Commission — Platform Worker Disputes", y=1.02,
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(OUT / "04_wrc_sector_analysis.png", bbox_inches="tight")
plt.close()
print("Chart 4 saved")


# ═══════════════════════════════════════════════════════════════
# CHART 5: Google Trends — gig search interest over time
# ═══════════════════════════════════════════════════════════════
COLOURS_TREND = {
    "Deliveroo Ireland": TEAL,
    "Fiverr Ireland": PURPLE,
    "side hustle Ireland": AMBER,
    "zero hours contract Ireland": CORAL,
    "gig work Ireland": GRAY,
}

fig, ax = plt.subplots(figsize=(12, 5))
for term, colour in COLOURS_TREND.items():
    sub = trends[trends["term"] == term]
    monthly_avg = sub.set_index("date")["interest"].resample("QE").mean()
    ax.plot(monthly_avg.index, monthly_avg.values,
            color=colour, lw=1.8, label=term, alpha=0.9)

ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2021-06-30"),
           alpha=0.08, color=CORAL)
ax.text(pd.Timestamp("2020-06-01"), 85, "Covid-19", color=CORAL, fontsize=9, alpha=0.7)
ax.set_ylabel("Search interest (0–100)")
ax.set_title("Google Trends — Gig Economy Search Interest in Ireland (2018–2025)\n"
             "Rising interest tracks with growing precarious work")
ax.legend(fontsize=8, loc="upper left", framealpha=0.9)
plt.tight_layout()
plt.savefig(OUT / "05_google_trends_gig_ireland.png", bbox_inches="tight")
plt.close()
print("Chart 5 saved")


# ═══════════════════════════════════════════════════════════════
# CHART 6: Heatmap — Hidden Work Gap by county across years
# ═══════════════════════════════════════════════════════════════
pivot = master.pivot(index="county", columns="year", values="hidden_work_gap_pct")
pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

fig, ax = plt.subplots(figsize=(12, 9))
sns.heatmap(pivot, cmap="YlOrRd", ax=ax, linewidths=0.3,
            linecolor="#eee", cbar_kws={"label": "Hidden Work Gap (%)"},
            fmt=".1f", annot=True, annot_kws={"size": 7})
ax.set_title("Hidden Work Gap Heatmap — All Counties 2018–2025\n"
             "Darker = higher proportion of under-27s in uncounted precarious work",
             pad=12)
ax.set_xlabel("Year")
ax.set_ylabel("")
plt.tight_layout()
plt.savefig(OUT / "06_heatmap_county_year.png", bbox_inches="tight")
plt.close()
print("Chart 6 saved")


# ═══════════════════════════════════════════════════════════════
# CHART 7: WRC claims by age — who's fighting back?
# ═══════════════════════════════════════════════════════════════
age_summary = (wrc.groupby(["claimant_age_band","claim_type"])
               .size().reset_index(name="count"))
age_pivot = age_summary.pivot(index="claimant_age_band",
                               columns="claim_type", values="count").fillna(0)
age_order = ["Under 25","25-34","35-44","45+"]
age_pivot = age_pivot.reindex([a for a in age_order if a in age_pivot.index])

fig, ax = plt.subplots(figsize=(10, 5))
age_pivot.plot(kind="bar", ax=ax, width=0.7,
               color=[PURPLE, TEAL, CORAL, AMBER], edgecolor="none")
ax.set_xlabel("Claimant age band")
ax.set_ylabel("Number of WRC cases")
ax.set_title("WRC Platform Worker Claims by Age and Claim Type\n"
             "Under-25s disproportionately file misclassification claims")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
ax.legend(title="Claim type", fontsize=8)
plt.tight_layout()
plt.savefig(OUT / "07_wrc_age_claim_type.png", bbox_inches="tight")
plt.close()
print("Chart 7 saved")


print(f"\nAll 7 charts saved to {OUT}")
print("\n=== Key Findings ===")
gap_2025 = national[national["year"] == 2025]["gap_pct"].values[0]
gap_2018 = national[national["year"] == 2018]["gap_pct"].values[0]
print(f"National hidden work gap 2018: {gap_2018:.1f}%")
print(f"National hidden work gap 2025: {gap_2025:.1f}%")
print(f"Growth: +{gap_2025 - gap_2018:.1f} percentage points")
print(f"Correlation deprivation vs gap: r = {r:.2f}")
top5 = latest.nlargest(5, "hidden_work_gap_pct")[["county","hidden_work_gap_pct","risk_category"]]
print(f"\nTop 5 counties by hidden work gap:\n{top5.to_string(index=False)}")
