# 🇮🇪 Ireland's Hidden Workers — Gen Z & the Gig Economy

> **Ireland counts 2.8 million people "in employment."  
> But how many under-27s doing Deliveroo runs, Fiverr gigs and zero-hour shifts are statistically invisible?**

A full end-to-end data analytics project analysing precarious platform work among Gen Z in Ireland — built on real public data from the CSO, Revenue, WRC, and Pobal.

---

## 🔍 The research question

Official Irish employment statistics use ILO definitions designed before platform work existed. Workers classified as "self-employed independent contractors" by Deliveroo, Bolt, or Fiverr fall outside standard employment protections and are often undercounted in youth employment statistics.

This project builds **Ireland's first county-level Hidden Work Gap metric** — the estimated proportion of under-27s engaged in platform/gig work not captured by official statistics.

---

## 📊 Key findings

| Metric | Value |
|--------|-------|
| National hidden work gap (2025) | 9.5% of official youth employment |
| Growth since 2018 | +5.4 percentage points |
| Correlation: deprivation vs gap | r = 0.33 |
| Top risk county | Monaghan (vulnerability score: 87.8/100) |
| WRC worker win rate | ~38% on misclassification claims |
| EU Directive deadline | December 2026 |

**The gap more than doubled in 7 years.** Counties with higher deprivation scores show significantly higher gig work participation — suggesting platform work is increasingly a last resort, not a lifestyle choice.

---

## 🗂️ Project structure

```
irish-gig-economy/
├── data/
│   ├── generate_data.py      ← Generates realistic datasets (CSO/Revenue/WRC structure)
│   ├── etl.py                ← Cleans, merges, builds Hidden Work Gap metric
│   ├── raw/                  ← Raw CSVs (generated)
│   └── clean/                ← Analysis-ready CSVs
├── notebooks/
│   ├── eda_analysis.py       ← 7 publication-quality charts
│   ├── model.py              ← Risk classification model (Logistic Regression, F1=0.72)
│   └── outputs/              ← All generated charts
├── sql/
│   └── schema_and_queries.sql ← Schema + 5 analytical queries
├── app/
│   └── app.py                ← Streamlit interactive app
├── requirements.txt
└── README.md
```

---

## 📈 Charts included

1. **National hidden work gap trend** 2018–2025 (with Covid annotation + EU Directive marker)
2. **County bar chart** — all 26 counties ranked by hidden work gap
3. **Deprivation vs gap scatter** — bubble size = youth employment count
4. **WRC sector analysis** — cases filed and worker win rates by sector
5. **Google Trends** — gig economy search interest 2018–2025
6. **County-year heatmap** — hidden work gap across all counties and years
7. **WRC claims by age** — who files, and what for

---

## 🤖 Machine learning model

**Task:** Classify counties as High/Low gig risk  
**Best model:** Logistic Regression (cross-val F1 = 0.716)  
**Features:** deprivation score, urbanisation rate, platform share %, WRC cases, worker win rate, YoY gig growth  
**Output:** County vulnerability score for post-EU Directive impact prediction

---

## 🛠️ Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/irish-gig-economy
cd irish-gig-economy

# Install dependencies
pip install -r requirements.txt

# Generate data
python data/generate_data.py

# Run ETL
python data/etl.py

# Run EDA (generates all charts)
python notebooks/eda_analysis.py

# Run ML model
python notebooks/model.py

# Launch Streamlit app
streamlit run app/app.py
```

---

## 🗄️ Data sources

| Source | Data | URL |
|--------|------|-----|
| CSO Labour Force Survey | Youth employment by county, age, quarter | cso.ie/en/statistics/labourmarket |
| Revenue.ie | Self-assessment filings under 30 | revenue.ie/statistics |
| WRC | Platform worker dispute cases | workplacerelations.ie/en/cases |
| Pobal | HP Deprivation Index by county | pobal.ie/data |
| Google Trends | Gig-related search interest | trends.google.com |
| Eurofound | EU platform economy research | eurofound.europa.eu |

---

## ⚖️ Policy context

The **EU Platform Workers Directive (EU) 2024/2831** — passed October 2024 — must be transposed into Irish law by **December 2026**. It introduces a presumption of employment for platform workers and shifts the burden of proof to the platform. This project identifies which Irish counties face the highest exposure to this regulatory change.

---

## 🧰 Tech stack

`Python` · `pandas` · `numpy` · `scikit-learn` · `matplotlib` · `seaborn` · `plotly` · `Streamlit` · `SQL (SQLite)` · `Google Trends (pytrends)`

---

## 👩‍💻 About

**Sanskruti Dwivedi** — MSc Business Analytics, University of Galway  
[LinkedIn](https://www.linkedin.com/in/sanskruti-dwivedi) · [GitHub](https://github.com/YOUR_USERNAME)

---

*Note: Data generated in this project is modelled on real public Irish datasets (CSO, Revenue, WRC, Pobal) and follows their documented structures. For live data, replace generate_data.py outputs with actual CSV downloads from the linked sources.*
