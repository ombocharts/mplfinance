import datetime as dt
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
from matplotlib import style
import matplotlib.dates as mdates
import numpy as np
import mplfinance as mpf
yf.pdr_override()

##############################################################

#I marked up this document to explain some of the code. If you have any questions on how it works...
#let me know, thanks! 

#Tyler/@ombocharts

##############################################################
#Change either to add them to the chart or remove them - automatically does the rest
enableWebbyRSI = True
enableRS = True
##############################################################

#sets the moving averages and corresponding colors (ex. 8ema is 'b' - blue)
emasUsed = [8,21]
emaColors = ['b', 'm']
smasUsed = [50,200]
smaColors = ['r', 'k']
usedVolumeMA = [50]

ogStart = dt.datetime(2020,1,1) #ogstart means original start
start =  ogStart - dt.timedelta(days=2 * max(smasUsed)) #check resetDate for explaination on the 2 *
now = dt.datetime.now()
stock = input("Enter your stock ('quit' to exit): ")


def setMovingAverages():
	#If this is confusing I recommend Richard Moglen's python tutorial
	global emasUsed, smasUsed, df
	for x in emasUsed:
		ema = x
		df["EMA_"+str(ema)] = df['Adj Close'].ewm(span = ema).mean()
	for x in smasUsed:
		sma = x
		df["SMA_"+str(sma)] = df['Adj Close'].rolling(window = sma).mean()
	for x in usedVolumeMA:
		volMA = x
		df["VOL_"+str(volMA)] = df['Volume'].rolling(window = volMA).mean()



def webbyRSI():
	#calculates the distance from the 21 ema, and calculates the percent from it
	global df, percentFrom21
	percentFrom21 =[]
	for row in df.index:
	 	appendMe = ((df['Adj Close'][row] - df['EMA_21'][row])/df["Adj Close"][row] * 100)
	 	if appendMe < 0:
	 		appendMe = 0
	 	percentFrom21.append(appendMe)			
	df["PERCENT_FROM_21"] = percentFrom21
	#df["WRSI_SMA_10"] = df["PERCENT_FROM_21"].rolling(window = 10).mean()#line is no longer needed --> mav = 10 does this for me

def relativeStrength():
	#calculates the RS of the stock vs. SPY
	global df
	spydf = pdr.get_data_yahoo("SPY",start, now)
	stockRS = []
	for row in df.index:
		appendMe = ((df['Adj Close'][row])/spydf['Adj Close'][row])
		stockRS.append(appendMe)
	df["RS"] = stockRS

def resetDate():
	#I created this because I had issues with the moving averages - not very important

	#Explaination:
	#the dates are in trading days, so when resetting the date, adding 200 days actuallys puts the date forward...
	#further than intended b/c its setting it forward 200 trading days, not 200 calendar days

	#Fix:
	#I doulbed the distance back it goes to ensure that theres enough data for the longest moving average...
	#and had a list to count how many trading days to remove (I used the length as the index: in iloc) until it hit the starting day...
	#the reason its within a range of around 6 days is because the date entered isn't necessarily on a trading day
	global df, ogStart
	removeList = []	
	for i in df.index:
		removeList.append(df["Date"][i])
		og = mdates.date2num(ogStart)
		passedDate = df["Date"][i]
		if int(passedDate >= int(og) - 3 and int(passedDate) <= int(og + 3)):
			df = df.iloc[int(len(removeList)):]
			break

def additions():
	#Sets all the extra 'addplots' to one list -> allows for more control
	global df, additions, emaColors, smaColors

	#KEY
	#panel 0 - price
    #panel 1 - volume
    #panel 2 - next indicator   


	#This variable is the index of the next panel to be added. starts at 2 - since price and volume already exists
	nextPanel = 2

	#this creates a horizontal line as long as the data frame 
	line6 = []
	line4 = []
	line2 = []
	for i in df.index:
		line6.append(6) 
		line4.append(4)
		line2.append(2)

	#creating an array to put every element from every indicator into. this is because mpf.plot only allows for one addplot
	#as a result, we must condense each seperate indicator into one array - I seperated from the start for organizational purposes
	additions =[]

	#Code for the WebbyRSI addition to the plot
	if enableWebbyRSI:
		webbyRSI_add = [
			mpf.make_addplot(df["PERCENT_FROM_21"],panel = 2, type='bar', color = 'b', mav = 10, width = .75, ylabel = "WebbyRSI"),
			mpf.make_addplot(line6,panel = nextPanel,color='r'),
		    mpf.make_addplot(line4,panel = nextPanel,color='y'),
		    mpf.make_addplot(line2,panel = nextPanel,color='g')
				] 
		for x in webbyRSI_add:
			additions.append(x)
		#since panel is being used, move to the next to set up for following indicator
		nextPanel += 1

	#Code for the Relative Strength addition to the plot
	if enableRS:
		RS_add = [
				#str(stock) +
				mpf.make_addplot((df['RS']),panel=nextPanel,color='g', ylabel =  "RS")
				]
		for x in RS_add:
			additions.append(x)
		nextPanel += 1


	#Code for the moving averages addition to the plot
	movingAverages_add = []
	for x in smasUsed:
		sma = x
		movingAverages_add.append(mpf.make_addplot(df['SMA_'+str(sma)],panel = 0, color = smaColors[smasUsed.index(sma)])) #setting ema to color set at top
	for x in emasUsed:
		ema = x
		movingAverages_add.append(mpf.make_addplot(df['EMA_'+str(ema)],panel = 0, color = emaColors[emasUsed.index(ema)]))
	for x in usedVolumeMA:
		volMA = x
		movingAverages_add.append(mpf.make_addplot(df['VOL_'+str(volMA)],panel = 1))
	for x in movingAverages_add:
		additions.append(x)
		




def figures():
	global df, additions, stock
	#sets all the additions
	additions()

	#volume = True creates another panel (panel 1) of volume with correctly colored bars
	mpf.plot(df, type = "candle", addplot=additions,panel_ratios=(1,.25),figratio=(1,.25),figscale=1.5, style = 'blueskies', volume = True, title = str(stock) + " Daily")
	mpf.show()

while stock != "quit":
	df = pdr.get_data_yahoo(stock, start, now)
	df["Date"] = mdates.date2num(df.index)
	setMovingAverages()
	webbyRSI()
	relativeStrength()
	resetDate()
	figures()


	stock = input("Enter your stock ('quit' to exit): ")

	##############

	#Thanks for reading!

	##############



