# SimpleStocks
By Jonathan Etiz for CS 122 at San Jose State University

## Description
**SimpleStocks** is an open-source, easy-to-use interface for investors to track their current and historical positions on the stock market. This program is a simple web interface that uses the [**Alpha Vantage API**](https://www.alphavantage.co/documentation/) and [**Polygon API**](https://polygon.io/docs/rest/quickstart) to fetch and display historical time series data on stock positions. Due to the vast nature of market data, the program uses a passive caching technique where tracked stocks are updated and cached real-time in the background without any necessary user input. It is meant to serve as an easy way for investors to track positions of specific stocks or indexes, along with additional tooling to help inform investment decisions.

## Features (non-exclusive)
- Robust user interface with a focus on simplicity
- Add specific stocks to track
- Get news from multiple sources on tracked stocks
- **Simple moving average** analysis for varied time periods

## Interface Plan
SimpleStocks is served as a single-page application, with no bloated or unnecessary features to make the experience as user-friendly and seamless as possible. The main interface includes an adjustable time series graph for specified stocks, along with a list of the stocks to be tracked.

The application is served by [Plotly Dash](https://dash.plotly.com/), a Python framework for building interactive and data-driven web applications.

## Data Collection and Storage
The data is sourced from the [**Alpha Vantage API**](https://www.alphavantage.co/documentation/) and [**Polygon API**](https://polygon.io/docs/rest/quickstart) and all requests are cached in order to reduce API limits, as the free tier of Alpha Vantage has 25 requests per day, and Polygon limits users to 5 requests per minute.

Both APIs are used for the following:
- Alpha Vantage
  - Retrieve full historical OHLC data (Polygon limits to 2 years history for free tier)
  - Get news feed
- Polygon
  - Retrieve recent trading data (which updates cached alpha vantage data)
  - Retrieve list of all tickers
  - Retrieve stock split data

## Data Analysis and Visualization
The data is visualized primarily as time-series data to provide users with insight on market.

## File Structure
```
./
│   ├─ cache/           # Cached requests
│   ├─ __init__.py      # All API methods are called from here
│   ├─ alpha_vantage.py # Alpha Vantage API methods
│   ├─ caching.py       # Internal caching library
│   └─ polygon.py       # Polygon API methods
│
├─ assets/              # Static assets
│   └─ stylesheet.css
│
├─ pages/               # Plotly dash pages
│   └─ home.py          # The main page
│
├─ .env                 # Environment variables (to be created by user)
├─ .gitignore
├─ app.py               # Main program file
├─ LICENSE
├─ README.md            # You are here!
└─ requirements.txt
```

## Setup
### Prerequisites
- Python > 3.10

Start by installing the requirements with the following command:
```
pip install -r requirements.txt
```

Create a file in the root directory named `.env` and place the following contents:
```
POLYGON_API_KEY = get_free_from_polygon_website
ALPHA_VANTAGE_API_KEY = get_free_from_alpha_vantage_website
```

To run the project, run the command:
```
python app.py
```