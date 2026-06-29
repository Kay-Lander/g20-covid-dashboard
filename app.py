import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from database import (get_country_trend, get_g20_latest_totals,
                      get_multi_country_trend, get_peak_days,
                      get_available_countries)
from constants import NAVY, ACCENT, BG, CARD, G20_COUNTRIES
 
# ── Initialize ────────────────────────────────────────────────
app    = dash.Dash(__name__, title='G20 COVID-19 Dashboard')
server = app.server   # expose Flask server for Render
 
# ── Load static data once at startup ──────────────────────────
g20_totals  = get_g20_latest_totals()
countries   = get_available_countries()
peak_days   = get_peak_days()
 
# ── Layout ────────────────────────────────────────────────────
app.layout = html.Div(
    style={'backgroundColor': BG, 'fontFamily': 'Arial, sans-serif', 'minHeight': '100vh'},
    children=[
 
    # ── Header ───────────────────────────────────────────────
    html.Div(style={'backgroundColor': NAVY, 'padding': '20px 40px',
                    'borderBottom': f'4px solid {ACCENT}'}, children=[
        html.H1('G20 COVID-19 Global Dashboard',
                style={'color': 'white', 'margin': 0, 'fontSize': '26px'}),
        html.P('Tracking COVID-19 trends across the world\'s 19 major economies | Source: Our World in Data',
               style={'color': '#AABBD4', 'margin': '4px 0 0', 'fontSize': '13px'})
    ]),
 
    # ── KPI Cards ────────────────────────────────────────────
    html.Div(style={'display': 'flex', 'gap': '16px', 'padding': '24px 40px 0'}, children=[
        html.Div(id='kpi-total-cases',  style={'flex':1, 'background': CARD, 'padding':'18px', 'borderRadius':'8px', 'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'}),
        html.Div(id='kpi-total-deaths', style={'flex':1, 'background': CARD, 'padding':'18px', 'borderRadius':'8px', 'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'}),
        html.Div(id='kpi-peak-day',     style={'flex':1, 'background': CARD, 'padding':'18px', 'borderRadius':'8px', 'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'}),
        html.Div(id='kpi-cfr',          style={'flex':1, 'background': CARD, 'padding':'18px', 'borderRadius':'8px', 'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'}),
    ]),
 
    # ── Single Country Filter ─────────────────────────────────
    html.Div(style={'padding': '20px 40px 0', 'display':'flex', 'gap':'20px', 'alignItems':'center'}, children=[
        html.Label('Country:', style={'fontWeight':'bold', 'color': NAVY}),
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': c, 'value': c} for c in countries],
            value='United States',
            clearable=False,
            style={'width': '260px'}
        ),
        html.Label('Date Range:', style={'fontWeight':'bold', 'color': NAVY, 'marginLeft':'20px'}),
        dcc.DatePickerRange(
            id='date-range',
            start_date='2021-01-01',
            end_date='2023-03-01',
            display_format='MMM DD, YYYY'
        )
    ]),
 
    # ── Time Series Chart ─────────────────────────────────────
    html.Div(style={'padding': '20px 40px 0'}, children=[
        dcc.Graph(id='timeseries',
                  style={'background': CARD, 'borderRadius':'8px',
                         'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'})
    ]),
 
    # ── World Map + Rankings ──────────────────────────────────
    html.Div(style={'display':'flex', 'gap':'16px', 'padding':'16px 40px 0'}, children=[
        dcc.Graph(id='world-map',
                  style={'flex':2, 'background': CARD, 'borderRadius':'8px',
                         'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'}),
        dcc.Graph(id='ranking-bar',
                  style={'flex':1, 'background': CARD, 'borderRadius':'8px',
                         'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'}),
    ]),
 
    # ── Multi-Country Comparison ──────────────────────────────
    html.Div(style={'padding': '16px 40px 0'}, children=[
        html.Label('Compare G20 Countries (30-Day Average):',
                   style={'fontWeight':'bold', 'color': NAVY, 'padding':'0 0 8px'}),
        dcc.Dropdown(
            id='multi-country-dropdown',
            options=[{'label': c, 'value': c} for c in countries],
            value=['United States', 'India', 'Brazil', 'Germany', 'United Kingdom'],
            multi=True,
            style={'marginBottom': '12px'}
        ),
        dcc.Graph(id='multi-country-chart',
                  style={'background': CARD, 'borderRadius':'8px',
                         'boxShadow':'0 2px 6px rgba(0,0,0,0.07)'})
    ]),
 
    html.Div(style={'height': '40px'})
])
# ── Callback 1: KPI Cards + Time Series ──────────────────────
@app.callback(
    Output('kpi-total-cases',  'children'),
    Output('kpi-total-deaths', 'children'),
    Output('kpi-peak-day',     'children'),
    Output('kpi-cfr',          'children'),
    Output('timeseries',       'figure'),
    Input('country-dropdown',  'value'),
    Input('date-range',        'start_date'),
    Input('date-range',        'end_date'),
)
def update_country_view(country, start_date, end_date):
    df = get_country_trend(country)

    # Date filter — guard against None (cleared DatePickerRange fields)
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
 
    # KPI values
    total_cases  = df['new_cases'].sum()
    total_deaths = df['new_deaths'].sum() if 'new_deaths' in df.columns else 0
    cfr_row      = g20_totals[g20_totals['location'] == country]
    cfr          = cfr_row['cfr_pct'].values[0] if len(cfr_row) else 0
    peak_row     = peak_days[peak_days['location'] == country]
    peak_cases   = int(peak_row['peak_cases'].values[0]) if len(peak_row) else 0
    peak_date    = peak_row['peak_date'].values[0] if len(peak_row) else ''
    if hasattr(peak_date, 'strftime'):
        peak_date = peak_date.strftime('%b %d, %Y')
 
    def kpi(label, value, sub='', color=NAVY):
        return [
            html.P(label,  style={'color': ACCENT, 'fontWeight':'bold', 'margin':'0 0 4px', 'fontSize':'12px'}),
            html.H2(value, style={'color': color,  'margin':'0', 'fontSize':'26px'}),
            html.P(sub,    style={'color':'#888',  'margin':'4px 0 0', 'fontSize':'12px'}),
        ]
 
    # Time series figure
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['date'], y=df['new_cases'],
        name='Daily Cases', marker_color='#AABBD4', opacity=0.5
    ))
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['rolling_7day'],
        name='7-Day Average',
        line=dict(color=NAVY, width=2.5)
    ))
    fig.update_layout(
        title=dict(text=f'{country} — Daily New Cases', font=dict(size=15, color=NAVY)),
        xaxis_title='Date', yaxis_title='New Cases',
        legend=dict(orientation='h', y=1.08),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=40, r=20, t=60, b=40),
        hovermode='x unified'
    )
 
    return (
        kpi('CASES IN RANGE',  f"{total_cases:,.0f}"),
        kpi('DEATHS IN RANGE', f"{total_deaths:,.0f}"),
        kpi('PEAK DAY',        f"{peak_cases:,}", str(peak_date)),
        kpi('CASE FATALITY RATE', f"{cfr:.2f}%",
            'deaths / confirmed cases'),
        fig
    )
 
 
