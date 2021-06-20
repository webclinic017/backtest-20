import pandas as pd

# Download cryptoflash data for Bitcoin
# Convert to csv with datetime,open,high,low,close,volume
# Write to file

url = 'https://cryptoflash.net/api//historical/1?price_source_id=1'
df = pd.read_json(url)
df_res = df
df_res.index = pd.to_datetime(df_res['ts'])
df_res = df.drop(['created_at', 'updated_at', 'coin_id',
                 'price_source_id', 'ts'], axis=1)
df_res.index.rename('datetime', inplace=True)
# Open needed for backtrader = Close from last hour
df_res['open'] = df_res['close'].shift(1)
df_res.to_csv('cryptoflash.csv')
