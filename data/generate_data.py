"""
generate_data.py
Generates realistic Irish gig economy datasets modelled on:
  - CSO Labour Force Survey (LFS) structure
  - Revenue self-assessment filing patterns
  - WRC (Workplace Relations Commission) case data
  - Pobal HP Deprivation Index

Run this once to populate data/raw/ before running any notebooks or the app.
"""

import pandas as pd
import numpy as np
import os

np.random.seed(42)

COUNTIES = [
    "Carlow","Cavan","Clare","Cork","Donegal","Dublin","Galway","Kerry",
    "Kildare","Kilkenny","Laois","Leitrim","Limerick","Longford","Louth",
    "Mayo","Meath","Monaghan","Offaly","Roscommon","Sligo","Tipperary",
    "Waterford","Westmeath","Wexford","Wicklow"
]

YEARS = list(range(2018, 2026))
QUARTERS = ["Q1","Q2","Q3","Q4"]
AGE_BANDS = ["15-19","20-24","25-29","30-34"]

# County-level parameters (population size, urbanisation, deprivation)
COUNTY_PARAMS = {
    "Dublin":     {"pop_weight": 5.0, "urban": 0.95, "depriv": 18.2},
    "Cork":       {"pop_weight": 2.2, "urban": 0.72, "depriv": 22.4},
    "Galway":     {"pop_weight": 1.3, "urban": 0.58, "depriv": 26.1},
    "Limerick":   {"pop_weight": 0.9, "urban": 0.62, "depriv": 28.7},
    "Waterford":  {"pop_weight": 0.7, "urban": 0.55, "depriv": 27.9},
    "Kildare":    {"pop_weight": 1.0, "urban": 0.68, "depriv": 15.3},
    "Meath":      {"pop_weight": 0.9, "urban": 0.52, "depriv": 16.8},
    "Wicklow":    {"pop_weight": 0.8, "urban": 0.48, "depriv": 19.2},
    "Louth":      {"pop_weight": 0.7, "urban": 0.63, "depriv": 24.5},
    "Wexford":    {"pop_weight": 0.6, "urban": 0.42, "depriv": 29.3},
    "Tipperary":  {"pop_weight": 0.6, "urban": 0.35, "depriv": 31.2},
    "Kerry":      {"pop_weight": 0.6, "urban": 0.31, "depriv": 33.8},
    "Clare":      {"pop_weight": 0.5, "urban": 0.38, "depriv": 28.4},
    "Kilkenny":   {"pop_weight": 0.5, "urban": 0.39, "depriv": 25.6},
    "Westmeath":  {"pop_weight": 0.4, "urban": 0.44, "depriv": 27.1},
    "Offaly":     {"pop_weight": 0.4, "urban": 0.38, "depriv": 30.5},
    "Cavan":      {"pop_weight": 0.3, "urban": 0.28, "depriv": 34.2},
    "Donegal":    {"pop_weight": 0.5, "urban": 0.22, "depriv": 38.6},
    "Mayo":       {"pop_weight": 0.5, "urban": 0.25, "depriv": 37.1},
    "Sligo":      {"pop_weight": 0.3, "urban": 0.34, "depriv": 32.4},
    "Roscommon":  {"pop_weight": 0.3, "urban": 0.21, "depriv": 35.8},
    "Longford":   {"pop_weight": 0.2, "urban": 0.32, "depriv": 39.1},
    "Leitrim":    {"pop_weight": 0.2, "urban": 0.18, "depriv": 40.3},
    "Monaghan":   {"pop_weight": 0.3, "urban": 0.26, "depriv": 33.7},
    "Laois":      {"pop_weight": 0.3, "urban": 0.36, "depriv": 29.8},
    "Carlow":     {"pop_weight": 0.3, "urban": 0.41, "depriv": 28.9},
}

def make_lfs_data():
    """CSO Labour Force Survey — employment by county, age, quarter."""
    rows = []
    for county in COUNTIES:
        params = COUNTY_PARAMS[county]
        for year in YEARS:
            for q in QUARTERS:
                for age in AGE_BANDS:
                    base_pop = int(params["pop_weight"] * np.random.randint(800, 1400))
                    # Younger age = lower employment rate
                    age_factor = {"15-19": 0.35, "20-24": 0.68, "25-29": 0.82, "30-34": 0.88}[age]
                    # Employment grew 2018-2025 (+covid dip 2020)
                    year_factor = 1 + (year - 2018) * 0.018
                    if year == 2020: year_factor *= 0.88
                    if year == 2021: year_factor *= 0.94
                    employed = int(base_pop * age_factor * year_factor * np.random.uniform(0.96, 1.04))
                    unemployed = int(employed * np.random.uniform(0.04, 0.12))
                    self_emp = int(employed * np.random.uniform(0.08, 0.22) * (1 + (year - 2018) * 0.025))
                    rows.append({
                        "county": county,
                        "year": year,
                        "quarter": q,
                        "age_band": age,
                        "population_sample": base_pop,
                        "employed": employed,
                        "unemployed": unemployed,
                        "self_employed": self_emp,
                        "employment_rate": round(employed / base_pop * 100, 1),
                        "self_emp_rate": round(self_emp / employed * 100, 1),
                    })
    return pd.DataFrame(rows)


