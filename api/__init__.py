from os import getenv
from api import caching, polygon, alpha_vantage

def tickers():
    """Returns all tickers."""
    return caching.get('tickers', polygon.get_all_tickers, False)

def get_ticker_history(ticker):
    """Gets ticker history; if not in cache, makes a one time call to alpha vantage to get full history, if it's cached check date and make necessary updates with Polygon"""
    history = caching.get(f'historical.{ticker}', alpha_vantage.get_full_ticker_history, False, ticker=ticker)
    
    # TODO: update cache with polygon data

    return history

def get_ticker_intraday(ticker):
    return caching.get(f'intraday.{ticker}', polygon.get_intraday, None, ticker=ticker)

def get_watchlist():
    return caching.get('watchlist', lambda: {}, False)

def save_watchlist(watchlist: dict):
    caching.cache('watchlist', watchlist, False)