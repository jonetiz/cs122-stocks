import requests, time
from os import getenv
from datetime import date, timedelta

API_ENDPOINT = "https://api.polygon.io"
API_KEY = getenv('POLYGON_API_KEY')

def get_all_tickers():
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
        r = requests.get(url)
        data = r.json()

        while data.get('status') == 'ERROR':
            print(f"Ticker update rate limited; currently {len(tickers)} tickers in memory. Waiting 15 seconds to continue.")
            time.sleep(15)
            r = requests.get(url)
            data = r.json()
            print(data)

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

def get_intraday(ticker):
    """Get 15 minute increments of trading data for the past five days of data"""
    r = requests.get(f"{API_ENDPOINT}/v2/aggs/ticker/{ticker}/range/15/minute/{(date.today() - timedelta(days=6)).strftime('%Y-%m-%d')}/{date.today().strftime('%Y-%m-%d')}?limit=50000&apiKey={API_KEY}")
    data = r.json()

    results = {}

    for result in data.get('results'):
        t = int(result.get('t'))
        o = result.get('o')
        h = result.get('h')
        l = result.get('l')
        c = result.get('c')
        v = result.get('v')
        results[t] = {
            'open': o,
            'high': h,
            'low': l,
            'close': c,
            'volume': v
        }
    
    return results