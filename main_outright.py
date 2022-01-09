import datetime
import backtrader as bt  # https://www.backtrader.com/docu/
# Fix for pyfolio :
#    UserWarning: Module "zipline.assets" not found; 
#    mutltipliers will not be applied to position notionals.
import warnings
warnings.filterwarnings('ignore')
import pyfolio as pf  # https://quantopian.github.io/pyfolio/


class BuyAndHold_More_Fund(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        full_txt = f'{dt.strftime("%Y-%m-%d")},{txt}'
        print(full_txt)
        self.f.write(full_txt + '\n')

    def __init__(self):
        self.f = open("output_all.csv", "wt")
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.order = None
    
    def start(self):
        # Activate the fund mode and set the default value at 100
        self.broker.set_fundmode(fundmode=True, fundstartval=100.00)

        self.cash_start = self.broker.get_cash()
        self.val_start = 100.0

    # def nextstart(self):
    #     # Buy all the available cash
    #     # size = int(self.broker.get_cash() / self.data)
    #     size = self.broker.get_cash() / self.data
    #     self.buy(size=size)

    #     # Buy all the available cash
    #     # self.order_target_value(target=self.broker.get_cash())

    def stop(self):
        # calculate the actual returns
        self.roi = (self.broker.get_value() / self.cash_start) - 1.0
        self.froi = self.broker.get_fundvalue() - self.val_start
        # print('ROI:        {:.2f}%'.format(100.0 * self.roi))
        # print('Fund Value: {:.2f}%'.format(self.froi))
        txt = f'ROI,{100.0 * self.roi:.2f}%'
        self.log(txt)
        txt = f'Fund Value,{self.froi:.2f}'
        self.log(txt)

    def next(self):
        # Simply log the closing price of the series from the reference
        txt = f'Open,{self.dataopen[0]:.8f}'
        txt += f',Close,{self.dataclose[0]:.8f}'
        txt += f',Pos,{self.broker.getposition(self.datas[0]).size:.8f}'
        txt += f',NAV,{self.dataclose[0] * self.broker.getposition(self.datas[0]).size:.8f}'
        txt += f',Cash,{self.broker.get_cash():.8f}'
        txt += f',Port,{self.broker.getvalue():.8f}'
        self.log(txt)

        # Buy more
        ts = self.datas[0].datetime.datetime(0)
        buy_dates = {
            datetime.date(2014, 6, 27),
            datetime.date(2014, 7, 25),
            datetime.date(2014, 8, 13),
            datetime.date(2015, 7, 2),
            datetime.date(2019, 1, 31),
            datetime.date(2020, 1, 31),
            datetime.date(2020, 2, 27),
            datetime.date(2020, 5, 2),
            datetime.date(2020, 5, 22),
            datetime.date(2020, 9, 9),
            datetime.date(2021, 1, 6),
            datetime.date(2021, 1, 21),
            datetime.date(2021, 2, 23),
            }
        if ts.date() in buy_dates:
            cash_increment = 10000
            # Add the influx of cash to the broker
            self.broker.add_cash(cash_increment)
            # # buy available cash
            # target_value = self.broker.get_value() + cash_increment
            # self.order_target_value(target=target_value)
            # Buy all the available cash
            size = self.broker.get_cash() / self.data
            self.buy(size=size)

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
            txt += f' Cost {order.executed.value:.8f}'
            txt += f' Comm {order.executed.comm}'
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
        txt = f'TRADE Closed,Profit Gross,{trade.pnl:.2f},Net,{trade.pnlcomm:.2f}'
        self.log(txt)

def run_backtest():
    # Disable the 3 Observers are automatically added 
    # cerebro = bt.Cerebro(stdstats=False)
    cerebro = bt.Cerebro()

    # fromdate & todate are commented out as used in testing for shorter data set = quicker run time
    data = bt.feeds.GenericCSVData(
        dataname='backtest/btc_price_history.csv',
        fromdate=datetime.datetime(2014, 6, 1, 0, 0, 0),
        # todate=datetime.datetime(2016, 1, 1, 0, 0, 0),
        # timeframe=bt.TimeFrame.Minutes,
        # compression=60,
        nullvalue=0.0,
        dtformat=('%Y-%m-%d'),
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1
    )
    cerebro.adddata(data)

    # cerebro.broker.set_cash(0)
    start_portfolio_value = cerebro.broker.getvalue()
    start_cash = cerebro.broker.get_cash()

    # # Broker
    # broker_kwargs = dict(coc=True)  # default is cheat-on-close active
    # cerebro.broker = bt.brokers.BackBroker(**broker_kwargs)

    # cerebro.addstrategy(CryptoFlash)
    # cerebro.addsizer(PercentReverter)

    cerebro.addstrategy(BuyAndHold_More_Fund)
    cerebro.addsizer(bt.sizers.FixedSize)

    # set commission scheme
    # cerebro.broker.setcommission(commission=0.0, margin=0.00000001, mult=1)

    # Fund mode so add Observers to chart for FundValue and FundShares
    cerebro.addobserver(bt.observers.FundValue)
    cerebro.addobserver(bt.observers.FundShares)

    # Analyzer
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='draw_down')
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    results = cerebro.run()
    strat = results[0]
    end_portfolio_value = cerebro.broker.getvalue()
    end_cash = cerebro.broker.get_cash()
 
    # cerebro.plot()

    figure = cerebro.plot()[0][0]
    figure.savefig('backtest/plot_outright.png')

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
    print('Returns:', results_dic["strat"].analyzers.returns.get_analysis())
