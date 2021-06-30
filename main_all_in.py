from datetime import datetime
import backtrader as bt


class EmaCross(bt.SignalStrategy):
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        full_txt = f'{dt.isoformat()}, {txt}'
        print(full_txt)
        self.f.write(full_txt + '\n')

    def __init__(self):
        self.f = open("output.csv", "wt")
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.ema_short = bt.ind.EMA(period=5)
        self.ema_long = bt.ind.EMA(period=20)
        self.crossover = bt.ind.CrossOver(self.ema_short, self.ema_long)
        self.signal_add(bt.SIGNAL_LONGSHORT, self.crossover)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            if order.status == order.Submitted:
                # Print order details (lots of decimal places)
                txt = f'Order Submitted:'
                txt += f' {order.created.size:.20f}'
                txt += f' @'
                txt += f' {order.created.pricelimit:.8f}'
                txt += f' = {order.created.size * order.created.pricelimit:.20f}'
                self.log(txt)
            else:
                self.log(f'Order Status: {order.Status[order.status]}')
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                txt = f'BUY EXECUTED:'
            elif order.issell():
                txt = f'SELL EXECUTED:'

            txt += f' {order.executed.size:.20f}'
            txt += f' @'
            txt += f' {order.executed.price:.8f}'
            txt += f' = {order.executed.size * order.executed.price:.20f}'
            txt += f' Pos {self.broker.getposition(self.datas[0]).size:.8f}'
            txt += f' NAV {self.dataclose[0] * self.broker.getposition(self.datas[0]).size:.8f}'
            txt += f' Cash {self.broker.get_cash():.8f}'
            txt += f' Port {self.broker.getvalue():.8f}'
            self.log(txt)
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            txt = f'** ERROR ** Order Not Executed Due To {order.Status[order.status]}'
            self.log(txt)

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        txt = f'Open, {self.dataopen[0]:.8f}'
        txt += f', Close, {self.dataclose[0]:.8f}'
        txt += f', EmaShort, {self.ema_short[0]:.8f}'
        txt += f', EmaLong, {self.ema_long[0]:.8f}'
        txt += f', Cross, {self.crossover[0]:+.0f}'
        txt += f', Pos, {self.broker.getposition(self.datas[0]).size:.8f}'
        txt += f', NAV, {self.dataclose[0] * self.broker.getposition(self.datas[0]).size:.8f}'
        txt += f', Cash, {self.broker.get_cash():.8f}'
        txt += f', Port, {self.broker.getvalue():.8f}'
        self.log(txt)

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    # data = bt.feeds.YahooFinanceData(
    #     dataname='BTC-USD',
    #     fromdate=datetime(2015, 3, 1),
    #     todate=datetime(2015, 6, 1))

    # data = bt.feeds.YahooFinanceData(
    #     dataname='2006-min-005.txt',
    #     fromdate=datetime(2006, 1, 2),
    #     todate=datetime(2006, 1, 10))

    data = bt.feeds.GenericCSVData(
        dataname='2006-min-005.txt',
        fromdate=datetime(2006, 1, 2, 0, 0, 0),
        todate=datetime(2006, 1, 10, 0, 0, 0),
        timeframe=bt.TimeFrame.Minutes,
        compression=1,
        nullvalue=0.0,
        dtformat=('%Y-%m-%d'),
        tmformat=('%H:%M:%S'),
        datetime=0,
        time=1,
        open=2,
        high=3,
        low=4,
        close=5,
        volume=6,
        openinterest=7
    )

    cerebro.adddata(data)

    cerebro.broker.set_cash(1000000)
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():,.8f}')
    print(f'Current Cash Value: {cerebro.broker.get_cash():,.8f}')

    cerebro.addstrategy(EmaCross)

    # Can not be 100% as broker will reject on margin requirements
    # Also if large price move from closing bar to open price may not have $$
    cerebro.addsizer(bt.sizers.AllInSizer, percents=99)

    cerebro.run()
    print(f'Ending Portfolio Value: {cerebro.broker.getvalue():,.8f}')
    print(f'Current Cash Value: {cerebro.broker.get_cash():,.8f}')

    cerebro.plot()
