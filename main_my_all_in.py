from datetime import datetime
import backtrader as bt


class PercentReverter(bt.Sizer):
    params = (
        ('percents', 90),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        else:
            size = abs(position.size) + (position.size + cash /
                                         data.close[0]) * (self.params.percents / 100)
        return size


class CryptoFlash(bt.Strategy):
    params = (
        ('ema_short', 12), ('ema_long', 60)
    )

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
        self.ema_short = bt.ind.EMA(period=self.params.ema_short)
        self.ema_long = bt.ind.EMA(period=self.params.ema_long)
        self.crossover = bt.ind.CrossOver(self.ema_short, self.ema_long)
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            if order.status == order.Submitted:
                # Print order details (lots of decimal places)
                txt = f'ORDER Submitted:'
                if order.isbuy():
                    txt += f' BUY'
                elif order.issell():
                    txt += f' SELL'
                txt += f' {order.created.size:.20f}'
                txt += f' @'
                txt += f' {order.created.pricelimit:.8f}'
                txt += f' = {order.created.size * order.created.pricelimit:.20f}'
                self.log(txt)
            else:
                # self.log(f'Order Status: {order.Status[order.status]}')
                txt = f'ORDER Accepted:'
                if order.isbuy():
                    txt += f' BUY'
                elif order.issell():
                    txt += f' SELL'
                txt += f' {order.created.size:.20f}'
                txt += f' @'
                txt += f' {order.created.pricelimit:.8f}'
                txt += f' = {order.created.size * order.created.pricelimit:.20f}'
                self.log(txt)
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            txt = f'ORDER Completed:'
            if order.isbuy():
                txt += f' BUY'
            elif order.issell():
                txt += f' SELL'
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

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        txt = f'TRADE Closed: Profit Gross {trade.pnl:.2f} Net {trade.pnlcomm:.2f}'
        self.log(txt)

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
        # if self.crossover > 0:
        #     if self.position:
        #         self.order = self.close()
            
        #     self.order_target_size(target=self.getsizing())
        # if self.crossover < 0:
        #     if self.position:
        #         self.order = self.close()
            
        #     self.order_target_size(target=-self.getsizing())

    def next_open(self):
        if self.order is not None:
            return

        if self.crossover > 0:
            self.order_target_size(target=self.getsizing())
        if self.crossover < 0:
            self.order_target_size(target=-self.getsizing())

# class EmaCross(bt.SignalStrategy):
#     params = (('ema_short', 12), ('ema_long', 60,))

#     def log(self, txt, dt=None):
#         ''' Logging function for this strategy'''
#         dt = dt or self.datas[0].datetime.datetime(0)
#         full_txt = f'{dt.isoformat()}, {txt}'
#         print(full_txt)
#         self.f.write(full_txt + '\n')

#     def __init__(self):
#         self.f = open("output.csv", "wt")
#         self.dataclose = self.datas[0].close
#         self.dataopen = self.datas[0].open
#         self.ema_short = bt.ind.EMA(period=self.params.ema_short)
#         self.ema_long = bt.ind.EMA(period=self.params.ema_long)
#         self.crossover = bt.ind.CrossOver(self.ema_short, self.ema_long)
#         self.signal_add(bt.SIGNAL_LONGSHORT, self.crossover)

#     def notify_order(self, order):
#         if order.status in [order.Submitted, order.Accepted]:
#             # Buy/Sell order submitted/accepted to/by broker - Nothing to do
#             if order.status == order.Submitted:
#                 # Print order details (lots of decimal places)
#                 txt = f'Order Submitted:'
#                 txt += f' {order.created.size:.20f}'
#                 txt += f' @'
#                 txt += f' {order.created.pricelimit:.8f}'
#                 txt += f' = {order.created.size * order.created.pricelimit:.20f}'
#                 self.log(txt)
#             else:
#                 self.log(f'Order Status: {order.Status[order.status]}')
#             return

#         # Check if an order has been completed
#         # Attention: broker could reject order if not enough cash
#         if order.status in [order.Completed]:
#             if order.isbuy():
#                 txt = f'BUY EXECUTED:'
#             elif order.issell():
#                 txt = f'SELL EXECUTED:'

#             txt += f' {order.executed.size:.20f}'
#             txt += f' @'
#             txt += f' {order.executed.price:.8f}'
#             txt += f' = {order.executed.size * order.executed.price:.20f}'
#             txt += f' Pos {self.broker.getposition(self.datas[0]).size:.8f}'
#             txt += f' NAV {self.dataclose[0] * self.broker.getposition(self.datas[0]).size:.8f}'
#             txt += f' Cash {self.broker.get_cash():.8f}'
#             txt += f' Port {self.broker.getvalue():.8f}'
#             self.log(txt)
#             self.bar_executed = len(self)

#         elif order.status in [order.Canceled, order.Margin, order.Rejected]:
#             txt = f'** ERROR ** Order Not Executed Due To {order.Status[order.status]}'
#             self.log(txt)

#         # Write down: no pending order
#         self.order = None

#     def notify_trade(self, trade):
#         if not trade.isclosed:
#             return
#         txt = f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}'
#         self.log(txt)

#     def next(self):
#         # Simply log the closing price of the series from the reference
#         txt = f'Open, {self.dataopen[0]:.8f}'
#         txt += f', Close, {self.dataclose[0]:.8f}'
#         txt += f', EmaShort, {self.ema_short[0]:.8f}'
#         txt += f', EmaLong, {self.ema_long[0]:.8f}'
#         txt += f', Cross, {self.crossover[0]:+.0f}'
#         txt += f', Pos, {self.broker.getposition(self.datas[0]).size:.8f}'
#         txt += f', NAV, {self.dataclose[0] * self.broker.getposition(self.datas[0]).size:.8f}'
#         txt += f', Cash, {self.broker.get_cash():.8f}'
#         txt += f', Port, {self.broker.getvalue():.8f}'
#         self.log(txt)

#     def next_open(self):
#         txt = f'open {self.datas[0].open[0]:.2f} and close {self.dataclose[0]:.2f}'
#         self.log(txt)
#         sizer = self.broker.get_cash() / self.datas[0].open[0] - 0.1
#         txt = f'sizer: {sizer} cash: {self.broker.get_cash()} next_open price: {self.datas[0].open[0]}'
#         self.log(txt)
#         if self.position:
#             self.order = self.close()
#         else:
#             self.order = self.buy(size = sizer)


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    data = bt.feeds.GenericCSVData(
        dataname='cryptoflash.csv',
        fromdate=datetime(2018, 10, 14, 0, 0, 0),
        todate=datetime(2018, 11, 1, 0, 0, 0),
        timeframe=bt.TimeFrame.Minutes,
        compression=60,
        nullvalue=0.0,
        dtformat=('%Y-%m-%d %H:%M:%S'),
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1
    )
    cerebro.adddata(data)

    cerebro.broker.set_cash(1000000)
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():,.8f}')
    print(f'Current Cash Value: {cerebro.broker.get_cash():,.8f}')

    cerebro.addstrategy(CryptoFlash)
    cerebro.addsizer(PercentReverter)

    # Disable check margin/cash before accepting an order into the system
    cerebro.broker.set_checksubmit(checksubmit=False)

    # cerebro.addwriter(bt.WriterFile, csv=True, out='bt_output.csv')

    cerebro.broker.set_coo(True) 
    cerebro.run(cheat_on_open=True, quicknotify=True)
    # cerebro.run()
    print(f'Ending Portfolio Value: {cerebro.broker.getvalue():,.8f}')
    print(f'Current Cash Value: {cerebro.broker.get_cash():,.8f}')

    # cerebro.plot()
