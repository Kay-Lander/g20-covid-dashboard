"""
One-time enrichment for data/covid.db.

The working database (data/covid.db) holds all 19 G20 countries and the full
2020-2024 date range, but is missing three columns the dashboard needs:

    iso_code            - static ISO alpha-3 code per country (for the choropleth)
    new_cases_smoothed  - 7-day rolling average of new_cases (per country)
    population          - static population per country (for CFR / per-capita)

The original OWID CSV endpoint that once supplied these is retired, so we
backfill them here from constants + a static population lookup + a computed
rolling average. Safe to re-run: it recomputes and overwrites the columns.

Run once:  python enrich_db.py
"""
import sqlite3
import pandas as pd
from constants import DB_PATH, G20_COUNTRIES, G20_ISO_CODES

# location -> iso_code, built from the constants that are already kept in sync
ISO_BY_LOCATION = dict(zip(G20_COUNTRIES, G20_ISO_CODES))

# Static population per G20 country (~2021 figures, used for CFR/per-capita).
POPULATION = {
    'Argentina':       45_276_780,
    'Australia':       25_788_220,
    'Brazil':         213_993_440,
    'Canada':          38_067_900,
    'China':        1_425_893_470,
    'France':          67_564_250,
    'Germany':         83_900_470,
    'India':        1_407_563_840,
    'Indonesia':      273_753_190,
    'Italy':           59_240_330,
    'Japan':          125_681_590,
    'Mexico':         126_705_140,
    'Russia':         145_912_020,
    'Saudi Arabia':    35_950_400,
    'South Africa':    59_392_260,
    'South Korea':     51_830_140,
    'Turkey':          84_775_400,
    'United Kingdom':  67_281_040,
    'United States':  336_997_620,
}


def enrich():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        'SELECT * FROM covid_data', conn, parse_dates=['date']
    )
    df = df.sort_values(['location', 'date']).reset_index(drop=True)

    # Static lookups
    df['iso_code']   = df['location'].map(ISO_BY_LOCATION)
    df['population'] = df['location'].map(POPULATION)

    # 7-day rolling average of new_cases, computed per country
    df['new_cases_smoothed'] = (
        df.groupby('location')['new_cases']
          .transform(lambda s: s.rolling(window=7, min_periods=1).mean())
          .round(1)
    )

    # Fail loud if any country is missing a static value
    missing_iso = df[df['iso_code'].isna()]['location'].unique()
    missing_pop = df[df['population'].isna()]['location'].unique()
    if len(missing_iso):
        raise ValueError(f'Missing iso_code for: {missing_iso}')
    if len(missing_pop):
        raise ValueError(f'Missing population for: {missing_pop}')

    # Overwrite the table with the enriched frame, then rebuild indexes
    df.to_sql('covid_data', conn, if_exists='replace', index=False)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_date     ON covid_data(date)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_location ON covid_data(location)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_iso      ON covid_data(iso_code)')
    conn.commit()

    cols = [d[1] for d in conn.execute('PRAGMA table_info(covid_data)').fetchall()]
    n    = conn.execute('SELECT COUNT(*) FROM covid_data').fetchone()[0]
    conn.close()

    print(f'Enriched {DB_PATH}: {n:,} rows')
    print(f'Columns: {cols}')


if __name__ == '__main__':
    enrich()
