#modules.py
from yaml import load
from attrdict import AttrDict

class BaseModule(object):
    def __init__(module, system = None, stage = None):
        
        module.stage = stage
        module.sys = system

    def iscached(self, itemname, instrument = 'system'):
        return True if itemname in self.sys.data._cache[instrument.upper()].keys() else False



def load_futures_config(name):
    return AttrDict(load(open('.\\futures\\' + name + '\\config.yaml', 'rb')))