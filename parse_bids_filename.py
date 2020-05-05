# Script adapted from:
# https://github.com/mne-tools/mne-bids/blob/master/mne_bids/utils.py
import os, sys

fname = sys.argv[1]
return_key = sys.argv[2]

"""Get dict from BIDS fname."""
keys = ['sub', 'ses', 'task', 'acq', 'run', 'proc', 'run', 'space',
        'recording', 'kind', 'desc']
params = {key: None for key in keys}
entities = fname.split('_')
idx_key = 0
for entity in entities:
    try: 
        assert '-' in entity
        key, value = entity.split('-',1)
        if key not in keys:
            raise KeyError('Unexpected entity ''%s'' found in filename ''%s'''
                           % (entity, fname))
        if keys.index(key) < idx_key:
            raise ValueError('Entities in filename not ordered correctly.'
                             ' "%s" should have occured earlier in the '
                             'filename "%s"' % (key, fname))
        idx_key = keys.index(key)
        params[key] = value
        if key == return_key: 
                print( value )
    except AssertionError: 
        pass
    except KeyError: 
        pass
    except Exception as e:
        pass
# return params
