"""
etl.py — Clean, merge, and engineer features from raw datasets.
Outputs: data/clean/ folder with analysis-ready CSVs.

The key output is county_master.csv which contains the
"Hidden Work Gap" metric — Ireland's first county-level estimate
of precarious youth work invisible to official statistics.
"""

import pandas as pd
import numpy as np
import os

RAW = os.path.join(os.path.dirname(__file__), "raw")
CLEAN = os.path.join(os.path.dirname(__file__), "clean")
os.makedirs(CLEAN, exist_ok=True)


def clean_lfs():
    df = pd.read_csv(f"{RAW}/cso_lfs_youth_employment.csv")
    # Annual averages per county and age band
    annual = (df.groupby(["county","year","age_band"])
                .agg(avg_employed=("employed","mean"),
                     avg_self_employed=("self_employed","mean"),
                     avg_employment_rate=("employment_rate","mean"),
                     avg_self_emp_rate=("self_emp_rate","mean"),
                     avg_population=("population_sample","mean"))
                .reset_index())
    # Under-27 aggregate (15-19, 20-24, 25-29 bands)
    u27 = (annual[annual["age_band"].isin(["15-19","20-24","25-29"])]
           .groupby(["county","year"])
           .agg(official_employed_u27=("avg_employed","sum"),
                official_self_emp_u27=("avg_self_employed","sum"),
                avg_employment_rate_u27=("avg_employment_rate","mean"))
           .reset_index())
    u27.to_csv(f"{CLEAN}/lfs_annual_u27.csv", index=False)
    print(f"LFS cleaned → {len(u27)} rows")
    return u27


def clean_revenue():
    df = pd.read_csv(f"{RAW}/revenue_platform_filers.csv")
    df.to_csv(f"{CLEAN}/revenue_clean.csv", index=False)
    print(f"Revenue cleaned → {len(df)} rows")
    return df


def clean_wrc():
    df = pd.read_csv(f"{RAW}/wrc_platform_cases.csv")
    summary = (df.groupby(["county","year"])
                 .agg(total_cases=("case_id","count"),
                      worker_wins=("worker_won","sum"),
                      misclass_cases=("claim_type", lambda x: (x=="Misclassification").sum()))
                 .reset_index())
    summary["worker_win_rate"] = (summary["worker_wins"] / summary["total_cases"] * 100).round(1)
    summary.to_csv(f"{CLEAN}/wrc_summary.csv", index=False)
    df.to_csv(f"{CLEAN}/wrc_cases_clean.csv", index=False)
    print(f"WRC cleaned → {len(summary)} county-year summaries")
    return summary


def clean_deprivation():
    df = pd.read_csv(f"{RAW}/pobal_deprivation_index.csv")
    df.to_csv(f"{CLEAN}/deprivation_clean.csv", index=False)
    print(f"Deprivation index cleaned → {len(df)} counties")
    return df


def build_master(lfs, revenue, wrc, deprivation):
    """
    Build county-year master table and compute the Hidden Work Gap metric.

    Hidden Work Gap = estimated_gig_workers / official_employed_u27 * 100
    This captures the % of under-27 workers whose employment is NOT
    captured in standard ILO employment classifications.
    """
    master = lfs.merge(revenue[["county","year","estimated_platform_workers",
                                  "platform_share_pct","median_platform_income_eur",
                                  "top_platform"]], on=["county","year"], how="left")
    master = master.merge(wrc, on=["county","year"], how="left")
    master = master.merge(deprivation[["county","deprivation_score",
                                        "deprivation_category","urbanisation_rate"]],
                          on="county", how="left")

    # Fill WRC NaNs (counties with no cases in a year)
    master["total_cases"] = master["total_cases"].fillna(0).astype(int)
    master["worker_wins"] = master["worker_wins"].fillna(0).astype(int)
    master["misclass_cases"] = master["misclass_cases"].fillna(0).astype(int)
    master["worker_win_rate"] = master["worker_win_rate"].fillna(0)

    # --- THE HIDDEN WORK GAP METRIC ---
    # Gig workers estimated from platform filing data + a multiplier
    # (Revenue captures ~40% of true gig participation due to under-reporting)
    UNDER_REPORT_FACTOR = 2.5
    master["estimated_true_gig_workers"] = (
        master["estimated_platform_workers"] * UNDER_REPORT_FACTOR
    ).round(0).astype(int)

    master["hidden_work_gap_pct"] = (
        master["estimated_true_gig_workers"] /
        master["official_employed_u27"] * 100
    ).round(1)

    # Normalised gap score (0-100) for dashboard use
    raw_min = master["hidden_work_gap_pct"].min()
    raw_max = master["hidden_work_gap_pct"].max()
    master["gap_score"] = (
        (master["hidden_work_gap_pct"] - raw_min) /
        (raw_max - raw_min) * 100
    ).round(1)

    # Risk classification
    master["risk_category"] = pd.cut(
        master["gap_score"],
        bins=[0, 25, 50, 75, 100],
        labels=["Low","Medium","High","Critical"],
        include_lowest=True
    )

    # Year-on-year gig growth rate per county
    master = master.sort_values(["county","year"])
    master["gig_yoy_growth"] = (
        master.groupby("county")["estimated_true_gig_workers"]
        .pct_change() * 100
    ).round(1)

    master.to_csv(f"{CLEAN}/county_master.csv", index=False)
    print(f"Master dataset built → {len(master)} rows, {master['county'].nunique()} counties")
    return master


def build_trends_clean():
    df = pd.read_csv(f"{RAW}/google_trends_gig_ireland.csv")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df.to_csv(f"{CLEAN}/trends_clean.csv", index=False)
    print(f"Trends cleaned → {len(df)} rows")
    return df


if __name__ == "__main__":
    print("=== Irish Gig Economy ETL Pipeline ===\n")
    lfs = clean_lfs()
    rev = clean_revenue()
    wrc = clean_wrc()
    dep = clean_deprivation()
    build_trends_clean()
    master = build_master(lfs, rev, wrc, dep)

    print("\n=== Sample Hidden Work Gap (2025, top 5 counties) ===")
    sample = (master[master["year"]==2025]
              .sort_values("hidden_work_gap_pct", ascending=False)
              [["county","hidden_work_gap_pct","risk_category","deprivation_score"]]
              .head())
    print(sample.to_string(index=False))
    print("\nETL complete. Files in data/clean/")
