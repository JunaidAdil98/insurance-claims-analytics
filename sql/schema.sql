/* =====================================================================
   schema.sql  —  Auto-insurance claims warehouse (Microsoft SQL Server / T-SQL)
   Run order: schema.sql -> bulk-load the three CSVs -> analysis_queries.sql
   ===================================================================== */

IF OBJECT_ID('dbo.claims',    'U') IS NOT NULL DROP TABLE dbo.claims;
IF OBJECT_ID('dbo.policies',  'U') IS NOT NULL DROP TABLE dbo.policies;
IF OBJECT_ID('dbo.customers', 'U') IS NOT NULL DROP TABLE dbo.customers;

CREATE TABLE dbo.customers (
    customer_id   VARCHAR(12)  NOT NULL PRIMARY KEY,
    driver_age    SMALLINT     NOT NULL,
    region        VARCHAR(20)  NOT NULL,
    tenure_years  DECIMAL(5,1) NOT NULL,
    prior_claims  SMALLINT     NOT NULL
);

CREATE TABLE dbo.policies (
    policy_id       VARCHAR(12)   NOT NULL PRIMARY KEY,
    customer_id     VARCHAR(12)   NOT NULL REFERENCES dbo.customers(customer_id),
    coverage_type   VARCHAR(20)   NOT NULL,
    vehicle_age     SMALLINT      NOT NULL,
    annual_premium  DECIMAL(12,2) NOT NULL,
    accident_year   SMALLINT      NOT NULL
);

CREATE TABLE dbo.claims (
    claim_id         VARCHAR(12)   NOT NULL PRIMARY KEY,
    policy_id        VARCHAR(12)   NOT NULL REFERENCES dbo.policies(policy_id),
    customer_id      VARCHAR(12)   NOT NULL REFERENCES dbo.customers(customer_id),
    claim_type       VARCHAR(20)   NOT NULL,
    accident_date    DATE          NOT NULL,
    report_date      DATE          NOT NULL,
    settlement_date  DATE          NULL,
    status           VARCHAR(10)   NOT NULL,
    incurred_amount  DECIMAL(12,2) NOT NULL,
    paid_amount      DECIMAL(12,2) NOT NULL
);

CREATE INDEX ix_claims_policy ON dbo.claims(policy_id);
CREATE INDEX ix_claims_ay     ON dbo.claims(accident_date);
GO
