from swigibpy import EWrapper
from attrdict import AttrDict
from pybroker.lib.ibutils import NewDF
from datetime import datetime

EMPTY_HDATA = NewDF('date','open','high','low','close','volume')
EMPTY_POSDATA = NewDF('instrument', 'expiry', 'exchange', 'quantity', 'currency')

class IBWrapper(EWrapper):
    """
    Wrapper contains all our data requested from the server.
    """
    
    def __init__(self):
        EWrapper.__init__(self)
        
        self.init_cache()

#Cache Functions        
    def init_cache(self):
        setattr(self, 'cache', AttrDict())
        
    def set(self, field, data):
        self.cache[field] = data
        
    def get(self, field):
        return self.cache[field] if field in self.cache.keys() else None
        
    
#Error Handling
    def init_call(self, *args):
        self.init_error()
        
        for arg in args:
            call = getattr(self, arg)
            call()
            
    def init_error(self):
        self.set('flag.iserror', False)
        self.set('error.msg', "")
        
    def error(self, id, errorCode, errorString):
        errors = [201,103,502,504,509,200,162,420,2105,1100,478,201,399]
        
        if errorCode in errors:
            print("IB error id %d string %s" % (errorCode, errorString))
            
            self.set('flag.iserror', True), self.set('error.msg', '')
            
    def currentTime(self, time_from_server):
        self.set('data.servertime')

#Position Data
    def init_portfolio(self):
        self.set('data.portfolio', [])
        self.set('data.accountvalue', [])
        self.set('flag.portfolio.finished', False)
    
    def updatePortfolio(self, contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName):
        portfolio = self.get('data.portfolio')

        portfolio.append((contract.symbol, contract.expiry, contract.primaryExchange, position, contract.currency))  
        
    def updateAccountValue(self, key, value, currency, accountName):
        account = self.get('data.accountvalue')
        
        account.append((key, value, currency, accountName))

    def accountDownloadEnd(self, accountName):
        self.set('flag.portfolio.done', True)        

    def updateAccountTime(self, timeStamp):
        pass
        
#Market Data
    def init_tickdata(self, id):
        pass
    def tickPrice(self, id, tickType, price, canAutoExecute):
        pass
            
#Historic Data
    def init_historicdata(self, tickerid):
        histdata = dict() if self.get('data.historicdata') is None else self.get('data.historicdata')
        
        histdata[tickerid] = EMPTY_HDATA
        
        self.set('data.historicdata', histdata), self.set('flag.historicdata.done', False)
        
    def historicalData(self, reqId, date, openprice, high, low, close, volume, barCount, WAP, hasGaps):

        if date[:8] == 'finished':
            self.set(self, 'flag.historicdata.done', True)
        else:
            historicdata = self.get('data.historicdata')[reqId]
            date = datetime.strptime(date, '%Y%m%d')
            historicdata.add_row(date = date, open = openprice, high = high, low = low, close = close, volume = volume)

#Functions we don't use
    def nextValidId(self, orderId):
        pass

    def managedAccounts(self, openOrderEnd):
        pass