/* =====================================================================
   analysis_queries.sql  —  Descriptive, diagnostic & cohort analysis (T-SQL)
   Mirrors analysis.py so results can be cross-checked between SQL and Python.
   ===================================================================== */

/* ---------------------------------------------------------------------
   1. PORTFOLIO KPIs  — frequency, severity, loss ratio
   --------------------------------------------------------------------- */
WITH prem AS (SELECT SUM(annual_premium) AS earned_premium, COUNT(*) AS policies FROM dbo.policies),
     loss AS (SELECT SUM(incurred_amount) AS incurred, COUNT(*) AS claims,
                     AVG(incurred_amount) AS avg_severity,
                     SUM(CASE WHEN status='Open' THEN 1 ELSE 0 END) AS open_claims
              FROM dbo.claims)
SELECT  p.policies,
        l.claims,
        CAST(l.claims AS DECIMAL(10,4)) / p.policies            AS frequency,
        p.earned_premium,
        l.incurred,
        CAST(l.incurred AS DECIMAL(18,4)) / p.earned_premium    AS loss_ratio,
        l.avg_severity,
        l.open_claims
FROM prem p CROSS JOIN loss l;


/* ---------------------------------------------------------------------
   2. DIAGNOSTIC  — loss ratio by region (premium and losses joined by segment)
   --------------------------------------------------------------------- */
WITH prem AS (
    SELECT c.region, SUM(p.annual_premium) AS premium
    FROM dbo.policies p JOIN dbo.customers c ON c.customer_id = p.customer_id
    GROUP BY c.region),
loss AS (
    SELECT c.region, SUM(cl.incurred_amount) AS incurred
    FROM dbo.claims cl JOIN dbo.customers c ON c.customer_id = cl.customer_id
    GROUP BY c.region)
SELECT  pr.region,
        pr.premium,
        ls.incurred,
        CAST(ls.incurred AS DECIMAL(18,4)) / pr.premium AS loss_ratio
FROM prem pr JOIN loss ls ON ls.region = pr.region
ORDER BY loss_ratio DESC;


/* ---------------------------------------------------------------------
   3. DIAGNOSTIC  — claim frequency by driver-age band (CASE binning)
   --------------------------------------------------------------------- */
WITH banded AS (
    SELECT p.policy_id,
           CASE WHEN c.driver_age < 25 THEN '16-24'
                WHEN c.driver_age < 35 THEN '25-34'
                WHEN c.driver_age < 50 THEN '35-49'
                WHEN c.driver_age < 65 THEN '50-64'
                ELSE '65+' END AS age_band
    FROM dbo.policies p JOIN dbo.customers c ON c.customer_id = p.customer_id),
clm AS (
    SELECT policy_id, COUNT(*) AS n FROM dbo.claims GROUP BY policy_id)
SELECT  b.age_band,
        COUNT(*)                                              AS policies,
        SUM(ISNULL(cl.n,0))                                   AS claims,
        CAST(SUM(ISNULL(cl.n,0)) AS DECIMAL(10,4))/COUNT(*)   AS frequency
FROM banded b LEFT JOIN clm cl ON cl.policy_id = b.policy_id
GROUP BY b.age_band
ORDER BY b.age_band;


/* ---------------------------------------------------------------------
   4. DIAGNOSTIC  — average severity by claim type
   --------------------------------------------------------------------- */
SELECT  claim_type,
        COUNT(*)                  AS claim_count,
        AVG(incurred_amount)      AS avg_severity,
        SUM(incurred_amount)      AS total_incurred
FROM dbo.claims
GROUP BY claim_type
ORDER BY avg_severity DESC;


/* ---------------------------------------------------------------------
   5. COHORT  — accident-year loss development (% of ultimate paid by dev age)
   Window function builds the ultimate-per-cohort; DATEDIFF derives dev months.
   --------------------------------------------------------------------- */
WITH base AS (
    SELECT  accident_year = YEAR(accident_date),
            paid_amount,
            incurred_amount,
            dev_months = DATEDIFF(MONTH,
                            DATEFROMPARTS(YEAR(accident_date),1,1),
                            COALESCE(settlement_date, '9999-12-31'))
    FROM dbo.claims),
ult AS (
    SELECT accident_year, SUM(incurred_amount) AS ultimate
    FROM base GROUP BY accident_year)
SELECT  b.accident_year,
        dev.age AS dev_age_months,
        CAST(SUM(CASE WHEN b.dev_months <= dev.age THEN b.paid_amount ELSE 0 END)
             AS DECIMAL(18,4)) / u.ultimate AS pct_of_ultimate_paid
FROM base b
CROSS JOIN (VALUES (6),(12),(18),(24),(30),(36),(42),(48)) AS dev(age)
JOIN ult u ON u.accident_year = b.accident_year
GROUP BY b.accident_year, dev.age, u.ultimate
ORDER BY b.accident_year, dev.age;


/* ---------------------------------------------------------------------
   6. SEGMENTATION  — rank policyholders into risk quartiles by incurred loss
   (NTILE window function; feeds a simple risk-tiering view)
   --------------------------------------------------------------------- */
WITH policy_loss AS (
    SELECT p.policy_id, p.annual_premium,
           ISNULL(SUM(cl.incurred_amount),0) AS incurred
    FROM dbo.policies p
    LEFT JOIN dbo.claims cl ON cl.policy_id = p.policy_id
    GROUP BY p.policy_id, p.annual_premium)
SELECT  risk_quartile,
        COUNT(*)                                       AS policies,
        AVG(annual_premium)                            AS avg_premium,
        AVG(incurred)                                  AS avg_incurred,
        CAST(SUM(incurred) AS DECIMAL(18,4))/SUM(annual_premium) AS loss_ratio
FROM (
    SELECT *, NTILE(4) OVER (ORDER BY incurred DESC) AS risk_quartile
    FROM policy_loss) q
GROUP BY risk_quartile
ORDER BY risk_quartile;
GO
