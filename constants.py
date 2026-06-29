# constants.py
# Single source of truth for G20 country list and app config
 
G20_COUNTRIES = [
    'Argentina', 'Australia', 'Brazil',        'Canada',
    'China',     'France',    'Germany',        'India',
    'Indonesia', 'Italy',     'Japan',           'Mexico',
    'Russia',    'Saudi Arabia', 'South Africa', 'South Korea',
    'Turkey',    'United Kingdom', 'United States'
]
 
# ISO alpha-3 codes for Plotly choropleth map
# Must match OWID's 'iso_code' column exactly
G20_ISO_CODES = [
    'ARG', 'AUS', 'BRA', 'CAN', 'CHN', 'FRA', 'DEU', 'IND',
    'IDN', 'ITA', 'JPN', 'MEX', 'RUS', 'SAU', 'ZAF', 'KOR',
    'TUR', 'GBR', 'USA'
]
 
DB_PATH    = 'data/covid.db'
OWID_URL   = 'https://covid.ourworldindata.org/data/owid-covid-data.csv'
 
# Dashboard color scheme
NAVY   = '#1B3A6B'
ACCENT = '#2E75B6'
BG     = '#F8FAFD'
CARD   = '#FFFFFF'
