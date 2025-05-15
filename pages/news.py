import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash
import json
from dash import html, dcc, Input, Output, State, callback, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import re
import datetime

import api

# register page with Dash
dash.register_page(__name__, path='/news', path_template='/news/<ticker>')

# get all tickers and cached ticker watchlist
tickers = api.tickers()
watchlist = api.get_watchlist()

def generate_news_html(data):
    return html.Div([
        html.Div([
            html.H3(dcc.Link(
                (data.get('title')[:120] + '..' if len(data.get('title')) > 120 else data.get('title')),
                href=data.get('url'), 
                target='_blank')),
            html.P([f"Published {datetime.datetime.fromisoformat(data.get('time_published')).strftime('%Y-%m-%d, at %H:%M')} by {', '.join(data.get('authors'))} on ",
                    dcc.Link(f"{data.get('source')}", href=f"https://{data.get('source_domain')}", target="_blank")]),
            html.P(f"{data.get('summary')}"),
            html.B("Relevant Tickers:"),
            html.Ul(
                [html.Li(f"{item.get('ticker')} - Sentiment: {item.get('ticker_sentiment_label')}") for item in data.get('ticker_sentiment')]
            )
        ]),
        html.Img(src=data.get('banner_image'))
    ], className="news_item")

# HTML layout
def layout(ticker=None, **kwargs):
    data = api.get_news(ticker)

    return html.Div([
        dcc.Location(id='url'),
        html.P([
        dcc.Link("← Home Page", href="/"),
        " ",
        dcc.Link("All News", href="/news/")
        ]),
        *[generate_news_html(i) for i in data]
    ], className="news_page")