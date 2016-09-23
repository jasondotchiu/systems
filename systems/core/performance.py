#performance.py
import numpy as np

def equity(system):
    result = system.accounting.get_equity().ix[-1]
    return 'Total Equity: %s' % round(result, 0), result

def total_return(system):
    equity = system.accounting.get_equity()
    result = (equity.ix[-1] / equity.ix[0] - 1)
    return 'Total Return: %s' % round(result * 100, 2), result

def cagr(system):
    equity = system.accounting.get_equity()

    timedelta = (equity.index[-1] - equity.index[0]) / np.timedelta64(1, 'D')
    years = timedelta / 365
    
    result = np.exp(np.log(equity.ix[-1] / equity.ix[0]) / years) - 1
    
    return 'CAGR: %s' % round(result * 100, 2), result

def maxdd(system):
    equity = system.accounting.get_equity()
    result = (equity / equity.expanding().max() - 1).abs().max()
    return 'Max. DD: %s' % round(100 * result, 2), result

def mar_ratio(system):
    car = cagr(system)[1]
    dd = maxdd(system)[1]
    result = car / dd
    return 'MAR: %s' % round(result, 2), result
    
def annvol(system):
    equity = system.accounting.get_equity()
    chg = equity.pct_change()    
    result = chg.std() * np.sqrt(252)
    return 'Ann. Vol: %s' % round(100 * result, 2), result

def sortinovol(system):
    equity = system.accounting.get_equity()
    chg = equity.pct_change()    
    chg = chg.where(chg < 0).dropna()
    result = chg.std() * np.sqrt(252)
    return 'Sortino. Vol: %s' % round(100 * result, 2), result


def information_ratio(system):
    car = cagr(system)[1]
    vol = annvol(system)[1]
    result = car / vol
    return 'IR: %s' % round(result, 2), result
    
def sortino_ratio(system):
    car = cagr(system)[1]
    vol = sortinovol(system)[1]
    result = car / vol
    return 'Sortino: %s' % round(result, 2), result

def profit_by_year(system):
    result = profit_by_period(system, 'A')
    return 'Years Profit: %s' % round(100 * result, 2), result

def profit_by_month(system):
    result = profit_by_period(system, 'M')
    return 'Months Profit: %s' % round(100 * result, 2), result
    
def profit_by_period(system, freq = 'D'):
    pnl = profit_by_freq(system, freq)
    result = pnl.where(pnl > 0).count() / pnl.count()
    return result
    
def profit_by_freq(system, freq = 'D'):
    equity = system.accounting.get_equity()
    equity = system.accounting.get_equity(freq) if freq != 'D' else equity
    chg = equity.pct_change()    
    
    if len(equity) > 1:
        chg.ix[0] = equity.ix[1] / system.config.capital
        
    return chg

def time_in_drawdown(system):
    dd = system.accounting.get_drawdowns()
    
    nsample = len(dd)
    
    newhighs = len(dd.where(dd == 0).dropna())
    
    result = 1 -   newhighs / nsample
    
    return "Time in Drawdown: %s" % round(result * 100, 2), result 

def longest_drawdown(system):
    dd = np.sign(system.accounting.get_drawdowns()).abs()

    cum = dd.cumsum()
    
    diff = np.sign(cum.where(dd.diff() == -1))
    diff = diff * cum.shift(1)
    
    result = cum - diff.ffill()
    
    return result
    
    
    