import tensorflow as tf
import numpy as n
import matplotlib.pyplot as plt
import glob
import os
import imageio
import h5py
class random_shift_data(tf.keras.utils.Sequence):
    """
    generate data on the fly with random x shifts
    """
    def __init__(self,imgs,scaling,batch_size=64,N=5,x_width=100,shift=True,fr0=0,fr1=1.0,
                 prob=False):
        
        print(imgs.shape)
        idx=n.arange(imgs.shape[0])
        imgs0=imgs[int(fr0*len(idx)):int(fr1*len(idx)),:,:]
        self.imgs=imgs0

        self.scaling=scaling[int(fr0*len(idx)):int(fr1*len(idx)),:]
            
        self.batch_size=batch_size
        self.N=N
        self.x_width=x_width
        self.n_im=self.imgs.shape[0]
        self.shift=shift
        self.prob=prob
        
    def __len__(self):
        return(int(self.n_im*self.N/float(self.batch_size)))
    
    def __getitem__(self,idx):
        imi = n.array(n.mod(self.batch_size*idx + n.arange(self.batch_size,dtype=n.int),self.n_im),dtype=n.int)
        img_out=n.zeros([self.batch_size,self.imgs.shape[1],self.imgs.shape[2]],dtype=n.float32)
        scale_out=n.zeros([self.batch_size,self.scaling.shape[1]],dtype=n.float32)
        
        for i in range(self.batch_size):
            im0=n.copy(self.imgs[imi[i],:,:])
            xi=0.0
            if self.shift:
                xi=int(n.random.rand(1)*self.x_width-self.x_width/2.0)
                if self.scaling[imi[i],0]+xi < 0:
                    xi=0
#                plt.imshow(im0)
 #               plt.show()
                im0=n.roll(im0,xi,axis=1)
  #              plt.imshow(im0)
   #             plt.show()
            img_out[i,:,:]=im0
            
            # shift frequencies only if there is a frequency!
            if not self.prob:
                # f
                scale_out[i,0]=self.scaling[imi[i],0]+xi
                # h
                scale_out[i,1]=self.scaling[imi[i],1]
            else:
                scale_out[i,:]=self.scaling[imi[i],:]
                    
        img_out.shape=(img_out.shape[0],img_out.shape[1],img_out.shape[2],1)
        return(img_out,scale_out)


    
def get_images(dirname="./sod_ski",region="all",prob=False):
    fl=glob.glob("%s/iono*.png"%(dirname))
    fl.sort()
    n.random.seed(42)
    n.random.shuffle(fl)
#    print(len(fl))
    imgs=[]
    scalings=[]
    for f in fl:
        par_fname="%s.h5"%(f)
        if os.path.exists(par_fname):
            # we have scaled this manually
            h=h5py.File(par_fname,"r")
            s0=n.array([h["muf"].value,h["mue"].value,h["hmf"].value,h["he"].value],dtype=n.float32)
            img=n.array(imageio.imread(f),dtype=n.float32)/255.0
            
            ok=True
            if region == "f":
                if s0[0] < 1.0 or s0[2] < 1.0:
                    ok=False
                s=n.array([s0[0],s0[2]],dtype=n.float32)
            elif region == "e":
                if s0[1] < 1.0 or s0[3]< 1.0:
                    ok=False
                s=n.array([s0[1],s0[3]],dtype=n.float32)
                
            if prob:
                # only okay if E or F region is present in labels.
                # otherwise, we shouldn't train with this image, as the network will be confused
                ok=True
                s=n.zeros(2)
                # only hf or fo2
                if s0[1] > 1.0 and s0[3] < 1.0:
                    ok=False
                if s0[1] < 1.0 and s0[3] > 1.0:
                    ok=False

                # only hf or fo2
                if s0[0] < 1.0 and s0[2] > 1.0:
                    ok=False
                if s0[0] > 1.0 and s0[2] < 1.0:
                    ok=False
                    
                # both he and fe
                if s0[1] > 1.0 and s0[3] > 1.0:
                    # we have an e-region
                    ok=True
                    s[1]=1.0

                # both hf and fe
                if s0[0] > 1.0 and s0[2] > 1.0:
                    # we have an f-region
                    ok=True
                    s[0]=1.0
                    
            if ok:
                scalings.append(s)
                imgs.append(img)
                
            h.close()
    return(n.array(imgs),n.array(scalings))

def get_ionogram_data(dirname="./sod_ski",bs=64,N=10,x_width=50,shift=True,fr0=0.0,fr1=1.0,
                      prob=False,
                      region="all"):
    im,sc=get_images(dirname=dirname,region=region,prob=prob)
    n_images=im.shape[0]
    print("Total number of images %d"%(n_images))
    return(random_shift_data(im,sc,batch_size=bs,N=N,x_width=x_width,shift=shift,fr0=fr0,fr1=fr1,prob=prob))

if __name__ == "__main__":
    d=get_ionogram_data()
    b=d[0]
    imgs,scalings=get_images()
    for i in range(imgs.shape[0]):
        plt.imshow(imgs[i,:,:])
        plt.axhline(scalings[i,2])
        plt.axhline(scalings[i,3])
        plt.axvline(scalings[i,0])
        plt.axvline(scalings[i,1])
        plt.show()
            
        
    
