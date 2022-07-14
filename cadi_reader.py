#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 09:36:04 2021

@author: ase049
"""
###
### Make a cadi ionogram with only near zenith angles used. Use a 0..1 colorscale to
### visualize polarization. 0 corresponds to pure O-mode and 1 corresponds to pure X-mode. 
###

### Introductory imports and constants

import sys
import struct
import datetime
from time import strptime
import numpy as np
import matplotlib.pyplot as plt
import h5py
import os
import scipy.constants as sc


def read_ionograms(filename,
                   zenith_angle_limit=20.0, # don't include zenith angles larger than this
                   dheight = 3.0,  # not defined in data file
                   antenna_separation=35.36):


    max_ntimes = 256
    max_ndopbins = 300000
    
    f = open(filename, "rb")    

    # do some mumbojumbo with eof file? 
    f.seek(-1,2)     # go to the file end.
    eof = f.tell()   # get the end of file location
    f.seek(0,0)      # go back to file beginning
    
    #############################################################################
    ### 1) Read header information as described in the documentation p. 26-27
    #############################################################################
    
    try:
        site = f.read(3).decode("utf-8")
        ascii_datetime = f.read(22).decode("utf-8")
        filetype = f.read(1).decode("utf-8")
        nfreqs = struct.unpack("<H", f.read(2))[0]
        ndops = struct.unpack("<B", f.read(1))[0]
        minheight = struct.unpack("<H", f.read(2))[0]
        maxheight = struct.unpack("<H", f.read(2))[0]
        pps = struct.unpack("<B", f.read(1))[0]
        npulses_avgd = struct.unpack("<B", f.read(1))[0]
        base_thr100 = struct.unpack("<H", f.read(2))[0]
        noise_thr100 = struct.unpack("<H", f.read(2))[0]
        min_dop_forsave = struct.unpack("<B", f.read(1))[0]
        dtime = struct.unpack("<H", f.read(2))[0]
        gain_control = f.read(1).decode("utf-8")
        sig_process = f.read(1).decode("utf-8")
        noofreceivers = struct.unpack("<B", f.read(1))[0]
        spares = f.read(11).decode("utf-8")
        
        month = ascii_datetime[1:4]
        day = int(ascii_datetime[5:7])
        hour = int(ascii_datetime[8:10])
        minute = int(ascii_datetime[11:13])
        sec = int(ascii_datetime[14:16])
        year = int(ascii_datetime[17:21])
        
        month_number = strptime(month, '%b').tm_mon
        mydate = datetime.date(year, month_number, day)
        jd = mydate.toordinal() + 1721424.5
        jd0jd = datetime.date(1986, 1, 1)
        jd0 = jd0jd.toordinal() + 1721424.5
        
        time_header = (jd - jd0) * 86400 + hour * 3600 + minute * 60 + sec
        time_hour = 3600 * (time_header / 3600)

        # unix seconds at the beginning of the file
        dt0=datetime.date(year, month_number, day)
        unix_timestamp = (dt0 - datetime.date(1970, 1, 1)).total_seconds() + hour*3600 

        #############################################################################
        ### 2) Read all frequencies used
        #############################################################################
        
        # check that every ionogram has the same number of frequencies (should be 95 for nya)
        freqs = np.array([struct.unpack("<f", f.read(4))[0] for i in range(nfreqs)])
        
    
        if filetype == 'I':
            max_nfrebins = nfreqs
        else:
            max_nfrebins = min(max_ntimes * nfreqs, max_ndopbins)
            
            
            
        #############################################################################
        ### 3) Read rawdata
        #############################################################################
        #
        # Antenna channels
        # antennas 1 and 3 are aligned in polarization
        # antennas 0 and 2 are aligned in polarization
        #
                
        nheights = int(maxheight / dheight + 1)
        # an array containing heights
        vheights = np.arange(nheights)*dheight
        
        times = []
        frebins = []
        frebins_x = []
        frebins_gain_flag = []
        frebins_noise_flag = []
        frebins_noise_power10 = []
        time_min = 0
        time_sec = 0
        timex = -1
        freqx = nfreqs - 1
        dopbinx = -1
        frebinx = -1
        iq_bytes = np.zeros(noofreceivers,dtype=np.complex64)
        dopbin_x_timex = []
        dopbin_x_freqx = []
        dopbin_x_hflag = []
        dopbin_x_dop_flag = []
        dopbin_iq = []
        hflag = 0
        
        time_min = struct.unpack("<B", f.read(1))[0]

        unix_times=[]
        
        # as far as I can tell, this is hard coded so that there
        # is one ionogram every minute!?!
        while time_min != 255:
            print("time_min %d"%(time_min))
            time_sec = struct.unpack("<B", f.read(1))[0]
            flag = struct.unpack("<B", f.read(1))[0]  # gainflag
            # count the number of ionograms encountered in file
            timex += 1
            times.append(time_hour + 60 * time_min + time_sec)
            
            unix_times.append(unix_timestamp + 60 * time_min + time_sec)
            for freqx in range(nfreqs):
                print(freqx)
                noise_flag = struct.unpack("<B", f.read(1))[0]  # noiseflag
                noise_power10 = struct.unpack("<H", f.read(2))[0]
                frebinx += 1
                frebins_gain_flag.append(flag)
                frebins_noise_flag.append(noise_flag)
                frebins_noise_power10.append(noise_power10)
                flag = struct.unpack("<B", f.read(1))[0]
                while flag < 224:
                    ndops_oneh = struct.unpack("<B", f.read(1))[0]
                    hflag = flag
                    if ndops_oneh >= 128:
                        ndops_oneh = ndops_oneh - 128
                        hflag = hflag + 200
                    for dopx in range(ndops_oneh):
                        dop_flag = struct.unpack("<B", f.read(1))[0]
                        for rec in range(noofreceivers):
                            real_part=struct.unpack("<B", f.read(1))[0]
                            if real_part > 127:
                                real_part = real_part-256
                            imag_part=struct.unpack("<B", f.read(1))[0]
                            if imag_part > 127:
                                imag_part = imag_part-256
                            iq_bytes[rec] = real_part + imag_part*1j
                        dopbinx += 1
                        dopbin_iq.append(np.copy(iq_bytes))
                        dopbin_x_timex.append(timex)
                        # this list stores the frequency array index
                        dopbin_x_freqx.append(freqx)
                        # this list stores the virtual height array index
                        dopbin_x_hflag.append(hflag)
                        
                        ### Decode Doppler bin flags
                        if dop_flag < int(ndops / 2):
                            dop_flag = dop_flag + int(ndops / 2)
                        else:
                            dop_flag = dop_flag - int(ndops / 2)
                            
                        dopbin_x_dop_flag.append(dop_flag)

                    flag = struct.unpack("<B", f.read(1))[0]  # next hflag/gainflag/FF
            
            time_min = flag
            if ((f.tell() - 1) != eof):
                time_min = struct.unpack("<B", f.read(1))[0]  # next record
    except:
        print("error with reading file. add stack trace here!")

    f.close()

    # these ionogram indices of all the echoes in the file
    ionogram_indices = np.array(dopbin_x_timex)

    # unix timestamps of the ionograms in the file
    unix_times=np.array(unix_times)

    # convert to array of complex baseband signals
    dopbin_iq=np.vstack(dopbin_iq)

    # these are all the unique ionogram indices in file (should be 0..59)
    unique_ionogram_indices = np.unique(ionogram_indices)
    n_ionograms=len(ionogram_indices)
    
    print("found %d ionograms"%(n_ionograms))

    freq_idx=np.array(dopbin_x_freqx,dtype=np.uint64)
    height_idx=np.array(dopbin_x_hflag,dtype=np.uint64)

    # lambda is wavelength. note that this varies with frequency bin
    lamda = sc.c/freqs[freq_idx]

    # two different ways to calculate zenith angle
    # I think two of the antennas are rotated 180 degrees, giving a phase shift of 180 deg in phase, hence multiplication by -1
    zenith_angle02 = 180.0*np.arcsin(lamda*np.angle(-1*dopbin_iq[:,0]*np.conj(dopbin_iq[:,2]))/(2.0*np.pi*antenna_separation))/np.pi
    zenith_angle13 = 180.0*np.arcsin(lamda*np.angle(-1*dopbin_iq[:,1]*np.conj(dopbin_iq[:,3]))/(2.0*np.pi*antenna_separation))/np.pi
    
    ionograms = []
    
    for i,this_ionogram_idx in enumerate(unique_ionogram_indices):

        # these ionogram echoes are at the same time
        this_idx = np.where( (ionogram_indices == this_ionogram_idx) & (zenith_angle02 < zenith_angle_limit) & (zenith_angle13 < zenith_angle_limit) )[0]

        complex_ionogram = np.zeros([nfreqs,nheights],dtype=np.complex64)
        
        # average phasors
        for tid in this_idx:
            # use two different combinations of cross-polarized antennas to calculate the cross-polarization phase difference
            # which provides us information about circular polarization (+/- pi/2 for left and right hand circular polarization)
            # O-mode will correspond to phase difference -pi/2 and X-mode to pi/2
            complex_ionogram[freq_idx[tid],height_idx[tid]]+= ( dopbin_iq[tid,0]*np.conj(dopbin_iq[tid,1]) + dopbin_iq[tid,0]*np.conj(dopbin_iq[tid,1]) )

        complex_ionogram[np.abs(complex_ionogram)<1]=1.0

       # custom metric convert O and X mode into a black and white image (0..1 scale)            
        omode_phasor=np.exp(-1j*np.pi/2.0)

        # The distance of the cross polarization phase difference from the O-mode expected phase difference, normalized to 0..1
        omode_phdiff=np.abs(np.angle(complex_ionogram*np.conj(omode_phasor)))/np.pi

        # use 16-bit float to save disk space
        ionogram_img = np.array(omode_phdiff,dtype=np.float16)
        
        ionograms.append({"ionogram_image":ionogram_img,
                          "ionogram_idx":this_ionogram_idx,
                          "unix_time":unix_times[i]}
                         )

    return({"freqs":freqs,
            "site":site,
            "virtual_heights":vheights,
            "ionograms":ionograms,
            "ascii_datetime":ascii_datetime,
            "unix_times":unix_times
            })

def unix2date(x):
    return datetime.datetime.utcfromtimestamp(x)

def dirname2unix(dirn):
    r = re.search("(....)-(..)-(..)T(..)-(..)-(..)",dirn)
    return(date2unix(int(r.group(1)),int(r.group(2)),int(r.group(3)),int(r.group(4)),int(r.group(5)),int(r.group(6))))

def unix2datestr(x):
    d0=np.floor(x/60.0)
    frac=x-d0*60.0
    stri=unix2date(x).strftime('%Y-%m-%d %H:%M:')
    return("%s%02.2f"%(stri,frac))
  
def unix2cadi(x):
    date = re.split('\s|:|-', unix2datestr(x))
    m2c = chr(64 + int(date[1]))
    cadi = date[0][3] + m2c + date[2] + date[3] + date[4]
    return(cadi)

def plot_ionograms(ig):
    #
    # TODO: read dates and times of ionograms and write these to files
    # add ionogram scaling here.
    #
    for i in ig["ionograms"]:
        plt.pcolormesh(ig["freqs"]/1e6,ig["virtual_heights"],i["ionogram_image"].T,cmap="gray",vmin=0,vmax=1.0)
        
        plt.title("%d %s %s"%(i["ionogram_idx"],unix2datestr(i["unix_time"]),ig["ascii_datetime"]))
        fname="ionogram_%d.h5"%(i["ionogram_idx"])
        if os.path.exists(fname):
            ho=h5py.File(fname,"r+")
        else:
            ho=h5py.File(fname,"a")

        if "ionogram_image" in ho.keys():
            print("deleting")
            del ho["ionogram_image"]
        print(ho.keys())
        ho["ionogram_image"]=np.array(i["ionogram_image"],dtype=np.float16)

        if "freqs" in ho.keys():
            del ho["freqs"]
        ho["freqs"]=ig["freqs"]
        
        if "virtual_heights" in ho.keys():
            del ho["virtual_heights"]
        ho["virtual_heights"]=ig["virtual_heights"]
        
        if "fof2" in ho.keys():
            del ho["fof2"]            
        ho["fof2"]=1.0

        ho.close()
        print("saved %s"%(fname))
        
        plt.xlabel("Frequency (MHz)")
        plt.ylabel("Height (km)")        
        plt.colorbar()
        plt.savefig("%s.png"%(fname))
        plt.close()
        plt.clf()


        
if __name__ == "__main__":
    # test case
    res=read_ionograms(sys.argv[1])
    plot_ionograms(res)



