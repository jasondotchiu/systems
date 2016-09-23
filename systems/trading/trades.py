#trades
import pandas as pd

def calculate_slippage(filepath):
    trades = read_trades(filepath)
    trades = calculate_slippage_to_close(trades)
    slippage = trades.groupby('UnderlyingSymbol').sum()['slippage']
        
    return slippage
    
def read_trades(filepath):
    csv = pd.read_csv(filepath)    
    return csv

def calculate_slippage_to_close(trades):
    trades['slippage'] = (trades.ClosePrice - trades.TradePrice) * trades.Multiplier * trades.FXRateToBase * trades.Quantity
    return trades
    


result = calculate_slippage('D:\\Downloads\\DefaultTrades.csv')