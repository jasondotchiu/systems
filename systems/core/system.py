#system
from systems.core.modules import load_futures_config
from systems.core.datastore import DataStore
from systems.core.forecasting import Forecasting
from systems.core.positions import Positions
from systems.core.accounting import Accounting
from systems.core.reporting import Reporting
from systems.core.trading import Trading
from systems.core.diagnostics import Diagnostics
from systems.core.utils import profile

class TradingSystem():
    def __init__(self, name, warnings = True):
        self.config = load_futures_config(name)
        
        self.name = name
    
        profile(self.load_systems)
        
    def load_systems(self):
        self.data = DataStore(self)
        self.forecasting = Forecasting(self)
        self.positions = Positions(self)
        self.accounting = Accounting(self)
        self.trading = Trading(self)
        self.diag = Diagnostics(self)
        self.reporting = Reporting(self)
        
    #Backtest
    def backtest(system, **kwargs):
        """
        
        :: Generate Raw Forecasts
        :: Calculate Forecast Scaling
        :: Rescale Forecasts
        :: Cap Raw Forecasts
        """        
        config = system.config
        
        for key in kwargs:
            if hasattr(system.config, key) is True:
                config[key] = kwargs[key]
                    
        debug = system.config.profile
        
        profile(system.forecasting.get_raw_forecasts, debug)
        profile(system.forecasting.get_forecast_scaling, debug)
        profile(system.accounting.get_portfolio_returns, debug, config.capital)

        if config.report is True:
            profile(system.reporting.get_performance_stats, debug)

        if config.plot is True:
            system.accounting.get_equity().plot()
            
        #Diagnostics
        system.diag.check_stops()
    
        
    def iter_instruments(system, function, *args):
        for instrument in system.config.instruments:
            function(instrument, *args)
            