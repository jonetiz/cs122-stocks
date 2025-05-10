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
dash.register_page(__name__, path='/')

# get all tickers and cached ticker watchlist
tickers = api.tickers()
watchlist = api.get_watchlist()

# HTML layout
layout = html.Div([
    # left side panel
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

    # watchlist / right side panel
    html.Div([
        html.H3("Ticker Watchlist"),
        html.Div([dcc.Dropdown(id="ticker_search"), dbc.Button(
            "Add", color="primary", id="add_ticker_btn")], id="options", className="controlBar"),
        dcc.Loading([
            html.Table([
                html.Thead(
                    [html.Tr([html.Th("Ticker"), html.Th("Last Close"), html.Th("Options")])]),
                html.Tbody([], id="watchlist_items")
            ])
        ])
    ], className="right_panel")
], className="home_page")

# when ticker search value is updated, update options with this function
@callback(
    Output("ticker_search", "options"),
    Input("ticker_search", "search_value")
)
def update_ticker_search(search_value: str) -> list:
    """Update ticker search dropdown options based on search value"""

    # don't update if there's no search value (prevents clientside errrorr)
    if not search_value:
        raise PreventUpdate

    results = []

    if len(search_value) <= 2:
        
        # no regex here so we need uppercase
        search_value = search_value.upper()

        # if the ticker is 1 or 2 letters, only return if there's a direct match
        name = tickers.get(search_value)
        if name:
            results.append(
                {'label': f"{search_value} | {name}", 'value': search_value})
            
        return results
    
    for ticker, name in tickers.items():

        # regex search ticker and company name, then add all results to results
        regex = rf'.*{search_value}.*'

        if re.search(regex, str(ticker), re.IGNORECASE) or re.search(regex, str(name), re.IGNORECASE):
            results.append({'label': f"{ticker} | {name}", 'value': ticker})

    return results

# when add to watchlist button or remove from watchlist button are clicked, run this function; also ran on page load
@callback(
    Output('watchlist_items', 'children'),
    [
        Input('add_ticker_btn', 'n_clicks'),
        Input({'type': 'remove_watchlist_item', 'index': ALL}, "n_clicks")
    ],
    State('ticker_search', 'value')
)
def update_watchlist(n_clicks, _, ticker):
    """Handles addition and deletion from the watchlist"""

    # get the DOM ID of the instantiating button
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

    if "index" in input_id:

        # delete item from watchlist
        delete_item = json.loads(input_id)["index"]
        del watchlist[delete_item]

    elif "add_ticker_btn" in input_id:
        
        # add item to watchlist; last close will be set in next step, so set to 0
        watchlist[ticker] = 0

    for ticker in watchlist:

        # update all tickers on the watchlist
        watchlist[ticker] = api.get_last_close(ticker)

    # save the watchlist back to cache after updated
    api.save_watchlist(watchlist)

    # return each watchlist item to the watchlist table
    return [
        html.Tr(
            [
                html.Td(f"{item} | {tickers[item]}"),
                html.Td(f"${watchlist[item]}"),
                dbc.Button("Show", color="secondary", id={
                           "type": "show_watchlist_item", "index": item}),
                dbc.Button("Remove", color="danger", id={
                           "type": "remove_watchlist_item", "index": item})
            ],
            id={"type": "watchlist_item", "index": item})
        for item in watchlist
    ]


