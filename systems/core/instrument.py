#system
from systems.core.modules import load_futures_config
from systems.core.datastore import DataStore
from systems.core.utils import profile

class TradingSystem():
    def __init__(self, name):
        pass
    
class Instrument():
    def __init__(self, name):
        self.config = load_futures_config(name)
        
        self.name = name
    
        profile(self.load_systems)
        
    def load_systems(self):
        self.data = DataStore(self)