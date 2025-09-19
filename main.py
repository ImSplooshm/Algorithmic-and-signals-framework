import asyncio
import logging
from telegram import Bot
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import pandas as pd

import math

import MetaTrader5 as mt5

import time
from datetime import datetime, timedelta
import ta


#telegram codes
TOKEN = #TELEGRAM TOKEN HERE
CHAT_ID = #TELEGRAM ID HERE



#mt5 details
login = int(input("Enter MT5 Login: "))
password = str(input("Enter MT5 Password: "))
server = str(input("Enter MT5 Server: "))
interval = int(input("Enter check interval in minutes (e.g., 1, 5, 15): "))

ALGO_TRADE = False


def get(symbol, range, timeframe):
    mt5.initialize()
    authorized = mt5.login(
        login=login,
        password=password,
        server=server
    )
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0,range)
    rates = pd.DataFrame(rates)

    rates['time'] = pd.to_datetime(rates['time'], unit='s')
    rates.rename(columns={'close':'Close', 'open':'Open','high':'High','low':'Low'}, inplace=True)

    return rates

def open_trade(symbol, sl_price, tp_price, action):
    mt5.initialize()
    authorized = mt5.login(
        login=login,
        password=password,
        server=server
    )

    if not authorized:
        print("Failed to initialize MT5:", mt5.last_error())
        return mt5.last_error()

    # Check symbol info
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None or not symbol_info.visible:
        print(f"Symbol {symbol} not found or not visible.")
        mt5.shutdown()
        return mt5.last_error()

    # Get tick data for current price
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Failed to get tick for {symbol}")
        mt5.shutdown()
        return mt5.last_error()

    # Decide order type
    if action.lower() == "long":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
    elif action.lower() == "short":
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:

        mt5.shutdown()
        return mt5.last_error()

    # Get symbol properties
    min_distance = mt5.symbol_info(symbol).trade_stops_level * symbol_info.point

    # Adjust SL/TP if too close
    if action.lower() == "long":
        sl = sl_price
        tp = tp_price
        if abs(price - sl) < min_distance:
            sl = price - min_distance
        if abs(tp - price) < min_distance:
            tp = price + min_distance
    else:
        sl = sl_price
        tp = tp_price

        if abs(sl - price) < min_distance:
            sl = price + min_distance
        if abs(price - tp) < min_distance:
            tp = price - min_distance

    # Get account balance
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info:", mt5.last_error())
        mt5.shutdown()
        quit()

    free_margin = account_info.margin_free
    tick = mt5.symbol_info_tick(symbol)
    margin_1lot = mt5.order_calc_margin(order_type,symbol,1.0, price)

    raw_volume  = free_margin / margin_1lot 

    step        = symbol_info.volume_step
    vol_max     = symbol_info.volume_max

    volume      = math.floor(raw_volume / step) * step
    volume      = min(volume, vol_max)


    # Prepare order request
    request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": order_type,
    "price": price,
    "sl": round(sl, symbol_info.digits),
    "tp": round(tp, symbol_info.digits),
    "deviation": 20,
    "magic": 123456,
    "comment": "Auto trade",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send order
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.retcode}, {result.comment}")
        mt5.shutdown()
        return f"Order failed: {result.retcode}, {result.comment}"

    print(f"Order placed successfully. Ticket: {result.order}")
    mt5.shutdown()
    return result.order



def wait_until_next_1_minute_interval():
    now = datetime.now()

    next_minute = (now.minute // interval + 1) * interval
    if next_minute == 60:
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)

    wait_seconds = (next_time - now).total_seconds()
    print(f"Waiting {wait_seconds:.0f} seconds until {next_time.strftime('%H:%M:%S')}")
    time.sleep(wait_seconds)

def delay_until(hour,minute = 0, second = 0, year=None, month=None, day=None):
    now = datetime.now()

    if year and month and day:
        target = datetime(year, month, day, hour, minute, second)
    else:
        target = datetime(now.year, now.month, now.day, hour, minute, second)
        if target <=now:
            target += timedelta(days=1)
    
    delay = (target - now).total_seconds()
    print(f'Delaying until: {target} ({delay:.2f} seconds)')
    time.sleep(delay)
    

async def check_condition_and_notify():
    for ticker in tickers:
        df = get(ticker, 1000, '5m')
        trade_data = #YOUR METHOD HERE
        '''
        output method result in the form:
        data = {'action':'long'/'short',
                'sl': FLOAT,
                'tp':FLOAT}
        '''

        if trade_data != None:
            try:
                await bot.send_message(chat_id=CHAT_ID, text=f"Stock: {ticker}\nSignal: {trade_data['signal']}\nEntry: {trade_data['entry']}\nSL: {trade_data['sl']}\nTP 1: {trade_data['tp_1']}\nTP 2: {trade_data['tp_2']}")
                logger.info("Condition met message sent.")
            
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                await bot.send_message(chat_id='6093061317', text = e)
            if ALGO_TRADE == True:
                order = open_trade(ticker, trade_data['sl'], trade_data['tp_1'], trade_data['signal'])
                await bot.send_message(chat_id='6093061317', text = order)


        else:
            logger.info("Condition not met; no message sent.")

async def main():

    scheduler.add_job(check_condition_and_notify, 'interval', minutes=interval)
    scheduler.start()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("Bot is running with scheduled condition checks.")
    await asyncio.Event().wait()

if __name__ == '__main__':
    delay_until(#CHOOSE TIME TO DELAY UNTIL: HOUR, MINUTE)

    tickers = ['EURUSD','GBPUSD','USDJPY']
    print(tickers)


    wait_until_next_1_minute_interval()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    bot = Bot(token=TOKEN)
    app = ApplicationBuilder().token(TOKEN).build()
    scheduler = AsyncIOScheduler()
    asyncio.run(main())

