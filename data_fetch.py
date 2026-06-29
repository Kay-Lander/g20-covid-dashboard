"""
!!! RETIRED DATA SOURCE — THIS PIPELINE NO LONGER RUNS !!!

This script was the original ingest pipeline: it downloaded the full
Our World in Data COVID CSV (OWID_URL in constants.py) and built the
covid_data table from scratch.

Our World in Data has RETIRED that legacy endpoint
(https://covid.ourworldindata.org/data/owid-covid-data.csv). The host no
longer resolves, so fetch_owid_data() will fail with a DNS/connection error.
Do NOT rely on this to (re)build the database.

CURRENT STATE OF THE DATA:
  - The live database is data/covid.db (see DB_PATH in constants.py).
  - It already holds all 19 G20 countries for 2020-2024.
  - The three columns OWID used to supply (iso_code, population,
    new_cases_smoothed) are backfilled by enrich_db.py, NOT by this script.

IF YOU NEED TO REBUILD / REFRESH:
  - Replace fetch_owid_data() with a working source (OWID now publishes
    per-metric files under https://catalog.ourworldindata.org/ and the
    github.com/owid/covid-19-data repo), then re-run enrich_db.py afterward
    to restore the derived columns.
  - Until then, run `python enrich_db.py` to (re)derive columns on covid.db.

This file is kept for reference only.
"""
import requests
import pandas as pd
import sqlite3
import os
from datetime import datetime
from constants import G20_COUNTRIES, G20_ISO_CODES, DB_PATH, OWID_URL
 
 
def fetch_owid_data():
    '''Pull full OWID COVID dataset — no API key needed.'''
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Fetching OWID data...')
    response = requests.get(OWID_URL, timeout=120)
    response.raise_for_status()
 
    # Read CSV directly from response content
    from io import StringIO
    df = pd.read_csv(StringIO(response.text))
    print(f'  Raw rows pulled : {len(df):>10,}')
    print(f'  Raw columns     : {len(df.columns):>10}')
    return df
 
 
def filter_g20(df):
    '''Keep only the 19 G20 member countries.'''
    df_g20 = df[df['location'].isin(G20_COUNTRIES)].copy()
    print(f'  After G20 filter: {len(df_g20):>10,} rows')
    print(f'  Countries found : {df_g20["location"].nunique():>10}')
 
    # Verify all 19 countries are present
    found    = set(df_g20['location'].unique())
    missing  = set(G20_COUNTRIES) - found
    if missing:
        print(f'  WARNING — Missing countries: {missing}')
    return df_g20
 
 
def clean_data(df):
    '''Select columns, fix types, remove bad rows.'''
 
    keep_cols = [
        'location', 'iso_code', 'date',
        'new_cases', 'new_deaths',
        'total_cases', 'total_deaths',
        'new_cases_smoothed',          # OWID pre-calculated 7-day avg
        'new_deaths_smoothed',
        'people_vaccinated_per_hundred',
        'population'
    ]
 
    # Keep only columns that exist (some may be missing in older data)
    available = [c for c in keep_cols if c in df.columns]
    df = df[available].copy()
 
    # Convert date
    df['date'] = pd.to_datetime(df['date'])
 
    # Fill NaN numerics with 0
    num_cols = [c for c in df.columns if c not in ['location', 'iso_code', 'date']]
    df[num_cols] = df[num_cols].fillna(0)
 
    # Remove rows with negative case/death counts (reporting corrections)
    df = df[df['new_cases']  >= 0]
    df = df[df['new_deaths'] >= 0]
 
    # Sort
    df = df.sort_values(['location', 'date']).reset_index(drop=True)
 
    print(f'  After cleaning  : {len(df):>10,} rows')
    print(f'  Date range      : {df["date"].min().date()} → {df["date"].max().date()}')
    return df
 
 
def save_to_sqlite(df):
    '''Persist cleaned G20 data to SQLite.'''
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
 
    df.to_sql('covid_data', conn, if_exists='replace', index=False)
 
    # Indexes for fast dashboard queries
    conn.execute('CREATE INDEX IF NOT EXISTS idx_date     ON covid_data(date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_location ON covid_data(location)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_iso      ON covid_data(iso_code)')
    conn.commit()
    conn.close()
    print(f'  Saved to        : {DB_PATH}')
 
 
def refresh_data():
    '''Full pipeline: fetch → G20 filter → clean → save.

    DISABLED: the OWID source this depends on is retired (see module docstring).
    Refuses to run instead of failing deep inside a DNS error. To restore the
    derived columns on the existing data/covid.db, run `python enrich_db.py`.
    '''
    raise RuntimeError(
        'data_fetch.refresh_data() is disabled: the OWID CSV endpoint it '
        'fetches from is retired and no longer resolves. The live data is in '
        'data/covid.db; run `python enrich_db.py` to (re)derive its columns. '
        'See this module\'s docstring before re-enabling.'
    )

    print('='*50)
    print('G20 COVID Data Refresh')
    print('='*50)
    df_raw  = fetch_owid_data()
    df_g20  = filter_g20(df_raw)
    df_clean = clean_data(df_g20)
    save_to_sqlite(df_clean)
    print(f'[DONE] Refresh complete at {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*50)
 
 
if __name__ == '__main__':
    refresh_data()
