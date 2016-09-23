#forecasting.py
from systems.core.modules import BaseModule
from systems.core.forecastscaling import get_forecast_multiplier, scale_and_cap_forecasts
from systems.core.utils import calc_cum_returns, load_module
from functools import reduce
import pandas as pd
import numpy as np

class Forecasting(BaseModule):
    def __init__(self, system = None):    
        BaseModule.__init__(self, system, 'forecasting')
        
        self.rules = load_module(system, 'rules')                                #Load Trading Rules
        
    def get_forecast(self, forecast, instrument):
        return self.sys.data.get('forecasts.raw', instrument)[forecast]
        
    def get_combined_forecast(self, instrument):
        """ Returns combined forecast Series """
        sys = self.sys

        def _get_scaled_forecast(instrument):
            """ Returns Scaled Forecast """
            forecastraw = sys.data.get('forecasts.raw', instrument).ffill()
            #Rescale & Cap Forecast
            forecasts = scale_and_cap_forecasts(sys, forecastraw)
            #Reindex to Start Date
            forecasts = forecasts.loc[sys.config.start:sys.config.end]
            #Cache Forecast
            sys.data.cache('forecasts.scaled', forecasts, instrument)            
            return forecasts

        def _get_forecast_weights(forecasts, instrument):
            weights = [ sys.config.trading_rules[f]['weight'] for f in forecasts ]
            sys.data.cache('forecasts.weights', weights, instrument)
            return weights
        
        forecasts = _get_scaled_forecast(instrument)
        weights = _get_forecast_weights(forecasts, instrument)
        forecasts = (forecasts * weights).sum(axis = 1)
        
        if sys.config.long_trades is False:
            forecasts[forecasts > 0] = 0
        if sys.config.short_trades is False:
            forecasts[forecasts < 0] = 0
            
        if sys.config.risk_management.enable_stops is True:
            result = self.get_forecast_after_stops(forecasts, instrument).ffill().dropna()
        else:
            result = forecasts.ffill().dropna()

        sys.diag.get_combined_forecast_diag(instrument, result)    
        
        return result
            
    #Stage Functions
    def get_raw_forecasts(self):
        """
        SYSTEM STAGE
        
        Iterate through and get raw forecasts
        """
        self.sys.iter_instruments(self.get_instrument_raw_forecasts)

    def get_forecast_scaling(self):
        """ 
        SYSTEM STAGE

        Iterate through forecasts and calculate scaling 
        """         
        rules = self.sys.config.trading_rules
        
        for r in rules:
            if rules[r]['scalar_method'] == 'calculate':
                rules[r]['scalar'] = get_forecast_multiplier(self.sys, r)

    
                
    #Instrument Level Functions    
    def get_instrument_raw_forecasts(self, symbol):
        """
        Returns a DF with raw forecasts 
        IMPORTANT: Takes all price data into account
        """
        def _eval_data(data, system):
            """ Returns dict of data """
            return { item: reduce(getattr, data[item].split('.'), system)(symbol) for item in data }
                
        def _eval_params(params):
            """ Returns dict of params """
            return None if params is None else { item: params[item] for item in params }
        
        def _eval_rule(function, data, params):
            """ Evaluates function and returns output """
            function = getattr(self.rules, function)
            return function(**data) if params is None else function(**data, **params)
        
        sys = self.sys
        
        config = sys.config
        rules = config.trading_rules
        scalars = dict()
        
        for r in rules:            
            rule = rules[r]
            data = _eval_data(rule['data'], sys)
            params = _eval_params(rule['params'])
            
            scalars[r] = _eval_rule(rule['function'], data, params)
        
        result = pd.DataFrame(scalars)
        
        sys.data.cache('forecasts.raw', result, symbol)
        
        return result        

    def get_forecast_after_stops(self, forecast, symbol):
        """ Returns forecast after stops """
    
        sys = self.sys
        
        def _calculate_net_position(signal, trade, cumreturns, risk):
            """ Returns sign of signal """
            result = signal.where(signal == trade)
            result = result.where(cumreturns > -risk)
            return np.sign(result.fillna(0).abs())
            
        signal = np.sign(forecast.shift(0))
        returns = sys.data.price_returns(symbol)
        risk = sys.data.price_vol(symbol) * sys.config.risk_management.stop_size
        
        longreturns = calc_cum_returns(returns, signal, 1)
        shortreturns = calc_cum_returns(returns, signal, -1)
        
        netlong = _calculate_net_position(signal, 1, longreturns, risk)
        netshort = _calculate_net_position(signal, -1, shortreturns, risk)

        sys.data.cache('signreturns', longreturns + shortreturns, symbol)

        #Return Loc'ed Item
        result = (forecast * np.sign((netlong + netshort).abs()))

        return result
