#reporting
from systems.core.modules import BaseModule
import systems.core.performance as pstats

class Reporting():
    def __init__(self, system = None):
        BaseModule.__init__(self, system, 'reporting')

    def get_performance_stats(self):        
        stats = tuple(getattr(pstats, stat)(self.sys)[0] for stat in self.sys.config.performance_stats)        
        print('\n', stats)        
        return stats
    
        