from datetime import datetime
import statsmodels.api as sm
import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
from yahoo_fin import options
from wallstreet import Stock, Call, Put
from alpha_vantage.timeseries import TimeSeries
from pandas_datareader import data as pdr
import pandas as pd
from statsmodels import regression

st.set_option('deprecation.showPyplotGlobalUse', False)
ts = TimeSeries(key='JM4MU7FUTY9MN6VK', output_format='pandas')
#client_id = 'NCRJQTMSAW3PLXYMZXOTA6DAL2LUZLRW'

st.write("""
# Winter Haven Capital
Democratization of Retail Investing!
""")

st.write("""
# FILL IN ALL FIELDS TO REMOVE THE ERRORS!
""")

startDate = datetime.today().strftime('%Y-%m-%d')
endDate = datetime.today().strftime('%Y-%m-%d')

benchmark = 'SPY'
benchmarkData = yf.Ticker(benchmark)
benchmarkHistory = benchmarkData.history()
benchmarkPrice = (benchmarkHistory.tail(1)['Close'].iloc[0])
benchmarkData = pdr.get_data_yahoo(benchmark, start = '2019-11-29', end = '2019-11-29')
benchmarkRet = benchmarkData.Close.pct_change()[1:]
benchmark = st.sidebar.text_input("Select the benchmark ticker for your portfolio:")

numberStocks = st.sidebar.slider('Select the number of tickers in your portfolio')
st.sidebar.write('You have selected ', numberStocks, ' tickers to be in your portfolio.')
startYear = st.sidebar.text_input("Type year in 'YYYY' format")
startMonth = st.sidebar.text_input("Type month in 'MM' format")
startDay = st.sidebar.text_input("Type day in 'DD' format")
startDate = (startYear + "-" + startMonth + "-" + startDay)
endDate = datetime.today().strftime('%Y-%m-%d')

st.write("Select the hedge date.")
hedgeYear = st.sidebar.text_input("Type hedge year in 'YYYY' format")
hedgeMonth = st.sidebar.text_input("Type hedge month in 'MM' format")
hedgeDay = st.sidebar.text_input("Type hedge day in 'DD' format")
hedgeDate = (hedgeYear + "-" + hedgeMonth + "-" + hedgeDay)


benchmarkData = yf.Ticker(benchmark)
benchmarkHistory = benchmarkData.history()
benchmarkPrice = (benchmarkHistory.tail(1)['Close'].iloc[0])
benchmarkData = pdr.get_data_yahoo(benchmark, start = startDate, end = endDate)
benchmarkRet = benchmarkData.Close.pct_change()[1:]

betaWeights = []
explode = []
list = []
shareCount = []
expiryDates = []
userSelectedHedgeDates = {}
portfolioBWD = 0
i = 1
while (i < (int(numberStocks)) + 1):
    tickerNum = str(i)
    userInputDescrip = "Ticker # " + tickerNum + ": "
    currentTickerSlot = st.sidebar.text_input(userInputDescrip, tickerNum)
    currentTickerName = "Number of shares of " + currentTickerSlot
    numberShares = st.sidebar.number_input(currentTickerName, 1, 100)
    list += [currentTickerSlot]
    explode += [0]
    shareCount += [numberShares]
    i += 1


st.write("""
# The portfolio breakdown:
""")
labels = list
sizes = shareCount
fig1, ax1 = plt.subplots()
ax1.pie(sizes, explode = explode, labels = labels, autopct='%1.1f%%', shadow = True, startangle = 90)
ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
st.pyplot(fig1)

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
    betaWeights += [bwd]

st.write("""
# The total portfolio beta-weighted delta is:
""", portfolioBWD)

st.write("""
# The portfolio beta-weighted delta break down:
""")
labels = list
sizes = betaWeights
fig2, ax2 = plt.subplots()
ax2.pie(sizes, explode = explode, labels = labels, autopct='%1.1f%%', shadow = True, startangle = 90)
ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
st.pyplot(fig2)


# Predicting Sells/Buys

def find_closed_exp_dates(input_exp_day, input_exp_month, input_exp_year, expiration_dates_list, top_closest=10):
  df = pd.DataFrame(columns = ['potential_times', 'time_difference'])
  df['potential_times'] = expiration_dates_list

  input_date = datetime(input_exp_year, input_exp_month, input_exp_day)

  for index in range(len(df)):
    p_time = df['potential_times'][index]
    potential_exp = datetime.strptime(p_time, "%B %d, %Y")
    difference = abs((potential_exp - input_date).total_seconds()/60)
    df['time_difference'][index] = difference

  sorted_df = df.sort_values(by='time_difference')
  top_closest_dates = sorted_df['potential_times'][:top_closest].values
  return top_closest_dates

# 1: Target Delta
targetDelta = st.number_input("What is your target portfolio delta?", 1)

# 2: Reduce/Increase/Neutralize exposure
reqDelta = (targetDelta * 100) - portfolioBWD
exposString = "No action required"
if(reqDelta < 0):
    exposString = "Reduce Exposure; Buy Puts of delta:" + str(reqDelta)
if(reqDelta > 0):
    exposString = "Add Exposure; Buy Calls of delta:" + str(reqDelta)
# 3: Expiry dates
    # options import to find all expiry dates
benchMarkExpDate = options.get_expiration_dates(benchmark)
#stockExpirationDict = {}
st.write("Select hedge dates: ")
for stock in list:
    expDates = options.get_expiration_dates(stock)
    bestExpDates = find_closed_exp_dates(int(hedgeDay), int(hedgeMonth), int(hedgeYear), expDates, 3)
    currentStr = "Select hedge date for " + stock + " : "
    userSelectedHedgeDates[stock] = st.radio(currentStr, bestExpDates)



# 4: correct option type

# 5: corres. delta, strike prices

# 6: strike prices for delta range

# 7: calls/puts details
