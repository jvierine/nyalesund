import h5py
import os
import sys

def readh5(fname):
    if os.path.exists(fname):
        with h5py.File(fname,'r') as f:
            keys = list(f.keys())
            for i, v in enumerate(keys):
                print(v + ':\n' + str(f[v][()]) + '\n')
    
if __name__ == '__main__':
    fname = sys.argv[1]
    readh5(fname)
