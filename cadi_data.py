import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import imageio
import h5py

class random_shift_data(tf.keras.utils.Sequence):
    """
    generate data on the fly with random x shifts
    """
    def __init__(self, imgs, scaling, batch_size=64, x_width=100, fr0=0, fr1=1.0, prob=False):
        print(imgs.shape)
        idx=np.arange(imgs.shape[0])
        imgs0=imgs[int(fr0*len(idx)):int(fr1*len(idx)),:,:]
        self.imgs=imgs0

        self.scaling=scaling[int(fr0*len(idx)):int(fr1*len(idx)),:]
            
        self.batch_size=batch_size
        self.x_width=x_width
        self.n_im=self.imgs.shape[0]
        self.prob=prob
        
    def __len__(self):
        return(int(self.n_im/float(self.batch_size)))
    
    def __getitem__(self,idx):
        imi = np.array(np.mod(self.batch_size*idx + np.arange(self.batch_size,dtype=np.int),self.n_im),dtype=np.int)
        img_out=np.zeros([self.batch_size,self.imgs.shape[1],self.imgs.shape[2]],dtype=np.float32)
        scale_out=np.zeros([self.batch_size,self.scaling.shape[1]],dtype=np.float32)
        
        for i in range(self.batch_size):
            im0=np.copy(self.imgs[imi[i],:,:])
            img_out[i,:,:]=im0
            
            # shift frequencies only if there is a frequency!
            if not self.prob:
                # f
                scale_out[i,0]=self.scaling[imi[i],0]
                # h
                scale_out[i,1]=self.scaling[imi[i],1]
            else:
                scale_out[i,:]=self.scaling[imi[i],:]
                    
        img_out.shape=(img_out.shape[0],img_out.shape[1],img_out.shape[2],1)
        return(img_out,scale_out)


    
def get_images(dirname="./scaledData",region="f",prob=False):
    fl = glob.glob(os.path.join(dirname, '*/*/*.h5'))
    fl.sort()
    np.random.seed(42)
    np.random.shuffle(fl)
#    print(len(fl))
    imgs=[]
    scalings=[]
    for f in fl:
        if os.path.exists(f):
            # we have scaled this manually
            h=h5py.File(f,"r")
            s0=np.array([h["foF2"][()], h["foE"][()], h["h\'F2"][()], h["h\'E"][()]], dtype=np.float32)
            img=h['ionogram_image'][()]
            
            ok=True
            if region == "f":
                if s0[0] < 1.0 or s0[2] < 1.0:
                    ok=False
                s=np.array([s0[0], s0[2]], dtype=np.float32)
            elif region == "e":
                if s0[1] < 1.0 or s0[3]< 1.0:
                    ok=False
                s=np.array([s0[1], s0[3]], dtype=np.float32)
                
            if prob:
                # only okay if E or F region is present in labels.
                # otherwise, we shouldn't train with this image, as the network will be confused
                ok=True
                s=np.zeros(2)
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
    return(np.array(imgs), np.array(scalings))

def get_ionogram_data(dirname="./scaledData", bs=64, x_width=50, fr0=0.0, fr1=1.0, prob=False, region="f"):
    im, sc = get_images(dirname=dirname, region=region, prob=prob)
    n_images = im.shape[0]
    print("Total number of images %d" % (n_images))
    return(random_shift_data(im, sc, batch_size=bs, x_width=x_width, fr0=fr0, fr1=fr1, prob=prob))

if __name__ == "__main__":
    d=get_ionogram_data()
    b=d[0]
    imgs,scalings=get_images()
    for i in range(imgs.shape[0]):
        plt.imshow(imgs[i,:,:].T, origin = 'lower')
        #plt.axhline(scalings[i,2])
        #plt.axhline(scalings[i,3])
        #plt.axvline(scalings[i,0])
        #plt.axvline(scalings[i,1])
        plt.show()
