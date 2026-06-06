"""
generate_data.py
------------------
Generates a realistic *simulated* auto-insurance portfolio:
  - customers.csv : policyholder demographics
  - policies.csv  : annual auto policies with premium + risk attributes
  - claims.csv    : claims with accident/report/settlement dates and paid amounts

The data is synthetic but built with deliberate statistical structure so that
descriptive, diagnostic, cohort, and regression analyses recover real signal
(e.g. young urban drivers have higher claim frequency; comprehensive claims
in winter cost more). This is a portfolio demonstration -- NOT real data.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

N_CUSTOMERS = 9000
ACCIDENT_YEARS = [2021, 2022, 2023, 2024]
REGIONS = {
    # region: (relative claim frequency multiplier, relative severity multiplier, share)
    "Toronto":   (1.30, 1.15, 0.26),
    "Montreal":  (1.20, 1.05, 0.22),
    "Vancouver": (1.15, 1.20, 0.16),
    "Calgary":   (1.00, 1.00, 0.12),
    "Ottawa":    (0.85, 0.95, 0.12),
    "Halifax":   (0.75, 0.90, 0.12),
}
COVERAGES = {
    # coverage: (base annual premium, frequency mult, severity mult, share)
    "Liability":      (820,  0.75, 0.80, 0.30),
    "Collision":      (1150, 1.10, 1.10, 0.40),
    "Comprehensive":  (1480, 1.25, 1.30, 0.30),
}
CLAIM_TYPES = {
    # type: (share, severity multiplier, mean settlement lag days)
    "Collision":   (0.42, 1.10, 95),
    "Liability":   (0.18, 1.55, 180),
    "Theft":       (0.10, 1.35, 70),
    "Weather":     (0.18, 0.85, 55),
    "Glass/Minor": (0.12, 0.35, 25),
}


def make_customers():
    region_names = list(REGIONS.keys())
    region_p = np.array([REGIONS[r][2] for r in region_names])
    region_p /= region_p.sum()
    cust = pd.DataFrame({
        "customer_id": [f"C{100000 + i}" for i in range(N_CUSTOMERS)],
        "driver_age": np.clip(RNG.gamma(shape=2.5, scale=11.0, size=N_CUSTOMERS) + 18, 18, 90).round().astype(int),
        "region": RNG.choice(region_names, size=N_CUSTOMERS, p=region_p),
        "tenure_years": np.clip(RNG.exponential(scale=5.0, size=N_CUSTOMERS), 0, 35).round(1),
        "prior_claims": RNG.poisson(0.35, size=N_CUSTOMERS),
    })
    return cust


def make_policies(cust):
    cov_names = list(COVERAGES.keys())
    cov_p = np.array([COVERAGES[c][3] for c in cov_names])
    cov_p /= cov_p.sum()
    n = len(cust)
    coverage = RNG.choice(cov_names, size=n, p=cov_p)
    vehicle_age = np.clip(RNG.gamma(shape=2.2, scale=2.8, size=n), 0, 25).round().astype(int)

    base_prem = np.array([COVERAGES[c][0] for c in coverage], dtype=float)
    # young drivers and prior claims raise premium; tenure lowers it
    age = cust["driver_age"].values
    young_load = np.where(age < 25, 1.55, np.where(age < 35, 1.18, 1.0))
    senior_load = np.where(age > 75, 1.12, 1.0)
    prior_load = 1.0 + 0.18 * cust["prior_claims"].values
    tenure_disc = np.clip(1.0 - 0.012 * cust["tenure_years"].values, 0.80, 1.0)
    region_load = np.array([REGIONS[r][0] for r in cust["region"].values])
    veh_load = 1.0 + 0.015 * vehicle_age

    premium = (base_prem * young_load * senior_load * prior_load
               * tenure_disc * region_load * veh_load)
    premium *= RNG.normal(1.0, 0.06, size=n)  # pricing noise
    premium = premium.round(2)

    pol = pd.DataFrame({
        "policy_id": [f"P{500000 + i}" for i in range(n)],
        "customer_id": cust["customer_id"].values,
        "coverage_type": coverage,
        "vehicle_age": vehicle_age,
        "annual_premium": premium,
        "accident_year": RNG.choice(ACCIDENT_YEARS, size=n,
                                    p=[0.22, 0.24, 0.27, 0.27]),
    })
    return pol


def make_claims(cust, pol):
    df = pol.merge(cust, on="customer_id", how="left")
    age = df["driver_age"].values

    # ---- expected claim frequency (Poisson rate) ----
    age_freq = np.where(age < 25, 1.9, np.where(age < 35, 1.25,
               np.where(age < 60, 1.0, np.where(age < 75, 0.95, 1.25))))
    region_freq = np.array([REGIONS[r][0] for r in df["region"].values])
    cov_freq = np.array([COVERAGES[c][1] for c in df["coverage_type"].values])
    prior_freq = 1.0 + 0.22 * df["prior_claims"].values
    veh_freq = 1.0 + 0.02 * df["vehicle_age"].values
    base_rate = 0.16
    lam = base_rate * age_freq * region_freq * cov_freq * prior_freq * veh_freq
    n_claims = RNG.poisson(lam)

    rows = []
    ct_names = list(CLAIM_TYPES.keys())
    ct_p = np.array([CLAIM_TYPES[c][0] for c in ct_names]); ct_p /= ct_p.sum()
    claim_counter = 0
    for i in range(len(df)):
        for _ in range(n_claims[i]):
            yr = int(df["accident_year"].values[i])
            # accident date within the accident year
            doy = int(RNG.integers(0, 365))
            acc = pd.Timestamp(year=yr, month=1, day=1) + pd.Timedelta(days=doy)
            ctype = RNG.choice(ct_names, p=ct_p)

            # ---- severity (gamma) with structured multipliers ----
            region_sev = REGIONS[df["region"].values[i]][1]
            cov_sev = COVERAGES[df["coverage_type"].values[i]][2]
            type_sev = CLAIM_TYPES[ctype][1]
            # weather claims cost more in winter months
            winter = acc.month in (11, 12, 1, 2, 3)
            season_sev = 1.25 if (ctype == "Weather" and winter) else 1.0
            young_sev = 1.12 if age[i] < 25 else 1.0
            mean_sev = 4200 * region_sev * cov_sev * type_sev * season_sev * young_sev
            severity = float(RNG.gamma(shape=2.0, scale=mean_sev / 2.0))
            severity = round(min(severity, 120000), 2)

            report_lag = int(np.clip(RNG.exponential(9), 0, 120))
            report = acc + pd.Timedelta(days=report_lag)
            settle_lag = int(np.clip(RNG.normal(CLAIM_TYPES[ctype][2], 30), 5, 720))
            settle = report + pd.Timedelta(days=settle_lag)
            # ~8% of recent claims still open
            status = "Open" if (settle > pd.Timestamp("2025-01-01") and RNG.random() < 0.6) else "Closed"
            paid = severity if status == "Closed" else round(severity * RNG.uniform(0.2, 0.7), 2)

            rows.append({
                "claim_id": f"CL{900000 + claim_counter}",
                "policy_id": df["policy_id"].values[i],
                "customer_id": df["customer_id"].values[i],
                "claim_type": ctype,
                "accident_date": acc.date().isoformat(),
                "report_date": report.date().isoformat(),
                "settlement_date": settle.date().isoformat() if status == "Closed" else "",
                "status": status,
                "incurred_amount": severity,
                "paid_amount": paid,
            })
            claim_counter += 1

    claims = pd.DataFrame(rows)
    return claims


if __name__ == "__main__":
    cust = make_customers()
    pol = make_policies(cust)
    claims = make_claims(cust, pol)

    cust.to_csv("data/customers.csv", index=False)
    pol.to_csv("data/policies.csv", index=False)
    claims.to_csv("data/claims.csv", index=False)

    print(f"customers: {len(cust):,}")
    print(f"policies : {len(pol):,}")
    print(f"claims   : {len(claims):,}")
    print(f"claim freq (claims/policy): {len(claims)/len(pol):.3f}")
    print(f"total earned premium: ${pol['annual_premium'].sum():,.0f}")
    print(f"total incurred     : ${claims['incurred_amount'].sum():,.0f}")
    print(f"portfolio loss ratio: {claims['incurred_amount'].sum()/pol['annual_premium'].sum():.1%}")
