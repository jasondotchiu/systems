#datastore.py
from systems.core.utils import check_data_date
from systems.core.volatility import Volatility
from pickle import load

volatility = Volatility()

database = 'D:\\Dropbox\\Market Data\\MasterDB\\'

class DataStore():
    def __init__(self, system = None):                
        self._cache = { 'SYSTEM': dict() }
    
        self.load_instruments(system)

    def load_instruments(self, system):
        system.iter_instruments(self.load_futures_data, system)
        system.iter_instruments(self.load_fx_data, system)
        system.iter_instruments(self.load_volatility, system)
        system.iter_instruments(self.load_price_returns, system)
        
    def read_file(self, folder, instrument, suffix):
        """ Returns data from flat files """
        return load(open(database + folder + '\\' + instrument + '.' + suffix, 'rb'))        
    
    def load_price_returns(data, symbol, system):
        """ Calculate FX Adjusted Returns and Writes to Cache """
        price = data.price(symbol)
        
        mtmreturn = price.close.diff()
        fillreturn = (price[system.config.fillprice] - price.close.shift(1)).fillna(0)

        data.cache('returns.price', mtmreturn, symbol)
        data.cache('returns.fill', fillreturn, symbol)
        data.cache('returns.contract_mtm', mtmreturn * data.pv(symbol) * data.fx(symbol), symbol)        
        data.cache('returns.contract_ftm', fillreturn * data.pv(symbol) * data.fx(symbol), symbol)        
        
        #Slippage
        slippage = data.pv(symbol) * data.meta('slippage', symbol) * data.fx(symbol)
        data.cache('slippage', slippage, symbol)
        
    def load_futures_data(data, symbol, system):
        """ Reads Futures file and writes to symbol cache """
        price = data.read_file('Futures\\Price', symbol, 'futures')        
        meta = data.read_file('Futures\\Meta', symbol, 'meta')        
        warning = system.config.warnings
        
        check_data_date(price['continuous'].index[-1], symbol, warning)

        data.cache('price', price, symbol)
        data.cache('meta', meta, symbol)
            
    def load_fx_data(data, symbol, system):
        """ Reads FX file and writes to symbol cache """
        ccy = data.meta('currency', symbol)

        fx = data.read_file('FX', ccy, 'fx') if ccy != 'USD' else 1
        fx = fx.reindex(data.price(symbol).index).ffill() if ccy != 'USD' else fx
        
        data.cache('fx', fx, symbol)
        
    def load_volatility(data, symbol, system):
        """ Calculate Vol Based on Estimator """
        config = system.config.forecasting 
        price = data.price(symbol)                
        vol = volatility.estimator(price, config.vol_window, config.vol_estimator)
        data.cache('vol.price', vol, symbol)
        
    #Read Write Methods        
    def cache(self, itemname, item, instrument):
        instrument = instrument.upper()
        
        if instrument not in self._cache.keys():
            self._cache[instrument] = dict()
        
        self._cache[instrument][itemname] = item
    
    def get(self, itemname, instrument = 'system'):
        return self._cache[instrument.upper()][itemname]

    #Meta
    def brokerids(self, instrument):
        return self.meta('brokerid', instrument).strip().split(',')

    def brokerfactors(self, instrument):
        return self.meta('brokerfactor', instrument).strip().split(',')
        
    #Price Methods
    def meta(self, itemname, instrument):
        return self.get('meta', instrument.upper())[itemname]

    def fx(self, instrument):
        return self.get('fx', instrument.upper())
        
    def price(self, instrument, contract = 'continuous'):
        return self.get('price', instrument.upper())[contract]
    
    def price_front(self, instrument):
        return self.price(instrument, 'front')

    def price_carry(self, instrument):
        return self.price(instrument, 'carry')

    def expiry(self, instrument):
        return self.price(instrument)['expiry']
    #Meta Methods
    def pv(self, instrument):
        return self.meta('pv', instrument)
        
    #Return Methods
    def price_returns(self, instrument):
        return self.get('returns.price', instrument)
    
    def fill_returns(self, instrument):
        return self.get('returns.fill', instrument)
        
    def contract_mtm_returns(self, instrument):
        return self.get('returns.contract_mtm', instrument)        

    def contract_ftm_returns(self, instrument):
        return self.get('returns.contract_ftm', instrument)        
    
    def slippage(self, instrument):
        return self.get('slippage', instrument)
        
    #Vol Methods
    def price_vol(self, instrument):
        return self.get('vol.price', instrument)
    
    def contract_vol(self, instrument):
        return self.price_vol(instrument) * self.pv(instrument) * self.fx(instrument)