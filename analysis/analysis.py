"""
analysis.py
-----------
Full analytic pipeline on the simulated auto-insurance portfolio:

  1. Descriptive  : portfolio KPIs (frequency, severity, loss ratio)
  2. Diagnostic   : loss ratio & frequency broken down by segment
  3. Cohort       : accident-year loss-development triangle (% of ultimate paid)
  4. Regression   : (a) claim-severity linear model on log losses
                    (b) claim-occurrence logistic model (frequency drivers)

Outputs:
  - docs/dashboard_data.json  (consumed by the dashboard)
  - console summary of headline findings
"""

import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

cust = pd.read_csv("data/customers.csv")
pol = pd.read_csv("data/policies.csv")
clm = pd.read_csv("data/claims.csv", parse_dates=["accident_date", "report_date"])

clm["settlement_date"] = pd.to_datetime(clm["settlement_date"], errors="coerce")
full = clm.merge(pol, on=["policy_id", "customer_id"], how="left") \
          .merge(cust, on="customer_id", how="left")

AGE_BINS = [16, 25, 35, 50, 65, 99]
AGE_LABELS = ["16-24", "25-34", "35-49", "50-64", "65+"]


def age_band(s):
    return pd.cut(s, bins=AGE_BINS, labels=AGE_LABELS, right=False)


out = {}
pol_full = pol.merge(cust, on="customer_id", how="left")  # premium + region/age

# ----------------------------------------------------------------------
# 1. DESCRIPTIVE KPIs
# ----------------------------------------------------------------------
total_prem = float(pol["annual_premium"].sum())
total_incurred = float(clm["incurred_amount"].sum())
total_paid = float(clm["paid_amount"].sum())
n_claims = int(len(clm))
n_pol = int(len(pol))
open_claims = int((clm["status"] == "Open").sum())

out["kpis"] = {
    "policies": n_pol,
    "claims": n_claims,
    "frequency": round(n_claims / n_pol, 4),
    "earned_premium": round(total_prem, 0),
    "incurred": round(total_incurred, 0),
    "paid": round(total_paid, 0),
    "loss_ratio": round(total_incurred / total_prem, 4),
    "avg_severity": round(total_incurred / n_claims, 0),
    "open_claims": open_claims,
    "open_share": round(open_claims / n_claims, 4),
}

# ----------------------------------------------------------------------
# 2. DIAGNOSTIC breakdowns
# ----------------------------------------------------------------------
# loss ratio by region (incurred / premium for that segment)
prem_by_region = pol_full.groupby("region")["annual_premium"].sum()
inc_by_region = full.groupby("region")["incurred_amount"].sum()
lr_region = (inc_by_region / prem_by_region).sort_values(ascending=False)
out["loss_ratio_by_region"] = [
    {"region": r, "loss_ratio": round(float(lr_region[r]), 3),
     "premium": round(float(prem_by_region[r]), 0),
     "incurred": round(float(inc_by_region.get(r, 0)), 0)}
    for r in lr_region.index
]

# loss ratio by coverage
prem_by_cov = pol.groupby("coverage_type")["annual_premium"].sum()
inc_by_cov = full.groupby("coverage_type")["incurred_amount"].sum()
lr_cov = (inc_by_cov / prem_by_cov).sort_values(ascending=False)
out["loss_ratio_by_coverage"] = [
    {"coverage": c, "loss_ratio": round(float(lr_cov[c]), 3)}
    for c in lr_cov.index
]

# claim frequency by driver age band  (claims per policy in band)
pol_band = age_band(pol_full["driver_age"])
pol_count_band = pol_band.value_counts()
clm_band = age_band(full["driver_age"]).value_counts()
freq_band = (clm_band / pol_count_band).reindex(AGE_LABELS).fillna(0)
out["frequency_by_age"] = [
    {"age_band": b, "frequency": round(float(freq_band[b]), 3)} for b in AGE_LABELS
]

# average severity by claim type
sev_type = full.groupby("claim_type")["incurred_amount"].agg(["mean", "count"]).sort_values("mean", ascending=False)
out["severity_by_type"] = [
    {"claim_type": t, "avg_severity": round(float(sev_type.loc[t, "mean"]), 0),
     "count": int(sev_type.loc[t, "count"])}
    for t in sev_type.index
]

