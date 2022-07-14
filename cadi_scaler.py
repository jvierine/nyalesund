import cadi_reader as cr
import sys
import matplotlib.pyplot as plt
import h5py
import numpy as np
import os


def on_press(event, fig, ax, is_line, i_line, scale_vals, ghost):
    # Get mouse pointer data
    mx = event.xdata
    my = event.ydata
    
    # Draw vertical line and record foF2 data
    if event.key == '1':
        line = ax.axvline(mx, c = 'red', label = 'foF2')
        if not is_line[0]:
            plt.legend()
        else:
            ax.lines[i_line[0] + ghost].remove()
        
        for j in range(len(i_line)):
            if i_line[j] > i_line[0] and is_line[0]:
                i_line[j] -= 1
        is_line[0] = 1
        i_line[0] = sum(is_line) - 1
        foF2 = '%.3f' %mx
        scale_vals['foF2'] = float(foF2)
        fig.canvas.draw()
    
    # Draw horizontal line and record h'F2 data
    if event.key == '2':
        line = ax.axhline(my, c = 'orange', label = 'h\'F2')
        if not is_line[1]:
            plt.legend()
        else:
            ax.lines[i_line[1] + ghost].remove()
        
        for j in range(len(i_line)):
            if i_line[j] > i_line[1] and is_line[1]:
                i_line[j] -= 1
        is_line[1] = 1
        i_line[1] = sum(is_line) - 1
        hF2 = '%.1f' %my
        scale_vals['hF2'] = float(hF2)
        fig.canvas.draw()
        
    # Draw vertical line and record foE data
    if event.key == '3':
        line = ax.axvline(mx, c = 'blue', label = 'foE')
        if not is_line[2]:

            plt.legend()
        else:
            ax.lines[i_line[2] + ghost].remove()
            
        for j in range(len(i_line)):
            if i_line[j] > i_line[2] and is_line[2]:
                i_line[j] -= 1
        is_line[2] = 1
        i_line[2] = sum(is_line) - 1
        foE = '%.3f' %mx
        scale_vals['foE'] = float(foE)
        fig.canvas.draw()
    
    # Draw horizontal line and record h'E data
    if event.key == '4':
        line = ax.axhline(my, c = 'green', label = 'h\'E')
        if not is_line[3]:
            plt.legend()
        else:
            ax.lines[i_line[3] + ghost].remove()
            
        for j in range(len(i_line)):
            if i_line[j] > i_line[3] and is_line[3]:
                i_line[j] -= 1
        is_line[3] = 1
        i_line[3] = sum(is_line) - 1
        hE = '%.1f' %my
        scale_vals['hE'] = float(hE)
        fig.canvas.draw()

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
|  press 'q' to go to the next ionogram           |
|                                                 |
==================================================|
''')
    for i in ig['ionograms']:
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
        
        fig.canvas.mpl_connect('key_press_event', lambda event: on_press(event, fig, ax, is_line, i_line, scale_vals, ghostlines))
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
