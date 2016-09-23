#forecastscaling
import numpy as np
import pandas as pd

def get_forecast_multiplier(system, forecast):
    """
    """    
    if system.config.forecasting.avg_method == 'pool':
        result = get_pooled_forecast_multiplier(system, forecast)
    if system.config.forecasting.avg_method == 'mean':
        result = get_mean_forecast_multiplier(system, forecast)
        
    return result
    
def get_mean_forecast_multiplier(system, forecast):
    instruments = system.config.instruments
    
    def _get_forecast(forecast, instrument):
        return system.data.get('forecasts.raw', instrument)[forecast].abs().median()

    medians = [ _get_forecast(forecast, instrument) for instrument in instruments ]
        
    result = np.array(medians)
    result = np.mean(medians)
    
    return np.round(system.config.forecasting.avg_value / result, 0)
    
def get_pooled_forecast_multiplier(system, forecast):
    """
    Returns a value which is the our target avg. forecast by the avg absolute forecast
    """
    def _get_forecast_scalars(system, forecast):
        """ 
        Returns array of raw scalar values
        """
        scalars = []
        
        def _get_forecast(instrument, forecast):
            return system.data.get('forecasts.raw', instrument)[forecast].abs().fillna(0).tolist()
            
        for instrument in system.config.instruments:
            scalars += _get_forecast(instrument, forecast) 
        
        return np.array(scalars)

    scalar  = _get_forecast_scalars(system, forecast)

    avgscalar = np.median(abs(scalar))
    
    return round(system.config.forecasting.avg_value / avgscalar, 0)
    
    

def scale_and_cap_forecasts(system, forecastraw):
    """ Returns a DataFrame of rescaled and capped forecasts """   
    rules = system.config.trading_rules

    def _cap_forecasts(forecasts, config):
        if config.forecasting.max_enable is True:
            forecasts[forecasts > config.forecasting.max_value] = config.forecasting.max_value
            forecasts[forecasts < -config.forecasting.max_value] = -config.forecasting.max_value
        return forecasts
        
    forecasts = { f: forecastraw[f] * rules[f]['scalar'] for f in forecastraw }
    forecasts = pd.DataFrame(forecasts)
    forecasts = _cap_forecasts(forecasts, system.config)
    
    return forecasts
    
    