import numpy as np
import matplotlib.pyplot as plt
import h5py
import os
import sys
import glob

def h5(fpath):
    fl = glob.glob(fpath[:-7] + '*.h5')
    fl.sort()
    t = np.empty(0)
    foF2 = np.empty(0)
    hF2 = np.empty(0)
    foE = np.empty(0)
    hE = np.empty(0)
    if os.path.exists(fpath):
        for p in fl:
            t = np.append(t, 60 * int(p[-7:-5]) + int(p[-5:-3]))
            with h5py.File(p,'r') as f:
                v = [f['foF2'][()], f['h\'F2'][()], f['foE'][()], f['h\'E'][()]]
                if v[0] > 900:
                    v[0] = float('nan')
                foF2 = np.append(foF2, v[0])
                if v[1] > 9000:
                    v[1] = float('nan')
                hF2 = np.append(hF2, v[1])
                if v[2] > 900:
                    v[2] = float('nan')
                foE = np.append(foE, v[2])
                if v[3] > 9000:
                    v[3] = float('nan')
                hE = np.append(hE, v[3])
    
    return t, [foF2, hF2, foE, hE]
            
if __name__ == '__main__':
    t, v = h5(sys.argv[1])
    fig, axs = plt.subplots(2, 2, figsize=(15, 12))
    
    axs[0, 0].set_xticks([0, 240, 480, 720, 960, 1200, 1439])
    axs[0, 0].set_xticklabels([0, 4, 8, 12, 16, 20, 24])
    axs[0, 0].set_xlim(0, 1439)
    axs[0, 0].set_ylim(0, np.nanmax(v[0]))
    axs[0, 0].set_title('foF2')
    axs[0, 0].set_xlabel('Time (UT)')
    axs[0, 0].set_ylabel('Frequency (MHz)')
    axs[0, 0].plot(t, v[0])
    axs[0, 1].set_xticks([0, 240, 480, 720, 960, 1200, 1439])
    axs[0, 1].set_xticklabels([0, 4, 8, 12, 16, 20, 24])
    axs[0, 1].set_xlim(0, 1439)
    axs[0, 1].set_ylim(0, np.nanmax(v[1]))
    axs[0, 1].set_title('h\'F2')
    axs[0, 1].set_xlabel('Time (UT)')
    axs[0, 1].set_ylabel('Virtual height (km)')
    axs[0, 1].plot(t, v[1])
    axs[1, 0].set_xticks([0, 240, 480, 720, 960, 1200, 1439])
    axs[1, 0].set_xticklabels([0, 4, 8, 12, 16, 20, 24])
    axs[1, 0].set_xlim(0, 1439)
    axs[1, 0].set_ylim(0, np.nanmax(v[2]))
    axs[1, 0].set_title('foE')
    axs[1, 0].set_xlabel('Time (UT)')
    axs[1, 0].set_ylabel('Frequency (MHz)')
    axs[1, 0].plot(t, v[2])
    axs[1, 1].set_xticks([0, 240, 480, 720, 960, 1200, 1439])
    axs[1, 1].set_xticklabels([0, 4, 8, 12, 16, 20, 24])
    axs[1, 1].set_xlim(0, 1439)
    axs[1, 1].set_ylim(0, np.nanmax(v[3]))
    axs[1, 1].set_title('h\'E')
    axs[1, 1].set_xlabel('Time (UT)')
    axs[1, 1].set_ylabel('Virtual height (km)')
    axs[1, 1].plot(t, v[3])
    plt.show()
