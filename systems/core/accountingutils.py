#accountingutils
import pandas as pd

def get_groups_from_config(sys):
    """ Returns list of commodity groups """
    return set([ sys.data.meta('sector', symbol) for symbol in sys.config.instruments ])
    

def get_returns_by_group(sys, groups):
    instruments = { symbol: sys.data.meta('sector', symbol) for symbol in sys.config.instruments }
    instruments = pd.Series(instruments)
    returns = sys.accounting.get_portfolio_returns(sys.config.capital)
    returnsgrp = { group: {} for group in groups }    
    
    for g in groups:
        instrslice = instruments.where(instruments == g).dropna().index        
        returnsgrp[g] = returns[instrslice].fillna(0).sum(axis = 1)          

    return pd.DataFrame(returnsgrp)


