#accounting
from systems.core.modules import BaseModule
from systems.core.utils import load_module
import systems.core.accountingutils as utils
import pandas as pd

class Accounting(BaseModule):
    def __init__(self, system = None):
        BaseModule.__init__(self, system, 'accounting')

        self.weighting_rules = load_module(system, 'weighting')
                    
    def get_portfolio_slippage(self, start = None):
        sys = self.sys
        
        instruments = sys.config.instruments

        basis = { symbol: sys.data.meta('slippage', symbol) for symbol in instruments }
        trades = { symbol: sys.positions.get_trades(symbol) for symbol in instruments }
    
        def _slippage(symbol):
            return basis[symbol] * trades[symbol].abs() * sys.data.meta('pv', symbol) * sys.data.fx(symbol)

        forecastslippage = pd.DataFrame({ symbol: _slippage(symbol) for symbol in instruments })
        
        return pd.DataFrame(forecastslippage).sum() / pd.DataFrame(trades).abs().sum()
    
    def get_drawdowns(self, plot = False):
        equity = self.get_equity()
        drawdown = equity / equity.expanding().max() - 1        

        if plot is True:
            drawdown.plot()
            
        return drawdown
        
    def get_returns(self, freq = 'D'):
        if freq is 'D':
            return self.get_equity().pct_change()
        else:
            eq = self.get_equity(freq)
            result = eq.pct_change()
            result.ix[0] = eq.ix[0] / self.sys.config.capital - 1
            return result
            
    def get_equity(self, freq ='D'):
        """ Returns scaled Equity Series """
        if self.iscached('portfolio.equity', 'system') is True:
            equity = self.sys.data.get('portfolio.equity')
            return equity.resample(freq).last() if freq is not 'D' else equity
        else:
            returns = self.get_portfolio_returns(self.sys.config.capital).sum(axis = 1).add(1).cumprod()
            self.sys.data.cache('portfolio.equity', returns * self.sys.config.capital, 'system')            
            returns = returns.resample(freq).last() if freq is not 'D' else returns            
            result = returns * self.sys.config.capital             
        
        return result

    def calculate_raw_portfolio_returns(self, capital):
        """ Returns DataFrame of Raw Returns """        
        sys = self.sys
        
        if self.iscached('portfolio.rawreturns', 'system') is True:
            result = sys.data.get('portfolio.rawreturns', 'system')
        else:
            result = { symbol: self.get_instrument_returns(symbol, capital) for symbol in sys.config.instruments }        
            result = pd.DataFrame(result).loc[sys.config.start:sys.config.end].fillna(0)            
            sys.data.cache('portoflio.rawreturns', result, 'system')
        
        return result
        
    def calculate_portfolio_weights(self):
        """ Returns DataFrame of Portfolio Weights """
        sys = self.sys
        
        if self.iscached('portfolio.weights', 'system') is True:
            weights = sys.data.get('portfolio.weights')
        else:
            weights = getattr(self.weighting_rules, sys.config.portfolio_weighting)(sys).ffill()
            weights = weights.loc[sys.config.start:sys.config.end].ffill()       
            sys.data.cache('portfolio.weights', weights, 'system')
        
        return weights
        
    def get_portfolio_returns(self, capital):
        """ SYSTEM LEVEL
        
        Returns a DataFrame of Weighted Portfolio Percent Returns """
        sys = self.sys
        
        if self.iscached('portfolio.returns', 'system') is True:
            return sys.data.get('portfolio.returns', 'system')
        else:
            returns = self.calculate_raw_portfolio_returns(capital)        
            weights = self.calculate_portfolio_weights()
            result = (returns * weights)        
            sys.data.cache('portfolio.returns', result, 'system')
            
        return result
    
    def get_returns_by_group(self):
        """
        Returns a DataFrame of grouped returns
        """
        groups = utils.get_groups_from_config(self.sys)
        result = utils.get_returns_by_group(self.sys, groups)
        return result.add(1).cumprod()
        
    def get_instrument_returns(self, symbol, capital):
        """ 
        SYSTEM LEVEL

        Returns DataFrame of Percent Returns 
        """
        if self.iscached('returns.pct', symbol) is True:
            return self.sys.data.get('returns.pct', symbol)
        else:
            return self.get_instrument_returns_from_positions(symbol, capital)
                        
    def get_instrument_slippage(self, apply_slippage = True, trades = None, symbol = None):
        """ Returns Series of FX Adjusted Slippage """
        slippage = self.sys.data.slippage(symbol)
        return slippage * trades.abs() if apply_slippage is True else 0 * trades.abs()
        
    def get_instrument_returns_from_positions(self, symbol, capital):
        """
        SYSTEM LEVEL
        
        Returns DF of returns and percentage
        
        Cache returns in cash and percentage.
        """
        sys = self.sys
        
        positions = sys.positions.get_positions(symbol, capital)   
        trades = sys.positions.get_trades(symbol, capital)
        
        mtm = sys.data.contract_mtm_returns(symbol)
        ftm = sys.data.contract_ftm_returns(symbol)
        comm = sys.config.commission * trades
        
        slippage = self.get_instrument_slippage(sys.config.slippage, trades, symbol)

        posreturn = positions * mtm
        trdreturn = trades * ftm
        
        cashreturns = posreturn - trdreturn - slippage - comm
        pctreturns = cashreturns / sys.config.capital
        
        sys.data.cache('returns.cash', cashreturns, symbol)
        sys.data.cache('returns.pct', pctreturns, symbol)
                    
        return pctreturns

