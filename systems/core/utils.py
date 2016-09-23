#utils.py
from datetime import datetime
from importlib.util import spec_from_file_location, module_from_spec
from pandas.tseries.offsets import BDay
from time import time
import numpy as np

def profile(function, debug = False, *args):
    """ Times Function Execution """
    ts = time()
    result = function(*args)

    if debug is True:
        print('profile: %s took %s seconds.' % (function.__name__, time() - ts))    

    return result
    
def load_module(system, file = None, folder = 'futures'):
    path = '.\\' + folder + '\\' + system.name + '\\' + file + '.py'
    spec = spec_from_file_location('rules', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def align_series(alignfrom, alignto, pad = 'ffill'):
    return alignfrom.reindex(alignto.index, method = pad)


def calc_cum_returns(returns, signal, trade):
    sign = np.sign(signal)
    series = returns.where(sign == trade) 
    cumsum = series.cumsum().ffill()
    reset = -cumsum.loc[series.isnull()].diff().fillna(cumsum)
    return series.where(series.notnull(), reset).cumsum() * trade

def get_nearest_bday():
    """ Returns most recent weekday if today is not a weekday """
    return datetime.now() if datetime.now().weekday() < 5 else datetime.now() - BDay()

def check_data_index_date(bar):
    return True if datetime.date(bar) < datetime.date(get_nearest_bday()) else False
        
def check_data_date(lastbar, symbol, warnings):
    if check_data_index_date(lastbar) is True and warnings is True:
            print('Warning: %s last date is %s' % (symbol, format(lastbar, '%Y-%m-%d')))

