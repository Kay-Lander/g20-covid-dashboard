-- ============================================================
--  COVID-19 G20 Dashboard — SQL Query Library
--  Data Source: Our World in Data (OWID)
--  Scope: G20 Nations (19 countries)
--  Author: Keith Sanders
-- ============================================================

-- G20 Countries in scope:
-- Argentina, Australia, Brazil, Canada, China, France, Germany,
-- India, Indonesia, Italy, Japan, Mexico, Russia, Saudi Arabia,
-- South Africa, South Korea, Turkey, United Kingdom, United States


-- ============================================================
--  QUERY 1: 7-Day Rolling Average of New Cases by Country
--  Window Function: AVG() OVER (PARTITION BY ... ROWS BETWEEN)
--  Use: Time-series chart with smoothed trend line
-- ============================================================
SELECT
    date,
    location,
    new_cases,
    ROUND(
        AVG(new_cases) OVER (
            PARTITION BY location
            ORDER BY date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 1
    ) AS rolling_7day_avg
FROM covid_data
ORDER BY location, date;


-- ============================================================
--  QUERY 2: G20 Country Rankings by Total Cases
--  Window Function: RANK() OVER (ORDER BY ...)
--  Use: Bar chart — ranked leaderboard of G20 nations
-- ============================================================
WITH latest_per_country AS (
    SELECT
        location,
        total_cases,
        total_deaths,
        ROW_NUMBER() OVER (
            PARTITION BY location
            ORDER BY date DESC
        ) AS rn
    FROM covid_data
)
SELECT
    location,
    total_cases,
    total_deaths,
    RANK() OVER (ORDER BY total_cases DESC)  AS case_rank,
    RANK() OVER (ORDER BY total_deaths DESC) AS death_rank
FROM latest_per_country
WHERE rn = 1
ORDER BY case_rank;


-- ============================================================
--  QUERY 3: Month-over-Month Change in New Cases
--  Window Function: LAG() OVER (PARTITION BY ... ORDER BY ...)
--  Use: Identifying which countries improved or worsened
-- ============================================================
WITH monthly_totals AS (
    SELECT
        location,
        STRFTIME('%Y-%m', date)  AS month,
        SUM(new_cases)           AS monthly_cases,
        SUM(new_deaths)          AS monthly_deaths
    FROM covid_data
    GROUP BY location, month
),
with_lag AS (
    SELECT
        location,
        month,
        monthly_cases,
        monthly_deaths,
        LAG(monthly_cases) OVER (
            PARTITION BY location
            ORDER BY month
        ) AS prev_month_cases
    FROM monthly_totals
)
SELECT
    location,
    month,
    monthly_cases,
    prev_month_cases,
    monthly_cases - prev_month_cases AS mom_change,
    ROUND(
        CASE
            WHEN prev_month_cases = 0 THEN NULL
            ELSE (monthly_cases - prev_month_cases) * 100.0 / prev_month_cases
        END, 1
    ) AS mom_pct_change
FROM with_lag
WHERE prev_month_cases IS NOT NULL
ORDER BY location, month;


-- ============================================================
--  QUERY 4: Peak Day Per Country (Worst Single Day)
--  Window Function: MAX() OVER (PARTITION BY ...)
--  Use: KPI card — "Worst Day" stat per selected country
-- ============================================================
WITH daily_max AS (
    SELECT
        location,
        date,
        new_cases,
        MAX(new_cases) OVER (
            PARTITION BY location
        ) AS country_peak
    FROM covid_data
)
SELECT
    location,
    date  AS peak_date,
    new_cases AS peak_cases
FROM daily_max
WHERE new_cases = country_peak
ORDER BY peak_cases DESC;


-- ============================================================
--  QUERY 5: Cumulative Case Growth — Running Total Check
--  Window Function: SUM() OVER (PARTITION BY ... ORDER BY ...)
--  Use: Verify total_cases column matches running sum of new_cases
--  (Data quality validation query)
-- ============================================================
SELECT
    location,
    date,
    new_cases,
    total_cases                              AS reported_total,
    SUM(new_cases) OVER (
        PARTITION BY location
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                        AS calculated_running_total,
    total_cases - SUM(new_cases) OVER (
        PARTITION BY location
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                        AS discrepancy
FROM covid_data
ORDER BY location, date;


-- ============================================================
--  QUERY 6: G20 Case Fatality Rate (CFR) by Country
--  Window Function: RANK() OVER (ORDER BY ...)
--  Use: Choropleth map color scale — CFR tells a different
--       story than raw case counts
-- ============================================================
WITH latest AS (
    SELECT
        location,
        total_cases,
        total_deaths,
        ROW_NUMBER() OVER (
            PARTITION BY location
            ORDER BY date DESC
        ) AS rn
    FROM covid_data
)
SELECT
    location,
    total_cases,
    total_deaths,
    ROUND(
        CASE
            WHEN total_cases = 0 THEN 0
            ELSE total_deaths * 100.0 / total_cases
        END, 3
    ) AS case_fatality_rate_pct,
    RANK() OVER (
        ORDER BY
            CASE
                WHEN total_cases = 0 THEN 0
                ELSE total_deaths * 100.0 / total_cases
            END DESC
    ) AS cfr_rank
FROM latest
WHERE rn = 1
ORDER BY cfr_rank;


-- ============================================================
--  QUERY 7: 30-Day Trailing Avg — Comparing G20 Countries
--  Window Function: AVG() OVER (PARTITION BY ... ROWS BETWEEN)
--  Use: Multi-line chart comparing smoothed trends across
--       all G20 nations on one chart
-- ============================================================
SELECT
    date,
    location,
    new_cases,
    ROUND(
        AVG(new_cases) OVER (
            PARTITION BY location
            ORDER BY date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 1
    ) AS rolling_30day_avg
FROM covid_data
ORDER BY date, location;


-- ============================================================
--  QUERY 8: First and Latest Date Per Country
--  Use: Data validation — confirm all G20 countries have
--       complete date coverage before building charts
-- ============================================================
SELECT
    location,
    MIN(date)          AS first_date,
    MAX(date)          AS latest_date,
    COUNT(*)           AS total_rows,
    SUM(new_cases)     AS total_cases_sum,
    MAX(total_cases)   AS reported_total_cases
FROM covid_data
GROUP BY location
ORDER BY location;