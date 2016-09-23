#ibest
from systems.broker.ibwrapper import IBWrapper
from attrdict import AttrDict
from time import time
from swigibpy import Contract
from swigibpy import EPosixClientSocket
import pandas as pd

WAIT = 5

class IBClient():
    account = AttrDict(newct = AttrDict(), jcsim = AttrDict(), rxsource = AttrDict())
    
    account['newct']['accountid'] = 'U9030396'
    account['newct']['port'] = 4001
    
    account['jcsim']['accountid'] = 'DU426948'
    account['jcsim']['port'] = 4002

    account['rxsource']['accountid'] = 'DU426948'
    account['rxsource']['port'] = 4003
    
    def __init__(self, accountname = None):  
        setattr(self, 'cache', AttrDict())
        
        callback = IBWrapper()
        
        tws = EPosixClientSocket(callback)

        self.set('accountid', self.account[accountname]['accountid'])  
        self.set('port', self.account[accountname]['port'])
        
        setattr(self, 'ibwrap', callback), setattr(self, 'tws', tws)        

    def get(self, field):
        return self.cache[field] if field in self.cache.keys() else None
    
    def set(self, field, data):
        self.cache[field] = data
                
            
    def check_errors(self, flag = None, timeout = 10):
        finished, iserror, timestart = False, False, time()
                
        while not finished and not iserror:
            finished = self.ibwrap.get('flag.' + flag + '.done')
            iserror = self.ibwrap.get('flag.iserror')
            
            if time() - timestart > timeout:
                iserror = True
            
            if iserror:
                print(self.ibwrap.get('error.msg'))
                return iserror
                
    def futures(self, symbol, expiry, exchange, currency):
        con = Contract()

        con.symbol, con.expiry, con.exchange, con.currency = symbol, expiry, exchange, currency
        
        setattr(self, '_contract', con)
        
    def getMarketPrice(self, id, contract, generalTicks = "", snapshot = True, mktDataOptions = 'XYZ'):
        self.tws.reqMktData(id, contract, generalTicks, snapshot, mktDataOptions)
    
    def getPortfolio(self):
        self.tws.eConnect("", self.get('port'), 995)
        
        self.ibwrap.init_call('init_portfolio')
        
        self.tws.reqAccountUpdates(True, self.get('accountid'))
        
        self.check_errors('portfolio')

        self.tws.eDisconnect()
    
        result = pd.DataFrame(self.ibwrap.get('data.portfolio'), columns = ['instrument', 'expiry', 'exchange', 'quantity', 'currency'])

        result.index = result['instrument']
        
        result['expiry'] = pd.to_datetime(result['expiry'], format='%Y%m%d')
      
        return result
