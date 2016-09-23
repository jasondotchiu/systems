#ibutils
import pandas as pd
import numpy as np

DEFAULT_VALUE = np.nan

class NewDF(object):
    
    def __init__(self, *args):
        setattr(self, 'keynames', args)
        
        storage = { keyname: list() for keyname in self.keynames }
        
        setattr(self, 'storage', storage)
    
    def add_row(self, **kwargs):
        for keyname in self.storage.keys():
            if keyname in kwargs:
                self.storage[keyname].append(kwargs[keyname])
            else:
                self.storage[keyname].append(DEFAULT_VALUE)
    
    def to_pandas(self, indexname = None):
        if indexname is not None:
            data = self.storage
            index = self.storage[indexname]
            data.pop(indexname)
            return pd.DataFrame(data, index = index)
        else:
            return pd.DataFrame(self.storage)

    