# when the "Show" button is pressed, update the graph tabs (left side panel); also ran on page start
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
    """Logic for generating and displaying the graph tabs"""

    # do not update if watchlist is 0 to prevent clientside error
    if len(watchlist) == 0:
        raise PreventUpdate
    
    # get ticker of pressed button
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    ticker = json.loads(input_id).get('index')

    # get history and load to dataframe
    history = api.get_ticker_history(ticker)
    history_df = pd.DataFrame.from_dict(history, orient='index', dtype=float)
    history_df.index = pd.to_numeric(history_df.index)
    history_df.index = pd.to_datetime(history_df.index, unit='s')

    # get intraday data and load to dataframe
    intraday = api.get_ticker_intraday(ticker)
    df_5d = pd.DataFrame.from_dict(intraday, orient='index', dtype=float)
    df_5d.index = pd.to_numeric(df_5d.index)
    df_5d.index = pd.to_datetime(df_5d.index, unit='s')

    # create dataframes for the different timespans
    history_df_1m = history_df[history_df.index > (
        datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')]
    history_df_6m = history_df[history_df.index > (
        datetime.date.today() - datetime.timedelta(weeks=26)).strftime('%Y-%m-%d')]
    history_df_ytd = history_df[history_df.index > (
        datetime.date.today().replace(month=1, day=1)).strftime('%Y-%m-%d')]
    history_df_1y = history_df[history_df.index > (
        datetime.date.today() - datetime.timedelta(weeks=52)).strftime('%Y-%m-%d')]
    history_df_5y = history_df[history_df.index > (
        datetime.date.today() - datetime.timedelta(weeks=260)).strftime('%Y-%m-%d')]

    # graph labels
    labels = {
        'date': 'Date',
        'value': 'Price'
    }

    # creates the intraday graph
    def intraday_graph(df, title):

        # calculate whether this stock up or down since the start of the period
        first = df[df.index == df.index.min()]
        last = df[df.index == df.index.max()]
        up: bool = float(last['close'].iloc[0]) > float(first['close'].iloc[0])

        # https://plotly.com/python/graph-objects/
        fig = go.Figure(data=[
            go.Scatter(x=df.index, y=df['close'], line=dict(color='green' if up else 'red'), name="Closing Price"),
            go.Scatter(x=df.index, y=df['sma'], line=dict(color='blue'), name="3-day SMA")
        ])

        # get missing days
        alldays = set(df.index[0] + datetime.timedelta(x) for x in range((df.index[len(df.index)-1] - df.index[0]).days))
        missing = sorted(set(alldays)-set(df.index))

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Closing Price",
            # don't show missing data (weekends)
            xaxis=dict(
                rangebreaks=[
                    dict(bounds=[0,8], pattern="hour"), # there is no data between 12a-8a
                    dict(values=missing), # Hide weekends
                ]
            ),
            hovermode='x unified'
        )

        return fig

    # creates graphs for all except 5d and max
    def line_graph(df, title):
        
        # melt df so to make graphing OHLC values much easiere
        mod_df = pd.melt(df.reset_index().rename(
            columns={'index': 'date'}).drop(columns=['volume']), id_vars='date')
        
        # graph the values
        fig = px.line(mod_df, x='date', y='value', color='variable', color_discrete_sequence=["grey", "green", "red", "blue", "orange"],
                      labels=labels, title=title)

        fig.update_layout(
            hovermode='x unified',
            # xaxis=dict(
            #     rangebreaks=[
            #         # dict(bounds=[0,8], pattern="hour"),
            #         # dict(values=missing),  # Hide weekends
            #     ]
            # )
        )

        return fig

    # creates OHLC graph used in full history graph
    def ohlc_graph(df, title):
        
        # https://plotly.com/python/ohlc-charts/ 
        fig = go.Figure(data=[go.Ohlc(
            x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
        
        fig.update_layout(title=dict(text=title), xaxis=dict(title=dict(text="Date"), rangeslider=dict(
            visible=False)), yaxis=dict(title=dict(text="Price")), hovermode='x unified')

        return fig

    # generates the HTML layout for each graph
    def statistics(df, title, graph_func, sma_window=None):
        
        # calculate SMA if set
        if sma_window:
            df.loc[:, 'sma'] = df['close'].rolling(sma_window).mean()

        # run the graph function
        graph = graph_func(df, title)

        # return the generated HTML
        return html.Div([
            dcc.Graph(figure=graph),
            html.Table([
                html.Tr([
                    html.Th("Open"), html.Td(df[df.index == df.index.min()]['open']), html.Th("Volume Traded"), html.Td(df['volume'].sum(
                    )), html.Th(""), html.Td([dcc.Link("News", href=f"https://finance.yahoo.com/quote/{ticker}/news/", target="blank")])
                ]),
                html.Tr([
                    html.Th("High"), html.Td(df['high'].max()), html.Th(
                        "Average Close"), html.Td(round(df['close'].mean(), 2))
                ]),
                html.Tr([
                    html.Th("Low"), html.Td(df['low'].min()), html.Th(
                        "52 week Average Close"), html.Td(round(history_df_1y['close'].mean(), 2))
                ]),
            ])
        ])

    # return generated HTML
    return (
        statistics(df_5d, f"{ticker} 5 day Market Summary", intraday_graph, '3d'),
        statistics(history_df_1m,
                   f"{ticker} 30 day Market Summary", line_graph, '10d'),
        statistics(history_df_6m,
                   f"{ticker} 6 month Market Summary", line_graph, '50d'),
        statistics(history_df_ytd, f"{ticker} YTD Market Summary", line_graph),
        statistics(history_df_1y,
                   f"{ticker} 52 week Market Summary", line_graph, '100d'),
        statistics(history_df_5y,
                   f"{ticker} 5 year Market Summary", line_graph, '365d'),
        statistics(history_df, f"{ticker} Market History", ohlc_graph)
    )
