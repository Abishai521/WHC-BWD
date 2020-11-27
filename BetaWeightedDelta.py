from datetime import datetime
import statsmodels.api as sm
import streamlit as st
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from pandas_datareader import data as pdr
from statsmodels import regression

ts = TimeSeries(key='JM4MU7FUTY9MN6VK', output_format='pandas')
#client_id = 'NCRJQTMSAW3PLXYMZXOTA6DAL2LUZLRW'

st.write("""
# Winter Haven Capital
Democratization of Retail Investing!
""")
st.write("""
# ENSURE YOU HAVE FILLED OUT ALL INPUTS TO REMOVE ERROR BOX!!!
""")


startDate = datetime.today().strftime('%Y-%m-%d')
benchmark = st.sidebar.text_input("Select the benchmark ticker for your portfolio:")

numberStocks = st.sidebar.slider('Select the number of tickers in your portfolio')
st.sidebar.write('You have selected ', numberStocks, ' tickers to be in your portfolio.')
startYear = st.sidebar.text_input("Type year in 'YYYY' format")
startMonth = st.sidebar.text_input("Type month in 'MM' format")
startDay = st.sidebar.text_input("Type day in 'DD' format")
startDate = (startYear + "-" + startMonth + "-" + startDay)
endDate = datetime.today().strftime('%Y-%m-%d')



list = []
shareCount = []
portfolioBWD = 0
i = 1
while (i < (int(numberStocks)) + 1):
    tickerNum = str(i)
    userInputDescrip = "Ticker # " + tickerNum + ": "
    currentTickerSlot = st.sidebar.text_input(userInputDescrip, tickerNum)
    currentTickerName = "Number of shares of " + currentTickerSlot
    numberShares = st.sidebar.number_input(currentTickerName, 1, 100)
    list += [currentTickerSlot]
    shareCount += [numberShares]
    i += 1

benchmarkData = yf.Ticker(benchmark)
benchmarkHistory = benchmarkData.history()
benchmarkPrice = (benchmarkHistory.tail(1)['Close'].iloc[0])
benchmarkData = pdr.get_data_yahoo(benchmark, start = startDate, end = endDate)
benchmarkRet = benchmarkData.Close.pct_change()[1:]

def linreg(x, y):
    x = sm.add_constant(x)
    model = regression.linear_model.OLS(y, x).fit()
    x = x[:, 1]
    return  model.params[0], model.params[1]


stockNumber = 0
for stock in list:
    st.title(stock)
    # get data on this ticker
    tickerData = yf.Ticker(stock)
    # get the historical prices for this ticker
    tickerDf = tickerData.history(period = '1d', start = startDate, end = endDate)
    # Open	High	Low	Close	Volume	Dividends	Stock Splits

    st.line_chart(tickerDf.Close)
    stockData = pdr.get_data_yahoo(stock, start = startDate, end = endDate)
    stockRet = stockData.Close.pct_change()[1:]

    stockHistory = tickerData.history()
    stockPrice = (stockHistory.tail(1)['Close'].iloc[0])

    # Getting the Beta
    stockChoice = stockRet.values
    benchmarkChoice = benchmarkRet.values
    alpha, beta = linreg(benchmarkChoice, stockChoice)
    delta = shareCount[stockNumber]
    stockNumber += 1
    bwd = (beta * delta * (stockPrice / benchmarkPrice))
    portfolioBWD += bwd
    # st.write("Excess returns(alpha) of " + stock + " is: ", alpha)
    st.write("Current stock price of " + stock + "is: ", stockPrice)
    st.write("Risk factor(beta) of " + stock + " is: ", beta)
    # st.write("Delta of " + stock + " is: ", delta)
    st.write("The Beta Weighted Delta of " + stock + " is: ", bwd)

st.write("""
# The total portfolio weighted delta is:
""", portfolioBWD)
