import requests
from datetime import datetime
from os import getenv

API_ENDPOINT = 'https://www.alphavantage.co/query?'
API_KEY = getenv('ALPHA_VANTAGE_API_KEY')

# Alpha Vantage has a 25-per-day limit on API calls (for free use), so these are used sparingly.

def get_full_ticker_history(ticker):
    """Retrieves the ticker's full history; """
    url = f"{API_ENDPOINT}function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={API_KEY}"
    request = requests.get(url)
    data = request.json()

    history = {}

    # shave and normalize data
    timeseries_data = data.get('Time Series (Daily)')
    try:
        for date in timeseries_data:
            timestamp = int(datetime.strptime(date, '%Y-%m-%d').timestamp())
            data_dict = timeseries_data[date]
            history[timestamp] = {
                'open': float(data_dict.get('1. open')),
                'high': float(data_dict.get('2. high')),
                'low': float(data_dict.get('3. low')),
                'close': float(data_dict.get('4. close')),
                'volume': float(data_dict.get('5. volume')),
            }
    except Exception as e:
        print(e)
        return None

    return history