# ----------------------------------------------------------------------
# 3. COHORT / LOSS DEVELOPMENT  (accident-year triangle)
# ----------------------------------------------------------------------
dev_ages = [6, 12, 18, 24, 30, 36, 42, 48]
cohort = {}
for yr, g in full.groupby("accident_year"):
    start = pd.Timestamp(year=int(yr), month=1, day=1)
    ultimate = g["incurred_amount"].sum()
    settled = g.dropna(subset=["settlement_date"]).copy()
    settled["dev_months"] = (settled["settlement_date"] - start).dt.days / 30.44
    curve = []
    for d in dev_ages:
        paid_to_date = settled.loc[settled["dev_months"] <= d, "paid_amount"].sum()
        curve.append(round(float(paid_to_date / ultimate), 3) if ultimate else 0.0)
    cohort[int(yr)] = curve
out["loss_development"] = {"dev_ages": dev_ages, "cohorts": cohort}

# ----------------------------------------------------------------------
# 4a. REGRESSION — claim severity (log-linear)
# ----------------------------------------------------------------------
sev = full.copy()
sev["winter"] = sev["accident_date"].dt.month.isin([11, 12, 1, 2, 3]).astype(int)
sev["log_incurred"] = np.log(sev["incurred_amount"].clip(lower=1))
feat_num = ["driver_age", "vehicle_age", "prior_claims", "winter"]
X = pd.concat([
    sev[feat_num],
    pd.get_dummies(sev["region"], prefix="region", drop_first=True),
    pd.get_dummies(sev["coverage_type"], prefix="cov", drop_first=True),
    pd.get_dummies(sev["claim_type"], prefix="type", drop_first=True),
], axis=1).astype(float)
y = sev["log_incurred"].values
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=7)
lin = LinearRegression().fit(Xtr, ytr)
r2 = r2_score(yte, lin.predict(Xte))
# express coefficients as % effect on severity (exp(coef)-1) for interpretability
coefs = sorted(
    [{"feature": f, "pct_effect": round(float(np.exp(c) - 1) * 100, 1)}
     for f, c in zip(X.columns, lin.coef_)],
    key=lambda d: abs(d["pct_effect"]), reverse=True
)[:8]
out["severity_model"] = {"r2": round(float(r2), 3), "drivers": coefs}

# ----------------------------------------------------------------------
# 4b. REGRESSION — claim occurrence (logistic, frequency drivers)
# ----------------------------------------------------------------------
freq = pol.merge(cust, on="customer_id", how="left")
has_claim = full.groupby("policy_id")["claim_id"].count()
freq["had_claim"] = (freq["policy_id"].map(has_claim).fillna(0) > 0).astype(int)
Xf = pd.concat([
    freq[["driver_age", "vehicle_age", "prior_claims", "tenure_years"]],
    pd.get_dummies(freq["region"], prefix="region", drop_first=True),
    pd.get_dummies(freq["coverage_type"], prefix="cov", drop_first=True),
], axis=1).astype(float)
yf = freq["had_claim"].values
scaler = StandardScaler()
Xf_s = scaler.fit_transform(Xf)
Xtr, Xte, ytr, yte = train_test_split(Xf_s, yf, test_size=0.25, random_state=7)
logit = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
auc = roc_auc_score(yte, logit.predict_proba(Xte)[:, 1])
odds = sorted(
    [{"feature": f, "odds_ratio": round(float(np.exp(c)), 2)}
     for f, c in zip(Xf.columns, logit.coef_[0])],
    key=lambda d: abs(np.log(d["odds_ratio"])), reverse=True
)[:7]
out["frequency_model"] = {"auc": round(float(auc), 3), "drivers": odds}

# ----------------------------------------------------------------------
with open("docs/dashboard_data.json", "w") as f:
    json.dump(out, f, indent=2)

# ---- console findings ----
k = out["kpis"]
print("=" * 60)
print("PORTFOLIO HEADLINE")
print("=" * 60)
print(f"  Policies {k['policies']:,} | Claims {k['claims']:,} | Frequency {k['frequency']:.1%}")
print(f"  Earned premium ${k['earned_premium']:,.0f} | Incurred ${k['incurred']:,.0f}")
print(f"  LOSS RATIO {k['loss_ratio']:.1%}  | Avg severity ${k['avg_severity']:,.0f}")
print(f"  Open claims {k['open_claims']:,} ({k['open_share']:.1%})")
print("\nWORST LOSS-RATIO REGIONS")
for r in out["loss_ratio_by_region"][:3]:
    print(f"  {r['region']:<10} {r['loss_ratio']:.0%}")
print("\nSEVERITY MODEL  R^2 =", out["severity_model"]["r2"])
for d in out["severity_model"]["drivers"][:4]:
    print(f"  {d['feature']:<20} {d['pct_effect']:+.1f}% on severity")
print("\nFREQUENCY MODEL  AUC =", out["frequency_model"]["auc"])
for d in out["frequency_model"]["drivers"][:4]:
    print(f"  {d['feature']:<20} odds x{d['odds_ratio']}")
print("\nwrote docs/dashboard_data.json")