def make_revenue_data():
    """Revenue self-assessment filings — proxy for gig/freelance income under 30."""
    rows = []
    PLATFORMS = ["Deliveroo","JustEat","Bolt","Fiverr","Upwork","Airbnb","TaskRabbit","Other"]
    for county in COUNTIES:
        params = COUNTY_PARAMS[county]
        for year in YEARS:
            n_filers = int(params["pop_weight"] * np.random.randint(120, 280))
            # Gig filing growth: doubled 2018-2025
            gig_share = 0.18 + (year - 2018) * 0.04 + np.random.uniform(-0.02, 0.02)
            gig_filers = int(n_filers * gig_share)
            rows.append({
                "county": county,
                "year": year,
                "total_self_assessed_under30": n_filers,
                "estimated_platform_workers": gig_filers,
                "platform_share_pct": round(gig_share * 100, 1),
                "median_platform_income_eur": int(np.random.uniform(4800, 14200) * (1 + (year-2018)*0.03)),
                "top_platform": np.random.choice(PLATFORMS, p=[0.22,0.18,0.12,0.14,0.10,0.08,0.06,0.10]),
            })
    return pd.DataFrame(rows)


def make_wrc_data():
    """WRC case data — platform worker disputes by sector and year."""
    SECTORS = ["Food delivery","Ride-hailing","Freelance digital","Cleaning","Care work","Logistics"]
    OUTCOMES = ["Worker won","Platform won","Settled","Withdrawn"]
    PLATFORMS_WRC = ["Deliveroo","JustEat","Bolt","Uber","Other platform","Unnamed employer"]
    rows = []
    case_id = 1000
    for year in YEARS:
        # Cases growing year on year
        n_cases = int(np.random.uniform(18, 35) * (1 + (year - 2018) * 0.18))
        for _ in range(n_cases):
            county = np.random.choice(COUNTIES, p=[
                COUNTY_PARAMS[c]["pop_weight"] /
                sum(COUNTY_PARAMS[x]["pop_weight"] for x in COUNTIES)
                for c in COUNTIES
            ])
            sector = np.random.choice(SECTORS, p=[0.30,0.18,0.20,0.12,0.10,0.10])
            outcome = np.random.choice(OUTCOMES, p=[0.38,0.31,0.22,0.09])
            rows.append({
                "case_id": f"WRC-{case_id}",
                "year": year,
                "county": county,
                "sector": sector,
                "platform": np.random.choice(PLATFORMS_WRC),
                "claimant_age_band": np.random.choice(["Under 25","25-34","35-44","45+"],
                                                        p=[0.41,0.33,0.18,0.08]),
                "outcome": outcome,
                "worker_won": outcome == "Worker won",
                "claim_type": np.random.choice(
                    ["Misclassification","Minimum wage","Holiday pay","Unfair dismissal"],
                    p=[0.42,0.28,0.18,0.12]
                ),
                "duration_weeks": int(np.random.uniform(4, 52)),
            })
            case_id += 1
    return pd.DataFrame(rows)


def make_deprivation_data():
    """Pobal-style HP Deprivation Index by county."""
    rows = []
    for county, params in COUNTY_PARAMS.items():
        rows.append({
            "county": county,
            "deprivation_score": params["depriv"],
            "deprivation_category": (
                "Affluent" if params["depriv"] < 20 else
                "Marginally above average" if params["depriv"] < 25 else
                "Marginally below average" if params["depriv"] < 30 else
                "Disadvantaged" if params["depriv"] < 36 else
                "Very disadvantaged"
            ),
            "urbanisation_rate": round(params["urban"] * 100, 1),
            "population_weight": params["pop_weight"],
        })
    return pd.DataFrame(rows)


def make_trends_data():
    """Google Trends proxy data — monthly search interest for gig-related terms."""
    import datetime
    terms = ["Deliveroo Ireland","Fiverr Ireland","side hustle Ireland",
             "zero hours contract Ireland","gig work Ireland"]
    rows = []
    start = datetime.date(2018, 1, 1)
    for m in range(96):  # 8 years * 12 months
        date = (start.replace(day=1) if m == 0 else
                datetime.date(2018 + (m // 12), (m % 12) + 1, 1))
        for term in terms:
            # Upward trend with covid spike + seasonal variation
            base = 30 + m * 0.55
            if 2020 <= date.year <= 2021: base *= 1.35  # covid gig surge
            seasonal = 8 * np.sin(2 * np.pi * date.month / 12)
            interest = max(0, min(100, int(base + seasonal + np.random.normal(0, 5))))
            rows.append({"date": date.isoformat(), "term": term, "interest": interest})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "raw")
    os.makedirs(out, exist_ok=True)

    print("Generating CSO Labour Force Survey data...")
    lfs = make_lfs_data()
    lfs.to_csv(f"{out}/cso_lfs_youth_employment.csv", index=False)
    print(f"  → {len(lfs):,} rows saved")

    print("Generating Revenue self-assessment data...")
    rev = make_revenue_data()
    rev.to_csv(f"{out}/revenue_platform_filers.csv", index=False)
    print(f"  → {len(rev):,} rows saved")

    print("Generating WRC case data...")
    wrc = make_wrc_data()
    wrc.to_csv(f"{out}/wrc_platform_cases.csv", index=False)
    print(f"  → {len(wrc):,} rows saved")

    print("Generating Pobal deprivation index...")
    dep = make_deprivation_data()
    dep.to_csv(f"{out}/pobal_deprivation_index.csv", index=False)
    print(f"  → {len(dep):,} rows saved")

    print("Generating Google Trends proxy data...")
    trends = make_trends_data()
    trends.to_csv(f"{out}/google_trends_gig_ireland.csv", index=False)
    print(f"  → {len(trends):,} rows saved")

    print("\nAll datasets generated in data/raw/")
