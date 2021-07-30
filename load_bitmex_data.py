import datetime
import time
import ccxt  # https://github.com/ccxt/ccxt/wiki/Manual
import pandas as pd

def load_bitmex_data(start_date, i):
    df_res = pd.DataFrame()
    while (i != 0):
        print(f'{i:3}: Getting 1,000 hourly OHLCV points from {start_date}')
        # Convert start_date to unix millisconds 
        unix_time_millis = datetime.datetime.timestamp(start_date) * 1000
        # Load 1h OHLCV candles from Bitmex, max is 1,000 per call
        ohlcv = ccxt.bitmex().fetchOHLCV('BTC/USD', '1h', limit=1000, since=unix_time_millis)
        df_bitmex = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df_bitmex.index = pd.to_datetime(df_bitmex['Timestamp'], unit='ms')
        df_bitmex = df_bitmex.drop('Timestamp', axis=1)
        # Store in df_res
        df_res = df_res.combine_first(df_bitmex)
        # Get last hour timestamp and increase 1 hour for next start_time 
        start_date = df_bitmex.index[-1] + datetime.timedelta(hours=1)
        # Decrement loop counter
        i = i - 1
        # Pause to comply with Bitmex API rate limits
        time.sleep(1)
    
    return df_res

if __name__ == '__main__':
    start_date = datetime.datetime(2018, 10, 14, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    df = load_bitmex_data(start_date=start_date, i=30)
    df.to_csv('bitmex.csv')