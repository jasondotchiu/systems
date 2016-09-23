#trading.py
from systems.core.modules import BaseModule
from systems.broker import ibclient
from datetime import datetime
import numpy as np
import pandas as pd

np.seterr(invalid = 'ignore')
pd.set_option('display.max_columns', 1000)
#pd.set_option('display.width', 1000)

class Trading(BaseModule):
    def __init__(self, system = None):
        BaseModule.__init__(self, system, 'trading')

    def get_trading_report(self, capital = None, print_trades = True, print_roll = True):        
        """ Returns DataFrame of Target Positions, prints trades & rolls """        
        sys = self.sys
        
        sys.backtest()
        
        broker = self.get_broker_positions(sys.config.ibaccount)
        targetpos = sys.positions.get_target_positions(capital)
        targetdf = self.get_target_df(broker, targetpos)
        trades = self.get_trades_from_target_df(targetdf)
        roll = self.get_rolls_from_target_df(targetdf)
        
        print('\n\n', trades, '\n\n', roll)
        
        return targetdf
        
    def get_broker_positions(self, accountname = 'newct'):
        """ Returns DataFrame of Positions """
        result = ibclient.IBClient(accountname).getPortfolio()
        result = result.where(result['quantity'] != 0).dropna()
        result = self.reindex_broker_symbols(result)
        return result
    
    def reindex_broker_symbols(self, broker):
        """ Reindexes Broker Indexes to System Instrument Codes """
        broker.index = [ self.get_instrument_from_broker_symbol(brokersymbol) for brokersymbol in broker.index ]
        factors = [ self.get_factor_from_broker_symbol(r.Index, r.instrument) for r in broker.itertuples() ]        
        broker['quantity'] *= factors
        return broker
    
    def get_instrument_from_broker_symbol(self, brokersymbol):
        """ Returns Instrument Code Based on Broker Symbol """
        for symbol in self.sys.config.instruments:
            brokerid = self.sys.data.brokerids(symbol)
            if brokersymbol in brokerid:
                return symbol
    
    def get_factor_from_broker_symbol(self, symbol, brokersymbol):        
        """ Returns Factor for Contract Based on Broker Symbol """
        brokerid = self.sys.data.meta('brokerid', symbol).strip().split(',')
        brokerfactor = self.sys.data.brokerfactors(symbol)
        position = [ i for i, x in enumerate(brokerid) if x == brokersymbol ][0]
        return float(brokerfactor[position]) 
    
    def get_target_df(self, broker, target):
        """ Returns DataFrame of Targets """
        def _get_combined_df(function):
            result = { instrument: function(instrument) for instrument in self.sys.config.instruments }
            result = pd.DataFrame(result).ffill()
            return result.ix[-1]
            
        df = pd.DataFrame(index = target.index)
        
        #Write Target DataFrame
        df['forecasts'] = _get_combined_df(self.sys.forecasting.get_combined_forecast)
        df['vol'] = _get_combined_df(self.sys.data.contract_vol) * self.sys.config.risk_management.stop_size
        df['targetraw'] = target
        df['targetpos'] = target.round()
        df['targetexp'] = _get_combined_df(self.sys.data.expiry)
        df['brokerpos'] = broker['quantity']
        df['brokerpos'] = df['brokerpos'].fillna(0)
        df['brokerexp'] = broker['expiry']
        df['brokerexp'] = df['brokerexp'].fillna(df['targetexp'])
        df['exch'] = broker['exchange']
        df['currency'] = broker['currency']
        #Write to File
        filename = format(datetime.now(), '%Y-%m-%d')        
        df.to_csv('.\\futures\\' + self.sys.name + '\\positions\\' + filename + '.csv')
        
        return df
    
    def get_trades_from_target_df(self, target):
        """ Returns DataFrame of Trades """
        tradeqty = target['targetpos'] - target['brokerpos']
        target['trade'] = tradeqty
        trades = target.fillna(0).where(tradeqty != 0).dropna()
        trades = trades[['targetraw','targetpos','targetexp','brokerpos','brokerexp','trade','exch','currency']]
        return trades
    
    def get_rolls_from_target_df(self, target):
        roll = (((target.brokerexp - target.targetexp) / np.timedelta64(1, 'D')).abs() > 7).fillna(False)
        target['roll'] = roll
        return target.where(roll == True).dropna()[['targetexp','brokerexp']]               


    def calculate_slippage_to_model(self):
        def _read_csv(filepath):
            csv = pd.read_csv(filepath)    
            csv['TradeDate'] = pd.to_datetime(csv['TradeDate'], format = '%Y%m%d')
            return csv
            
        def _calculate_slippage_to_close(trades):
            trades['slippage'] = (trades.ClosePrice - trades.TradePrice) * trades.Multiplier * trades.FXRateToBase * trades.Quantity
            return trades

        trades = _read_csv('.\\futures\\' + self.sys.name + '\\broker\\trades.csv')
        trades = _calculate_slippage_to_close(trades)
        trades = trades.where(trades['TradeDate'] > self.sys.config.start).dropna()
        slippage = trades.groupby('UnderlyingSymbol').sum()['slippage']
        
        return slippage.sum()
        
    
    def load_equity(self):
        def _read_csv(filepath):
            csv = pd.read_csv(filepath, index_col = 0)   
            csv.index = pd.to_datetime(csv.index)
            return csv
        
        equity = _read_csv('.\\futures\\' + self.sys.name + '\\broker\\equity.csv').ffill()
            
        equity = equity.where(equity != 0).dropna()        

        return equity
        
