import sqlite3
import pandas as pd
from constants import DB_PATH, G20_COUNTRIES
 
 
def get_conn():
    return sqlite3.connect(DB_PATH)
 
 
def get_country_trend(location='United States'):
    '''
    Daily new cases + OWID 7-day smoothed average for one country.
    Powers the main time-series chart.
    '''
    query = '''
        SELECT date, location,
               new_cases,
               new_cases_smoothed  AS rolling_7day
        FROM   covid_data
        WHERE  location = ?
        ORDER  BY date
    '''
    conn = get_conn()
    df = pd.read_sql_query(query, conn,
                           params=(location,),
                           parse_dates=['date'])
    conn.close()
    return df
 
 
def get_g20_latest_totals():
    '''
    Most recent cumulative totals per G20 country.
    Window function: ROW_NUMBER() to get latest row per country.
    Powers: choropleth map, bar chart rankings.
    '''
    query = '''
        WITH ranked AS (
            SELECT location, iso_code,
                   total_cases, total_deaths, population,
                   ROW_NUMBER() OVER (
                       PARTITION BY location
                       ORDER BY date DESC
                   ) AS rn
            FROM covid_data
        )
        SELECT location, iso_code,
               total_cases, total_deaths, population,
               ROUND(total_deaths * 100.0 / NULLIF(total_cases, 0), 3) AS cfr_pct,
               RANK() OVER (ORDER BY total_cases DESC) AS case_rank
        FROM ranked
        WHERE rn = 1
        ORDER BY case_rank
    '''
    conn = get_conn()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
 
 
def get_multi_country_trend(locations=None):
    '''
    30-day smoothed trend for multiple countries.
    Window function: AVG() OVER (PARTITION BY location ROWS BETWEEN 29 PRECEDING)
    Powers: multi-country comparison line chart.
    '''
    if locations is None:
        locations = ['United States', 'India', 'Brazil',
                     'Germany', 'United Kingdom', 'France']
 
    placeholders = ','.join(['?' for _ in locations])
    query = f'''
        SELECT date, location, new_cases,
               ROUND(AVG(new_cases) OVER (
                   PARTITION BY location
                   ORDER BY date
                   ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
               ), 1) AS rolling_30day
        FROM  covid_data
        WHERE location IN ({placeholders})
        ORDER BY date, location
    '''
    conn = get_conn()
    df = pd.read_sql_query(query, conn,
                           params=locations,
                           parse_dates=['date'])
    conn.close()
    return df
 
 
def get_peak_days():
    '''
    Worst single day per G20 country.
    Window function: MAX() OVER (PARTITION BY location)
    Powers: peak day KPI card.
    '''
    query = '''
        WITH daily_with_peak AS (
            SELECT location, date, new_cases,
                   MAX(new_cases) OVER (
                       PARTITION BY location
                   ) AS country_peak
            FROM covid_data
        )
        SELECT location, date AS peak_date, new_cases AS peak_cases
        FROM   daily_with_peak
        WHERE  new_cases = country_peak
        ORDER  BY peak_cases DESC
    '''
    conn = get_conn()
    df = pd.read_sql_query(query, conn, parse_dates=['peak_date'])
    conn.close()
    return df
 
 
def get_monthly_mom():
    '''
    Month-over-month % change in new cases per country.
    Window function: LAG() OVER (PARTITION BY location ORDER BY month)
    Powers: MoM change bar chart.
    '''
    query = '''
        WITH monthly AS (
            SELECT location,
                   STRFTIME('%Y-%m', date) AS month,
                   SUM(new_cases)          AS monthly_cases
            FROM   covid_data
            GROUP  BY location, month
        ),
        with_lag AS (
            SELECT location, month, monthly_cases,
                   LAG(monthly_cases) OVER (
                       PARTITION BY location ORDER BY month
                   ) AS prev_month
            FROM monthly
        )
        SELECT location, month, monthly_cases, prev_month,
               monthly_cases - prev_month AS mom_change,
               ROUND(
                   CASE WHEN prev_month = 0 THEN NULL
                        ELSE (monthly_cases - prev_month) * 100.0 / prev_month
                   END, 1
               ) AS mom_pct
        FROM with_lag
        WHERE prev_month IS NOT NULL
        ORDER BY location, month
    '''
    conn = get_conn()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
 
 
def get_available_countries():
    '''Return sorted G20 country list for dropdown.'''
    conn = get_conn()
    df = pd.read_sql_query(
        'SELECT DISTINCT location FROM covid_data ORDER BY location', conn)
    conn.close()
    return df['location'].tolist()
