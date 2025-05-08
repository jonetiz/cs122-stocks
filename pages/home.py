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

dash.register_page(__name__, path='/')

tickers = api.tickers()

watchlist = api.get_watchlist()

layout = html.Div([
    html.Div([
        html.H3("SimpleStocks"),
        dcc.Tabs([
            dcc.Tab(label="5D", id="graphtab_5d"),
            dcc.Tab(label="1M", id="graphtab_1m"),
            dcc.Tab(label="6M", id="graphtab_6m"),
            dcc.Tab(label="YTD", id="graphtab_ytd"),
            dcc.Tab(label="1Y", id="graphtab_1y"),
            dcc.Tab(label="5Y", id="graphtab_5y"),
            dcc.Tab(label="Max", id="graphtab_max"),
        ])
    ], className="left_panel"),
    html.Div([
        html.H3("Ticker Watchlist"),
        html.Div([dcc.Dropdown(id="ticker_search"), dbc.Button("Add", color="primary", id="add_ticker_btn")], id="options", className="controlBar"),
        dcc.Loading([
            html.Table([
                html.Thead([html.Tr([html.Th("Ticker"), html.Th("Last Close"), html.Th("Options")])]),
                html.Tbody([], id="watchlist_items")
            ])
        ])
    ], className="right_panel")
], className="home_page")

@callback(
    Output("ticker_search", "options"),
    Input("ticker_search", "search_value")
)
def update_ticker_search(search_value):
    if not search_value:
        raise PreventUpdate
    
    results = []
    if len(search_value) == 1:
        # simplify search by directly indexing if searching a single letter; also prevents actual search unless query is greater than 1 character 
        name = tickers.get(search_value)
        if name:
            results.append({'label': f"{search_value} | {name}", 'value': search_value})
        return results

    for ticker, name in tickers.items():
        regex = rf'.*{search_value}.*'

        if re.search(regex, str(ticker), re.IGNORECASE) or re.search(regex, str(name), re.IGNORECASE):
            results.append({'label': f"{ticker} | {name}", 'value': ticker})

    return results

@callback(
    Output('watchlist_items', 'children'),
    [
        Input('add_ticker_btn', 'n_clicks'),
        Input({'type': 'remove_watchlist_item', 'index': ALL}, "n_clicks")
    ],
    State('ticker_search', 'value')
)
def update_watchlist(n_clicks, _, ticker):
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if "index" in input_id:
        delete_item = json.loads(input_id)["index"]
        del watchlist[delete_item]
    elif "add_ticker_btn" in input_id:
        hist = api.get_ticker_history(ticker)
        last_close = hist[list(hist)[0]].get('close')
        watchlist[ticker] = last_close

    api.save_watchlist(watchlist)

    return [
        html.Tr(
            [
                html.Td(f"{item} | {tickers[item]}"),
                html.Td(f"${watchlist[item]}"),
                dbc.Button("Show", color="secondary", id={"type": "show_watchlist_item", "index": item}),
                dbc.Button("Remove", color="danger", id={"type": "remove_watchlist_item", "index": item})
            ],
            id={"type": "watchlist_item", "index": item})
            for item in watchlist
        ]

@callback(
    [   
        Output('graphtab_5d', 'children'),
        Output('graphtab_1m', 'children'),
        Output('graphtab_6m', 'children'),
        Output('graphtab_ytd', 'children'),
        Output('graphtab_1y', 'children'),
        Output('graphtab_5y', 'children'),
        Output('graphtab_max', 'children')
    ],
    Input({'type': 'show_watchlist_item', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def show_watchlist_item(n_clicks):
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    ticker = json.loads(input_id).get('index')

    history = api.get_ticker_history(ticker)

    history_df = pd.DataFrame.from_dict(history, orient='index', dtype=float)
    history_df.index = pd.to_datetime(history_df.index, unit='s')

    intraday = api.get_ticker_intraday(ticker)
    df_5d = pd.DataFrame.from_dict(intraday, orient='index', dtype=float)
    df_5d.index = pd.to_datetime(df_5d.index, unit='ms')

    history_df_1m = history_df[history_df.index > (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')]
    history_df_6m = history_df[history_df.index > (datetime.date.today() - datetime.timedelta(weeks=26)).strftime('%Y-%m-%d')]
    history_df_ytd = history_df[history_df.index > (datetime.date.today().replace(month=1, day=1)).strftime('%Y-%m-%d')]
    history_df_1y = history_df[history_df.index > (datetime.date.today() - datetime.timedelta(weeks=52)).strftime('%Y-%m-%d')]
    history_df_5y = history_df[history_df.index > (datetime.date.today() - datetime.timedelta(weeks=260)).strftime('%Y-%m-%d')]

    labels = {
        'date': 'Date',
        'time': 'Time',
        'value': 'Price'
    }

    def intraday_graph(df, title):
        mod_df = pd.melt(df.reset_index().rename(columns={'index':'time'}).drop(columns=['volume']), id_vars='time')
        first = df[df.index == df.index.min()]
        last = df[df.index == df.index.max()]
        up: bool = float(last['close']) > float(first['close'])
        fig = px.line(df, y='close', color_discrete_sequence=["green" if up else "red"],
                      labels=labels, title=title)
        
        # TODO: skip weekends

        return fig

    def line_graph(df, title):
        fig = px.line(mod_df, x='date', y='value', color='variable', color_discrete_sequence=["grey", "green", "red", "blue"],
                      labels=labels, title=title)
        return fig

    def ohlc_graph(df, title):
        fig = go.Figure(data=[go.Ohlc(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])

        fig.update_layout(title=dict(text=title), xaxis=dict(title=dict(text="Date")), yaxis=dict(title=dict(text="Price")))

        return fig

    def statistics(df, title, graph_func):
        graph = graph_func(df, title)

        return html.Div([
            dcc.Graph(figure=graph),
            html.Table([
                html.Tr([
                    html.Th("Open"), html.Td(df[df.index == df.index.min()]['open']), html.Th("Volume Traded"), html.Td(df['volume'].sum()), html.Th(""), html.Td([dcc.Link("News", href=f"https://finance.yahoo.com/quote/{ticker}/news/", target="blank")])
                ]),
                html.Tr([
                    html.Th("High"), html.Td(df['high'].max()), html.Th("Average Close"), html.Td(round(df['close'].mean(), 2))
                ]),
                html.Tr([
                    html.Th("Low"), html.Td(df['low'].min()), html.Th("52 week Average Close"), html.Td(round(history_df_1y['close'].mean(), 2))
                ]),
            ])
            ])


    return (
        statistics(df_5d, f"{ticker} 5 day Market Summary", intraday_graph),
        statistics(history_df_1m, f"{ticker} 30 day Market Summary", line_graph),
        statistics(history_df_6m, f"{ticker} 6 month Market Summary", line_graph),
        statistics(history_df_ytd, f"{ticker} YTD Market Summary", line_graph),
        statistics(history_df_1y, f"{ticker} 52 week Market Summary", line_graph),
        statistics(history_df_5y, f"{ticker} 5 year Market Summary", line_graph),
        statistics(history_df, f"{ticker} Market History", ohlc_graph)
    )