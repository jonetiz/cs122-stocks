# SimpleStocks
By Jonathan Etiz

## Description
**SimpleStocks** is an open-source, easy-to-use interface for investors to track their current and historical positions on the stock market. This program is a simple web interface that uses the [**Alpha Vantage API**](https://www.alphavantage.co/documentation/) to fetch and display real-time time series data on any stock positions. Due to the vast nature of market data, the program uses a passive caching technique where tracked stocks are updated and cached real-time in the background without any necessary user input. It is meant to serve as an easy way for investors to track positions of specific stocks or indexes, along with additional tooling to help inform investment decisions.

## Features (non-exclusive)
- Robust user interface with a focus on simplicity
- Add specific stocks or indexes to track
- **Volatile stocks list** showing stocks and indexes that are the most volatile/have the most change over a user-specified period of time
- **Machine learning predictions** on where future positions may be (note: the market is by nature very volatile and these predictions are not to be used as a sole source of investment advice).

## Interface Plan
SimpleStocks is served as a single-page application, with no bloated or unnecessary features to make the experience as user-friendly and seamless as possible. The main interface includes an adjustable time series graph for specified stocks and indexes, along with a list of the stocks to be tracked, and a selection of lists that users can choose to include, such as volatile stocks, stable stocks, and machine-learning suggested stocks.

## Data Collection and Storage
The data is sourced from the [**Alpha Vantage API**](https://www.alphavantage.co/documentation/) and older data is cached in JSON format up to a period of time the user may specify in intervals the user specifies (ie. the user can choose to store data for up to 7 days away updated at 1 minute intervals, or 30 days away updated hourly).

## Data Analysis and Visualization
The data is visualized primarily as time-series data, and will have machine-learning analysis integrated to provide users with predictions on market (note: the market is by nature very volatile and these predictions are not to be used as a sole source of investment advice).
