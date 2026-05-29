"""
model.py
Predictive model — classifies counties as High/Low gig risk
and forecasts post-EU Directive (Dec 2026) vulnerability.

Outputs:
  - model_results.csv   (per-county predictions + probabilities)
  - feature_importance.png
  - classification_report.txt
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings("ignore")

BASE  = Path(__file__).parent.parent
CLEAN = BASE / "data" / "clean"
OUT   = BASE / "notebooks" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

TEAL   = "#1D9E75"
CORAL  = "#D85A30"
PURPLE = "#7F77DD"
AMBER  = "#EF9F27"

# ── Load data ─────────────────────────────────────────────────
master = pd.read_csv(CLEAN / "county_master.csv")

# Use 2022-2024 data for training (avoid Covid years + leave 2025 for prediction)
train = master[master["year"].between(2022, 2024)].copy()
predict_df = master[master["year"] == master["year"].max()].copy()

FEATURES = [
    "deprivation_score",
    "urbanisation_rate",
    "avg_employment_rate_u27",
    "official_self_emp_u27",
    "platform_share_pct",
    "total_cases",
    "worker_win_rate",
    "gig_yoy_growth",
]

# Binary target: High risk = gap_score > 50
train["target"] = (train["gap_score"] > 50).astype(int)
predict_df["target"] = (predict_df["gap_score"] > 50).astype(int)

# Clean features
def prep(df):
    X = df[FEATURES].copy()
    X["gig_yoy_growth"] = X["gig_yoy_growth"].fillna(0)
    X["total_cases"] = X["total_cases"].fillna(0)
    X["worker_win_rate"] = X["worker_win_rate"].fillna(50)
    return X

X_train = prep(train)
y_train = train["target"]
X_pred  = prep(predict_df)
y_pred_true = predict_df["target"]

# ── Models ────────────────────────────────────────────────────
models = {
    "Random Forest":         RandomForestClassifier(n_estimators=200, max_depth=5,
                                                     random_state=42, class_weight="balanced"),
    "Gradient Boosting":     GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                                         learning_rate=0.1, random_state=42),
    "Logistic Regression":   Pipeline([
                                ("scaler", StandardScaler()),
                                ("clf",    LogisticRegression(C=1.0, random_state=42,
                                                               class_weight="balanced")),
                             ]),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
print("=== Cross-validation results (5-fold) ===")
best_model, best_score = None, 0
for name, model in models.items():
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_weighted")
    print(f"  {name:25s}  F1 = {scores.mean():.3f} ± {scores.std():.3f}")
    if scores.mean() > best_score:
        best_score = scores.mean()
        best_model = (name, model)

print(f"\nBest model: {best_model[0]} (F1={best_score:.3f})")

# ── Fit best model ────────────────────────────────────────────
clf = best_model[1]
clf.fit(X_train, y_train)
y_hat   = clf.predict(X_pred)
try:
    y_prob  = clf.predict_proba(X_pred)[:, 1]
except AttributeError:
    y_prob  = clf.decision_function(X_pred)

# ── Results ───────────────────────────────────────────────────
results = predict_df[["county","hidden_work_gap_pct","gap_score",
                       "risk_category","deprivation_score"]].copy()
results["predicted_high_risk"] = y_hat
results["high_risk_probability"] = np.round(y_prob, 3)
results["prediction_correct"] = (y_hat == y_pred_true).astype(int)

# Composite vulnerability score (for post-EU-Directive ranking)
results["vulnerability_score"] = (
    results["hidden_work_gap_pct"] / results["hidden_work_gap_pct"].max() * 40 +
    results["deprivation_score"]   / results["deprivation_score"].max()   * 40 +
    results["high_risk_probability"]                                       * 20
).round(1)

results = results.sort_values("vulnerability_score", ascending=False)
results.to_csv(CLEAN / "model_results.csv", index=False)

# ── Classification report ─────────────────────────────────────
report = classification_report(y_pred_true, y_hat,
                                target_names=["Low risk","High risk"])
report_text = (
    f"Irish Gig Economy — Risk Classification Model\n"
    f"Model: {best_model[0]}\n"
    f"Training period: 2022–2024\n"
    f"Prediction year: {master['year'].max()}\n"
    f"Features: {', '.join(FEATURES)}\n"
    f"Cross-val F1: {best_score:.3f}\n\n"
    f"{report}"
)
with open(OUT / "classification_report.txt", "w") as f:
    f.write(report_text)
print("\n" + report_text)

# ── Feature importance chart ───────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150, "figure.facecolor": "white",
    "axes.facecolor": "#fafafa", "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True,
    "grid.alpha": 0.3, "grid.linestyle": "--",
})

try:
    # Random Forest / Gradient Boosting have feature_importances_
    clf_inner = clf if not hasattr(clf, "named_steps") else clf.named_steps["clf"]
    importances = clf_inner.feature_importances_
except AttributeError:
    importances = np.abs(clf.named_steps["clf"].coef_[0])

feat_df = pd.DataFrame({
    "feature": [f.replace("_", " ").title() for f in FEATURES],
    "importance": importances,
}).sort_values("importance", ascending=True)

fig, ax = plt.subplots(figsize=(9, 5))
colors = [CORAL if v == feat_df["importance"].max() else TEAL for v in feat_df["importance"]]
ax.barh(feat_df["feature"], feat_df["importance"], color=colors,
        height=0.6, edgecolor="none")
ax.set_xlabel("Feature importance")
ax.set_title(f"Feature Importance — {best_model[0]}\n"
             "What best predicts a county being 'High gig risk'?")
plt.tight_layout()
plt.savefig(OUT / "feature_importance.png", bbox_inches="tight")
plt.close()
print("\nFeature importance chart saved")

# ── Vulnerability ranking chart ───────────────────────────────
import matplotlib.patches as mpatches
fig, ax = plt.subplots(figsize=(10, 7))
top = results.head(15).sort_values("vulnerability_score", ascending=True)
bar_colors = [CORAL if r == "Critical" else AMBER if r == "High"
              else TEAL for r in top["risk_category"]]
bars = ax.barh(top["county"], top["vulnerability_score"],
               color=bar_colors, height=0.65, edgecolor="none")
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.3, bar.get_y() + bar.get_height()/2,
            f"{w:.0f}", va="center", fontsize=8.5)

patches = [
    mpatches.Patch(color=CORAL, label="Critical"),
    mpatches.Patch(color=AMBER, label="High"),
    mpatches.Patch(color=TEAL,  label="Medium/Low"),
]
ax.legend(handles=patches, title="Risk category", fontsize=8)
ax.set_xlabel("Composite vulnerability score (0–100)")
ax.set_title("Top 15 Most Vulnerable Counties — Post EU Directive Dec 2026\n"
             "Composite of: hidden gap + deprivation + model probability")
plt.tight_layout()
plt.savefig(OUT / "vulnerability_ranking.png", bbox_inches="tight")
plt.close()

print(f"\nTop 5 most vulnerable counties post-EU Directive:")
print(results[["county","vulnerability_score","risk_category"]].head().to_string(index=False))
print("\nModel complete. Results in data/clean/model_results.csv")
