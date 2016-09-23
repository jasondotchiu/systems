#diagnostics class

from systems.core.modules import BaseModule
import pandas as pd



class Diagnostics(BaseModule):
    def __init__(self, system = None):
        BaseModule.__init__(self, system, 'diagnostics')
    
    def get_combined_forecast_diag(self, instrument, forecast):
        """
        Inputs Combined Forecast and Checks for Errors
        """
        sys = self.sys
        config = sys.config
        
        #Check for Max/Min Violation
        if config.forecasting.max_enable is True and forecast.abs().max() > config.forecasting.max_value:
            print("Warning in %s: Max Scalar Breached" % instrument)

        #Check for Expected Value
        scaledforecast = sys.data.get('forecasts.scaled', instrument).ix[-1]
                
        
    
    def get_instrument_returns_diag(self, instrument):
        system = self.sys
        forecasts = system.data.get('forecasts.scaled', instrument)
        forecast = system.forecasting.get_combined_forecast(instrument)
        targets = system.data.get('positions.target', instrument)
        trades = system.data.get('positions.trades', instrument)        
        vol = system.data.contract_vol(instrument)
        contractret = system.data.contract_mtm_returns(instrument)
        ftmret = system.data.contract_ftm_returns(instrument)
        cashret = system.data.get('returns.cash', instrument)
        comm = system.config.commission * trades.abs()
        result = pd.DataFrame({'forecast': forecast, 'vol': vol, 'target':targets, 'trades': trades, 
                               'pos': trades.cumsum(), 'calccashret': cashret, 'pctret': cashret / 1000000,
                                'conret': contractret, 'fillret': ftmret, 'comm': comm})                
        
        return result, forecasts
    

    def check_stops(self):
        for instrument in self.sys.config.instruments:
            result = self.check_instrument_stops(instrument)
            if result is not None:
                print(instrument)
                
    def check_instrument_stops(self, instrument):
        """
        Returns Boolean True/False on condition that cumreturns is < risk and forecast is != 0
        """
        sys = self.sys
        
        cumreturns = sys.data.get('signreturns', instrument).fillna(0)

        risk = sys.data.price_vol(instrument) * sys.config.risk_management.stop_size

        forecast = sys.forecasting.get_combined_forecast(instrument)
        
        result = pd.DataFrame({'cumret': cumreturns, 'risk': risk, 'forecast': forecast})
        
        result['check'] = (cumreturns < -risk).where(forecast != 0)
        
        flag = sum(result['check'])
        
        return True if flag > 0 else None