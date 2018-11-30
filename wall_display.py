# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 16:54:31 2018

@author: A

1 clock - 400 ms
2 clock2 - 400 ms
3 weathercurrent - 1 hour on the dot
4 weatherforecast - 24 hours after six
5 accountgraph - 24 hours after six
6 market - 24 hours after six
argv1 for fullscreen
"""
import Tkinter as tk
import datetime
import pandas as pd
from weather import Weather, Unit
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import ImageTk, Image
import os, sys
import matplotlib.pyplot as plt
import dateutil.parser

def isoformat_parser(stock):
#    stock = stock
    for i in range(len(stock)):
        stock['start'][i] = dateutil.parser.parse(stock['start'][i])
    return stock

def fix_refresh(hrs=18, mins=15, secs=00):
    # refresh 24 hour frames after six
    now = datetime.datetime.now().time()
    refresh_time = datetime.time(hrs, mins, secs)
    time_diff = datetime.datetime.combine(datetime.date.min, refresh_time) - datetime.datetime.combine(datetime.date.min, now)
    ms = (time_diff.seconds + 0) * 1000 # time to refresh_time plus 60 s buffer
    ms = int(ms)
    
    print('time: %s. %.0fh%.0fm til refresh' %(str(now), round(ms/60./60./1000 - 0.5), (ms/60./60./1000 - round(ms/60./60./1000 - 0.5))*60)) # hour
    return ms

def create_canvas(frame, figx, figy):
    fig = matplotlib.figure.Figure(figsize=(figx, figy))
    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.get_tk_widget().pack()
    return fig, canvas

def clock_update():
    global date1
    date2 = datetime.datetime.now().strftime('%H:%M:%S')
    if date2 != date1: # if time string has changed from previous date, update time + date
        date1 = date2 
        clock.config(text=date2)
        clock2.config(text=datetime.datetime.now().strftime('%a, %B %d, %Y'))
    return
        
def weather_update(weather):
    # does reloading lookup refresh data? or condition/forecasts?
    lookup = weather.lookup(9848)
    #lookup = weather.lookup_by_location('victoria')
    condition = lookup.condition
    forecasts = lookup.forecast
    return condition, forecasts

def weathercurrent_update():
    condition, forecasts = weather_update(weather) 
    forecast = forecasts[0]
    weather_now = 'Condition: %s \nCurrent: %s %sC \n\nHigh: %s %sC \nLow: %s %sC' %(forecast.text, condition.temp, u"\u00b0", forecast.high, u"\u00b0", forecast.low, u"\u00b0")
    weather_current.config(text=weather_now)
    return

def weatherforecast_plot(ax, fig):
    forecasts = weather_update(weather)[1]
    casts = pd.DataFrame()
    for i in range(len(forecasts)):
        forecast = pd.DataFrame({'dates': datetime.datetime.strptime(forecasts[i].date, '%d %b %Y'),
                                 'conditions': forecasts[i].text,
                                 'highs': float(forecasts[i].high),
                                 'lows': float(forecasts[i].low),
                                 }, index=[i])
        casts = casts.append(forecast)
    
    ax.clear()
    ax.plot(casts['dates'], casts['lows'], marker='.', markersize=13)
    ax.plot(casts['dates'], casts['highs'], marker='.', markersize=13)
    ax.set_ylabel('Temperature (' + u"\u00b0" + 'C)')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.axes.get_xaxis().set_ticklabels(range(10))
    fig.tight_layout()
    
    for i in range(len(casts['conditions'])):
        if i % 2 == 0: 
            ax.annotate(casts['conditions'][i], (casts['dates'][i], casts['highs'][i]), weight='bold')
        elif i % 2 == 1:
            ax.annotate(((pd.to_numeric(casts['highs'])+pd.to_numeric(casts['lows']))/float(2))[i], (casts['dates'][i], casts['lows'][i]), weight='bold')
    fig.canvas.draw()
    return ax

def accountgraph_update():
    global img2
    if os.name == 'nt':
        img = Image.open('C:\\Users\\name\\for_walldisplay.png')
    elif os.name == 'posix':
        img = Image.open('/mnt/name/for_walldisplay.png')
#    img = img.resize((1200/2, 400/2))
    img2 = ImageTk.PhotoImage(img)
    account_graph.config(image = img2)
    return

def market_data(token, symbol, datestring, interval):
    data = token.candles(symbol, datestring, interval)[0]
    df = pd.DataFrame(data)
    df['rate'] = df['close']/df['close'].iloc[0]
    if interval == 'OneDay':
         df['start'] = pd.to_datetime(pd.to_datetime(df['start']).dt.date)
         df['end'] = pd.to_datetime(pd.to_datetime(df['end']).dt.date)
    return df

#############
# MAIN CODE #
#############
if len(sys.argv) > 1:
    fullscreen = True
else: 
    fullscreen = False
fullscreen = True # for windows testing
    
# create window
root = tk.Tk()
if fullscreen == False:
    root.geometry('1235x565') # half-height screen
elif fullscreen == True:
    root.geometry('1235x930') # full screen
root.title('Raspberry Pi Wall Display')
title_font = 8
b_width = 4
pads_in = 5 # for labels only
plt.rc('font', size=7) # for graph fontsize

# refresh time for 3-6 (forecast, account, market)
six_refresh = [18, 15] # market causes a delay of ~15s, therefore, over a week, 3-6 refresh will deviate by two minutes

    
###################################
# clock
clock_title = tk.Label(root, font=('times', title_font), text='Clock')
clock = tk.Label(root, font=('times', 60, 'bold'), bg='white', padx=pads_in, pady=pads_in, borderwidth=b_width, relief='ridge')
clock2 = tk.Label(root, font=('times', 28, 'bold'), bg='white', padx=pads_in, pady=pads_in, borderwidth=b_width, relief='ridge')
clock_ms = 400 # if too slow, weather won't catch with seconds condition

date1 = ''
def clock_tick():
    clock_update()
 
    clock.after(clock_ms, clock_tick)
    
###################################
weather = Weather(unit=Unit.CELSIUS) # required for today's and forecast weather
# today's weather
weathercurrent_title = tk.Label(root, font=('times', title_font), text='Weather')
weather_current = tk.Label(root, font=('times', 25, 'bold'), bg='white', padx=pads_in, pady=pads_in, borderwidth=b_width, relief='ridge')
# rearrange so it refreshs on the hour
next_hour = datetime.datetime.now().hour + 1
if next_hour == 24:
    next_hour = 00
weathercurrent_ms = fix_refresh(next_hour, 0, 00) 

def weathercurrent_tick():
    weathercurrent_update()

    weather_current.after(weathercurrent_ms, weathercurrent_tick)

#################
# ten day forecast
weatherforecast_title = tk.Label(root, font=('times', title_font), text='Forecast')
weather_forecast = tk.Frame(root, bg='white', borderwidth=b_width, relief='ridge')
weatherforecast_ms = fix_refresh(six_refresh[0], six_refresh[1])
   
fig1, canvas1 = create_canvas(weather_forecast, 4, 2)
ax1 = fig1.add_subplot(111)
def weatherforecast_tick():
    weatherforecast_plot(ax1, fig1)
    
    weather_forecast.after(weatherforecast_ms, weatherforecast_tick)
    
###################################
accountgraph_title = tk.Label(root, font=('times', title_font), text='Portfolio')
account_graph = tk.Label(root, bg='white', borderwidth=b_width, relief='ridge')
# plot account stock graph
#account_graph_ms = fix_refresh(six_refresh[0], six_refresh[1])
account_graph_ms = fix_refresh(19, 15)

def accountgraph_tick():
    accountgraph_update()
    
    account_graph.after(account_graph_ms, accountgraph_tick)
    
###################################
# market (its in its own section due to the try-except functionality)
if fullscreen == True:
    if os.name == 'nt':
        sys.path.append('C:/Users/name/Questrade_API/')
    elif os.name == 'posix':
        sys.path.append('/mnt/name/Questrade_API/')
    try:
        from questrade import *
    except:
        pass
    market_title = tk.Label(root, font=('times', title_font), text='Market')
    market = tk.Frame(root, bg='white', borderwidth=b_width, relief='ridge')
#    market_ms = fix_refresh(six_refresh[0], six_refresh[1])
    market_ms = fix_refresh(22, 15)
      
    fig2, canvas2 = create_canvas(market, 12, 3)
    ax2 = fig2.add_subplot(131)
    ax3 = fig2.add_subplot(132)
    ax4 = fig2.add_subplot(133)
    
    def market_plot(token, ax2, ax3, ax4, fig2):
        print('before: %s' %token.access_token)
        token.check_access() # test without this - if error, then it works
        print('after: %s' %token.access_token)
        ax2.clear()
        ax3.clear()
        ax4.clear()
        # since start 
        interval_2 = 'OneDay'
        datestring_2 = '2018-01-05 to today'
        sp500_2 = market_data(token, 'spx.in', datestring_2, interval_2)
        nasdaq_2 = market_data(token, 'comp.in', datestring_2, interval_2)
        ex_2 = market_data(token, 'dlr.to', datestring_2, interval_2)
        bundles = [sp500_2, nasdaq_2, ex_2]
        bundles_names = ['sp500', 'nasdaq', 'ex rate']
        # plot
        i = 0
        for ea in bundles:
            ax2.plot(ea['start'], ea['rate'], label=bundles_names[i])
            i = i + 1
        ax2.legend()
        ax2.set_title('Since start')
        ax2.set_ylabel('Rate')
        ax2.axes.get_xaxis().set_ticklabels([])
            
        # weekly
        last_monday = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
        datestring_3 = '%s to today' %datetime.datetime.strftime(last_monday, '%Y-%m-%d')
        interval_3 = 'HalfHour'
        sp500_3 = market_data(token, 'spx.in', datestring_3, interval_3)
        nasdaq_3 = market_data(token, 'comp.in', datestring_3, interval_3)
        ex_3 = market_data(token, 'dlr.to', datestring_3, interval_3)
        sp500_3 = isoformat_parser(sp500_3)
        nasdaq_3 = isoformat_parser(nasdaq_3)
        ex_3 = isoformat_parser(ex_3)
        bundles = [sp500_3, nasdaq_3, ex_3]
        # plot
        i = 0
        for ea in bundles[0:2]:
            ax3.plot(ea['start'], ea['rate'], marker='.', markersize=5, label=bundles_names[i])
            i = i + 1
        ax3.plot(ex_3['start'], ex_3['rate'], linestyle='None', marker='.', markersize=5, label=bundles_names[i])
        ax3.set_title('Weekly')
        ax3.axes.get_xaxis().set_ticklabels([])
            
        # current holdings (ranked by absolute gains, but % is relative to the initial buy-in)
        positions = token.positions()[0]
        positions2 = []
        for ea in positions:
            try:
                positions2.append([ea['symbol'],
                    round(100*(ea['currentPrice'] - ea['averageEntryPrice']) / ea['averageEntryPrice'], 2),
                    (ea['totalCost'] - (ea['totalCost'] * ea['currentPrice'] / ea['averageEntryPrice'])) * -1])
            except:
                print('%s sold?' %ea['symbol'])
        positions2 = pd.DataFrame(positions2)
        positions2 = positions2.sort_values(by=[2], ascending=False)
        positions2 = positions2.reset_index(drop=True)
            
        ax4.bar(positions2[0], positions2[2]) # doesn't plot correctly in windows, but it does on Pi
#        ax4.bar(range(len(positions2)), positions2[2])
#        ax4.set_xticks(range(len(positions2)))
#        ax4.set_xticklabels((positions2[0]))
        for i in range(len(positions2)):
            ax4.annotate(str(positions2[1][i])+'%', (i-0.26, (max(positions2[2]) + min(positions2[2]))/2), weight='bold', size=10)
        ax4.set_title('Current Holdings')
        
        fig2.tight_layout()
        fig2.autofmt_xdate()
        fig2.canvas.draw()
        print(positions2)
        return ax2, ax3, ax4
    
    def market_tick():
        try:
            market_plot(token, ax2, ax3, ax4, fig2)
        except:
            print('questrade down or plot down')
    
        print('last updated-6: %s' %datetime.datetime.now())
        market.after(market_ms, market_tick)
            
        
    try:
        market_title.grid(row=5, column=0, columnspan=3)
        market.grid(row=6, column=0, columnspan=3)
        market_tick()
        market_ms = 1000*60*34
    except:
        print('questrade down')

        
###################################    
# grid layout
pads_out = 5
clock_title.grid(row=0, column=0)
clock.grid(row=1, column=0, padx=(pads_out, pads_out), pady=(pads_out, pads_out), sticky='nsew')
clock2.grid(row=2, column=0, padx=(pads_out, pads_out), pady=(pads_out, pads_out), sticky='nsew')
weathercurrent_title.grid(row=0, column=1)
weather_current.grid(row=1, column=1, padx=(pads_out, pads_out), pady=(pads_out, pads_out), sticky='nsew', rowspan=2)
weatherforecast_title.grid(row=0, column=2)
weather_forecast.grid(row=1, column=2, rowspan=2, padx=(pads_out, pads_out), pady=(pads_out, pads_out), sticky='nsew')
accountgraph_title.grid(row=3, column=0, columnspan=3)
account_graph.grid(row=4, column=0, columnspan=3, padx=(pads_out, pads_out), pady=(pads_out, pads_out), sticky='')

clock_tick()
clock_ms = 400 # no fix
weathercurrent_tick()
weathercurrent_ms = 1000*60*60 # no fix (kinda)
weatherforecast_tick()
weatherforecast_ms = 1000*60*60*24
accountgraph_tick()
account_graph_ms = 1000*60*60*24

root.mainloop() #continous loop

