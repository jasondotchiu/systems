#volatility.py
from pandas import concat

class Volatility():
    def __init__(self):
        pass
    
    def estimator(self, price, x, method = 'ATR'):
        function = getattr(self, method)
        return function(price, x)
    
    def ATR(self, price, x):
        hl = price.high - price.low
        hc = abs(price.high - price.close.shift(1))
        lc = abs(price.low - price.close.shift(1))
        
        tr = concat([hl, hc, lc], axis = 1).max(axis = 1)
        
        return tr.ewm(x).mean()
        
    def standard(self, price, x):
        return price.close.diff().rolling(x).std()
