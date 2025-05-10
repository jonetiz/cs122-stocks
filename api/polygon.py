import requests, time
from os import getenv
from datetime import date, timedelta

API_ENDPOINT = "https://api.polygon.io"
API_KEY = getenv('POLYGON_API_KEY')

# documentation: https://polygon.io/docs/rest/stocks/tickers/all-tickers
def get_all_tickers() -> dict:
    """Gets all tickers for all stocks traded on NYSE and returns a dictionary with the format:
    ```
    {
        'ticker': 'Company Name'
    }
    ```

    NOTE: Polygon limits free API requests to 5 per minute, and this takes 8 API requests to complete, so it will hit the cap and regulates the rate limiting.
    """
    print("Reloading ticker cache")

    tickers = {}

    def get_ticker_chunk(url):
        """Appends data on this request page to the tickers dictionary, returns the next_url cursor."""
        
        # make the request
        r = requests.get(url)
        data = r.json()

        # while we are waiting on API request, keep trying the request
        wait_count = 0
        while data.get('status') == 'ERROR':
            print(f"Ticker update rate limited; currently {len(tickers)} tickers in memory. Waiting 15 seconds to continue.")
            
            # wait 15 seconds
            time.sleep(15)

            # retry request
            r = requests.get(url)
            data = r.json()
            wait_count += 1

            # if we've waited 1m 30s, throw an error as this error is likely not api timeout
            if wait_count >= 6:
                raise Exception(f"Polygon API throwing error with data: {data}")

        # set the data in tickers dictionary
        for ticker in data.get('results'):
            tickers[ticker.get('ticker')] = ticker.get('name')

        # returns URL with API key if next url is set
        if data.get('next_url'):
            return data.get('next_url') + '&apiKey=' + API_KEY
        

    print("Retrieving NYSE tickers.")
    # search NYSE
    url = get_ticker_chunk(f"{API_ENDPOINT}/v3/reference/tickers?market=stocks&exchange=XNYS&limit=1000&apiKey={API_KEY}")
    
    # loop through all pages
    while url:
        url = get_ticker_chunk(url)

    print("Retrieving NASDAQ tickers.")
    # search NASDAQ next
    url = get_ticker_chunk(f"{API_ENDPOINT}v3/reference/tickers?market=stocks&exchange=XNAS&limit=1000&apiKey={API_KEY}")
    
    # loop through all pages
    while url:
        url = get_ticker_chunk(url)

    return tickers

# documentation: https://polygon.io/docs/rest/stocks/aggregates/custom-bars
def get_intraday(ticker: str) -> dict:
    """Get 15 minute increments of trading data for the past five days of data"""

    # make the request
    r = requests.get(f"{API_ENDPOINT}/v2/aggs/ticker/{ticker}/range/15/minute/{(date.today() - timedelta(days=6)).strftime('%Y-%m-%d')}/{date.today().strftime('%Y-%m-%d')}?limit=50000&apiKey={API_KEY}")
    data = r.json()

    results = {}

    # normalize data so it is same format as alpha vantage
    for result in data.get('results'):

        # reduce timestamp from milliseconds to seconds
        t = int(result.get('t')//1000)

        # open, high, low, close, volume
        o = result.get('o')
        h = result.get('h')
        l = result.get('l')
        c = result.get('c')
        v = result.get('v')

        results[t] = {
            'open': round(o, 2),
            'high': round(h, 2),
            'low': round(l, 2),
            'close': round(c, 2),
            'volume': int(v)
        }
    
    return results

# documentation: https://polygon.io/docs/rest/stocks/corporate-actions/splits
def get_splits(ticker):
    """Get stock split history for the specified ticker"""

    # make the request
    r = requests.get(f"{API_ENDPOINT}/v3/reference/splits?ticker={ticker}&limit=1000&apiKey={API_KEY}")
    data = r.json()

    results = []

    # only use the data we need (date, from, and to)
    for result in data.get('results'):
        date = result.get('execution_date')
        split_from = result.get('split_from')
        split_to = result.get('split_to')
        results.append({'date': date, 'split_from': split_from, 'split_to': split_to})
    
    return results