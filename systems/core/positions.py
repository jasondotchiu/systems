#positions.py
from systems.core.modules import BaseModule
import numpy as np
import pandas as pd

class Positions(BaseModule):
    def __init__(self, system = None):
        BaseModule.__init__(self, system, 'positions')
    
    def get_target_positions(self, capital = None):
        """ Returns Weighted Positions """
        sys = self.sys

        capital = sys.config.capital if capital is None else capital
        
        targetfunc = self.get_target_position_from_forecasts
        rawtargets = { symbol: targetfunc(symbol, capital) for symbol in sys.config.instruments }
        
        targets = pd.DataFrame(rawtargets).ffill().ix[-1]
        weights = sys.data.get('portfolio.weights').ix[-1]
        
        return targets * weights
        
    def get_positions(self, symbol, capital):
        return self.get_trades(symbol, capital).cumsum()

    def get_trades(self, symbol, capital):
        """ Returns Series of Trades """
        if 'positions.trades' in self.sys.data._cache[symbol].keys():
            return self.sys.data.get('positions.trades', symbol)
        else:
            return self.get_trades_from_forecasts(symbol, capital)
        
    def get_trades_from_forecasts(self,symbol, capital):
        """ Cache trades from target positions """        
        target = self.get_target_position_from_forecasts(symbol, capital)

        trades = target.shift(1).fillna(0).diff()
    
        self.sys.data.cache('positions.trades', trades, symbol)

        return trades

    def get_target_position_from_forecasts(self, symbol, capital):
        """ Returns rounded target forecast / contract volatility """
        sys = self.sys
        
        equityrisk = sys.config.risk_management.equity_risk
        
        forecast = sys.forecasting.get_combined_forecast(symbol) / 10
        
        vol = sys.data.contract_vol(symbol) * sys.config.risk_management.stop_size
        
        #if system.config.forecasting.vol_min_apply is True:
        #    vol[vol < system.config.forecasting.vol_min_value] = system.config.forecasting.vol_min_value
        
        dailyrisk = capital * equityrisk
        target = (forecast * dailyrisk / (vol)).round(0).ffill()
        target = target[sys.config.start : sys.config.end]
        
        #Set First Target as 0
        if len(target) > 0:
            target.ix[0] = 0
        
        sys.data.cache('positions.target', target, symbol)     

        return target
            