# ── Callback 2: World Map ─────────────────────────────────────
@app.callback(
    Output('world-map',   'figure'),
    Output('ranking-bar', 'figure'),
    Input('country-dropdown', 'value'),   # re-render on any interaction
)
def update_map_and_bar(_):
    # World choropleth — G20 countries colored by total cases
    map_fig = px.choropleth(
        g20_totals,
        locations='iso_code',
        color='total_cases',
        hover_name='location',
        hover_data={'total_deaths': True, 'cfr_pct': True, 'iso_code': False},
        color_continuous_scale='Blues',
        title='G20 — Total Cases by Country',
        labels={'total_cases': 'Total Cases', 'cfr_pct': 'CFR (%)'}
    )
    map_fig.update_layout(
        title=dict(font=dict(size=14, color=NAVY)),
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='white',
        geo=dict(showframe=False, showcoastlines=True, projection_type='natural earth')
    )
 
    # Bar chart — top G20 countries ranked
    top = g20_totals.head(10).sort_values('total_cases')
    bar_fig = go.Figure(go.Bar(
        x=top['total_cases'], y=top['location'],
        orientation='h', marker_color=ACCENT,
        text=top['total_cases'].apply(lambda x: f'{x/1e6:.1f}M'),
        textposition='outside'
    ))
    bar_fig.update_layout(
        title=dict(text='G20 Rankings — Total Cases', font=dict(size=14, color=NAVY)),
        xaxis_title='Total Cases',
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=10, r=60, t=50, b=40)
    )
 
    return map_fig, bar_fig
 
 
# ── Callback 3: Multi-Country Comparison ─────────────────────
@app.callback(
    Output('multi-country-chart', 'figure'),
    Input('multi-country-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
)
def update_multi_country(selected_countries, start_date, end_date):
    if not selected_countries:
        return go.Figure()
 
    df = get_multi_country_trend(selected_countries)

    # Date filter — guard against None (cleared DatePickerRange fields)
    if start_date:
        df = df[df['date'] >= start_date]
    if end_date:
        df = df[df['date'] <= end_date]
 
    fig = go.Figure()
    for country in selected_countries:
        cdf = df[df['location'] == country]
        fig.add_trace(go.Scatter(
            x=cdf['date'], y=cdf['rolling_30day'],
            name=country, mode='lines', line=dict(width=2)
        ))
 
    fig.update_layout(
        title=dict(text='G20 Country Comparison — 30-Day Average New Cases',
                   font=dict(size=15, color=NAVY)),
        xaxis_title='Date', yaxis_title='30-Day Avg New Cases',
        legend=dict(orientation='h', y=-0.15),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=40, r=20, t=60, b=60),
        hovermode='x unified'
    )
    return fig
 
 
# ── Run ───────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
