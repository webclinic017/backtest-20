from datetime import datetime
import backtrader as bt  # https://www.backtrader.com/docu/
# Fix for pyfolio :
#    UserWarning: Module "zipline.assets" not found; 
#    mutltipliers will not be applied to position notionals.
import warnings
warnings.filterwarnings('ignore')
import pyfolio as pf  # https://quantopian.github.io/pyfolio/


class PercentReverter(bt.Sizer):
    params = (
        ('percents', 100),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        size = cash / data.close[0] * (self.params.percents / 100)
        return size


class CryptoFlash(bt.Strategy):
    params = (
        ('ema_short', 12), ('ema_long', 60)
    )

    def log(self, txt, f_name, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        full_txt = f'{dt.isoformat()},{txt}'
        if self.print_output:
            print(full_txt)
        f_name.write(full_txt + '\n')

    def __init__(self):
        self.print_output = False   # Change to True if you want to see info in console
        self.f = open("output_all.csv", "wt")
        self.f_trades = open("output_trades.csv", "wt")
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
                self.log(txt, self.f)
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
                self.log(txt, self.f)
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
            txt += f' Cost {order.executed.value:.8f}'
            txt += f' Comm {order.executed.comm}'
            txt += f' Pos {self.broker.getposition(self.datas[0]).size:.8f}'
            txt += f' NAV {self.dataclose[0] * self.broker.getposition(self.datas[0]).size:.8f}'
            txt += f' Cash {self.broker.get_cash():.8f}'
            txt += f' Port {self.broker.getvalue():.8f}'
            self.log(txt, self.f)
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            txt = f'** ERROR ** Order Not Executed Due To {order.Status[order.status]}'
            self.log(txt, self.f)

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        txt = f'TRADE Closed,Profit Gross,{trade.pnl:.2f},Net,{trade.pnlcomm:.2f}'
        self.log(txt, self.f)
        self.log(txt, self.f_trades)

    def next(self):
        # Simply log the closing price of the series from the reference
        txt = f'Open,{self.dataopen[0]:.8f}'
        txt += f',Close,{self.dataclose[0]:.8f}'
        txt += f',EmaShort,{self.ema_short[0]:.8f}'
        txt += f',EmaLong,{self.ema_long[0]:.8f}'
        txt += f',Cross,{self.crossover[0]:+.0f}'
        txt += f',Pos,{self.broker.getposition(self.datas[0]).size:.8f}'
        txt += f',NAV,{self.dataclose[0] * self.broker.getposition(self.datas[0]).size:.8f}'
        txt += f',Cash,{self.broker.get_cash():.8f}'
        txt += f',Port,{self.broker.getvalue():.8f}'
        self.log(txt, self.f)
        if self.crossover > 0:
            if self.position:
                self.order = self.close()

            # self.order_target_size(target=self.getsizing())
            self.buy(size=self.getsizing())

        if self.crossover < 0:
            if self.position:
                self.order = self.close()

            # self.order_target_size(target=-self.getsizing())
            self.sell(size=self.getsizing())

def run_backtest(print_output=True):
    cerebro = bt.Cerebro()

    # Do you want to use actual CryptoFlash data
    # or raw BitMex data for back test?
    # Uncomment the correct name for 'data_set'
    # data_set = 'cryptoflash.csv'
    data_set = 'bitmex.csv'

    # fromdate & todate are commented out as used in testing for shorter data set = quicker run time
    data = bt.feeds.GenericCSVData(
        dataname=data_set,
        # fromdate=datetime(2018, 10, 14, 0, 0, 0),
        # todate=datetime(2019, 11, 1, 0, 0, 0),
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
    start_portfolio_value = cerebro.broker.getvalue()
    start_cash = cerebro.broker.get_cash()

    cerebro.addstrategy(CryptoFlash)
    cerebro.addsizer(PercentReverter)

    # set commission scheme
    cerebro.broker.setcommission(commission=0.0, margin=0.00000001, mult=1)

    # Analyzer
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='draw_down')
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    results = cerebro.run()
    strat = results[0]
    end_portfolio_value = cerebro.broker.getvalue()
    end_cash = cerebro.broker.get_cash()

    # cerebro.plot()
    results_dic = {
        'start_portfolio': start_portfolio_value,
        'start_cash': start_cash,
        'end_portfolio': end_portfolio_value,
        'end_cash': end_cash,
        'strat': strat
    }
    return results_dic

if __name__ == '__main__':
    results_dic = run_backtest()
    print(f'*'*120)
    print(f'*** Results')
    print(f'*'*120)
    print(f'Starting Portfolio Value: {results_dic["start_portfolio"]:,.2f}')
    print(f'Starting Cash Value: {results_dic["start_cash"]:,.2f}')
    print(f'Ending Portfolio Value: {results_dic["end_portfolio"]:,.2f}')
    print(f'Ending Cash Value: {results_dic["end_cash"]:,.2f}')
    print('Annual Returns:', results_dic["strat"].analyzers.annual_return.get_analysis())
    print('Sharpe Ratio:', results_dic["strat"].analyzers.sharpe.get_analysis())
    print('SQN:', results_dic["strat"].analyzers.sqn.get_analysis())
    print('Draw Down:', results_dic["strat"].analyzers.draw_down.get_analysis())
