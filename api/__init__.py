from api import caching, polygon, alpha_vantage
import pandas as pd

def tickers() -> dict:
    """Returns all tickers."""
    return caching.get('tickers', polygon.get_all_tickers, False)

def get_ticker_history(ticker: str) -> dict:
    """Gets ticker history; if not in cache, makes a one time call to alpha vantage to get full history, if it's cached check date and make necessary updates with Polygon"""
    history = caching.get(f'historical.{ticker}', alpha_vantage.get_full_ticker_history, False, ticker=ticker)

    # get the splits
    splits = get_splits(ticker)

    ### adjust history with split information

    # create dataframe from history
    df = pd.DataFrame.from_dict(history, orient='index')

    # convert index from timestamp to pd.DateTime
    df.index = pd.to_numeric(df.index)
    df.index = pd.to_datetime(df.index, unit='s')

    # for each split
    for split in splits:
        
        # get the date of the split
        date = pd.to_datetime(split.get('date'))

        # calculate the split ration; ie. a 7-for-1 split would be 1/7
        ratio = split.get('split_from') / split.get('split_to')
        
        # for all records before the date, apply the ratio
        df.loc[df.index < date, ['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].multiply(ratio).round(2)

    # sort the datetimes and convert back to integer timestamp
    df.sort_index(inplace=True)
    df.index = (df.index.astype('int64')//1000000000).astype('str')

    # convert dataframe to dictionary and return the adjusted history dict
    adjusted_history = df.to_dict(orient='index')

    return adjusted_history

def get_ticker_intraday(ticker: str) -> dict:
    """Returns data for the last five days of trading and updates historical cache with the new data."""

    intraday = caching.get(f'intraday.{ticker}', polygon.get_intraday, None, ticker=ticker)

    # append this data to alpha vantage
    caching.update(f'historical.{ticker}', intraday, alpha_vantage.get_full_ticker_history, False, ticker=ticker)

    return intraday

def get_last_close(ticker: str) -> float:
    """Returns the last closing price of the specified ticker."""

    intraday = get_ticker_intraday(ticker)
    last_item = list(intraday.keys())[-1]

    return round(intraday[last_item].get('close'), 2)

def get_watchlist() -> dict:
    """Returns user watchlist from cache."""

    # set AAPL as default ticker in the watchlist
    return caching.get('watchlist', lambda: {'AAPL': 0}, False)

def save_watchlist(watchlist: dict):
    """Updates the watchlist in cache"""

    caching.cache('watchlist', watchlist, False)

def get_splits(ticker: str) -> dict:
    """Get all splits for a specified ticker."""

    return caching.get(f'splits.{ticker}', polygon.get_splits, None, ticker=ticker)