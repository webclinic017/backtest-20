import datetime as dt
from pprint import pprint

import backtrader as bt


class FixedSize(bt.Sizer):
    params = (('stake', 1),)

    def _getsizing(self, comminfo, cash, data, isbuy):
        return self.params.stake


class FixedRerverser(FixedSize):
    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        size = self.p.stake * (1 + (position.size != 0))
        return size


class CryptoFlash(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.isoformat()} {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        sma_short = bt.indicators.EMA(self.data, period=12)
        sma_long = bt.indicators.EMA(self.data, period=60)
        self.crossover = bt.indicators.CrossOver(sma_short, sma_long)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log(
            f'Open {self.dataopen[0]:,.2f} | Close, {self.dataclose[0]:,.2f}')

        if self.crossover > 0:
            self.buy()
            self.log(f'BUY CREATE, {self.dataclose[0]:,.2f}')

        elif self.crossover < 0:
            self.sell()
            self.log(f'SELL CREATE, {self.dataclose[0]:,.2f}')


# Create a Data Feed
data = bt.feeds.GenericCSVData(
    dataname='cryptoflash.csv',
    fromdate=dt.datetime(2021, 6, 10),
    todate=dt.datetime(2021, 6, 17),
    dtformat='%Y-%m-%d %H:%M:%S',
    timeframe=bt.TimeFrame.Minutes,
    compression=60,
    datetime=0,
    open=1,
    high=2,
    low=3,
    close=4,
    volume=-1,
    openinterest=-1,
    nullvalue=0,
)

cerebro = bt.Cerebro()
cerebro.broker.set_cash(1000000)
print(f'Starting Portfolio Value: {cerebro.broker.getvalue():,.2f}')
cerebro.adddata(data)
cerebro.addstrategy(CryptoFlash)
cerebro.addsizer(FixedRerverser)
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
results = cerebro.run()
strat = results[0]
print(f'Ending Portfolio Value: {cerebro.broker.getvalue():,.2f}')
print(f'Current Cash Value: {cerebro.broker.get_cash():,.2f}')
# for e in strat.analyzers:
#     e.print()
cerebro.plot()