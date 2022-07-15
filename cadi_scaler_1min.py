import cadi_reader as cr
import cadi_scaler as cs
import sys
import matplotlib.pyplot as plt
import h5py
import numpy as np
import os




def plot_ionograms(ig):
    print('''
===================================================
|        Manual ionogram scaling program          |
|                                                 |
|  Hover the mouse pointer over the respective    |
|   values and press these buttons to scale:      |
|                                                 |
|  press '1' for foF2                             |
|  press '2' for h\'F2                             |
|  press '3' for foE                              |
|  press '4' for h\'E                              |
|  press 'q' to quit and save                     |
|                                                 |
==================================================|
''')
    i = ig['ionograms'][int(sys.argv[2])]
    fig, ax = plt.subplots(figsize = (15, 12))
    
    ### Draw faded "ghost" lines from previous scaled minute to see development
    ghostlines = 0
    color = ['red', 'orange', 'blue', 'green']
    pmname = cr.unix2cadi(i['unix_time'] - 60) + '.h5'
    if os.path.exists(pmname):
        with h5py.File(pmname, 'r') as f:
            params = [f['foF2'][()], f['h\'F2'][()], f['foE'][()], f['h\'E'][()]]
        for j, v in enumerate(params):
            if j % 2 == 0 and float(v) < 900:
                line = ax.axvline(float(v), c = color[j])
                line.set_alpha(0.2)
                ghostlines += 1
                fig.canvas.draw()
            elif j % 2 == 1 and float(v) < 9000:
                line = ax.axhline(float(v), c = color[j])
                line.set_alpha(0.2)
                ghostlines += 1
                fig.canvas.draw()
                
    
    cm = ax.pcolormesh(ig['freqs']/1e6,ig['virtual_heights'],i['ionogram_image'].T,cmap='gray',vmin=0,vmax=1.0)
    ax.set_title('%d %s %s'%(i['ionogram_idx'],cr.unix2datestr(i['unix_time']),ig['ascii_datetime']))
    fname= cr.unix2cadi(i['unix_time'])
    ax.set_xlabel('Frequency (MHz)')
    ax.set_ylabel('Height (km)')        
    cb = plt.colorbar(cm)
    
    is_line = [0, 0, 0, 0]
    i_line = [0, 0, 0, 0]
    scale_vals = {'foF2': 999.999,
                  'hF2': 9999.9,
                  'foE':  999.999,
                  'hE':  9999.9
                  }
    
    fig.canvas.mpl_connect('key_press_event', lambda event: cs.on_press(event, fig, ax, is_line, i_line, scale_vals, ghostlines))
    plt.show()
    
    #remove ghostlines before saving figure since they are only used to simplify scaling
    for j in range(ghostlines):
        ax.lines[0].remove()
    
    fig.savefig('%s.png'%(fname))
    plt.close()
    #plt.clf()
    
    h5name = '%s.h5'%(fname)
    if os.path.exists(h5name):
        ho=h5py.File(h5name,'r+')
    else:
        ho=h5py.File(h5name,'a')

    if 'ionogram_image' in ho.keys():
        del ho['ionogram_image']
    ho['ionogram_image']=np.array(i['ionogram_image'],dtype=np.float16)

    if 'freqs' in ho.keys():
        del ho['freqs']
    ho['freqs']=ig['freqs']
    
    if 'virtual_heights' in ho.keys():
        del ho['virtual_heights']
    ho['virtual_heights']=ig['virtual_heights']
    
    if 'foF2' in ho.keys():
        del ho['foF2']            
    ho['foF2']=scale_vals['foF2']
    
    if 'h\'F2' in ho.keys():
        del ho['h\'F2']            
    ho['h\'F2']=scale_vals['hF2']
    
    if 'foE' in ho.keys():
        del ho['foE']            
    ho['foE']=scale_vals['foE']
    
    if 'h\'E' in ho.keys():
        del ho['h\'E']            
    ho['h\'E']=scale_vals['hE']
    
    ho.close()
    print('saved %s'%(h5name))
    
if __name__ == '__main__':
    res=cr.read_ionograms(sys.argv[1])
    plot_ionograms(res)
