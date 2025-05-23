"""This script will prompt you to move the H2 nozzle in a regular set of moves to create a map of the plume from the electrolysis cell.
The scan is lateral (x) and vertical (y) and the user will input the increments and starting position"""
from matplotlib import pyplot as plt
import TimeTagger
import numpy as np


#functions live here
def get_delay_and_jitter(x, y):
    # Helper method to calculate the mean time difference of a histogram and the standard deviation.
    mean = np.average(x, weights=y)
    std = np.sqrt(np.average((x-mean)**2, weights=y))
    return mean, std
def calc_h2(n2data,h2data):
    # ratios N2 and H2 raman counts and applies correction to get H2 in ppm
    H2_ramanx=7.07E-30 #H2 Raman Xsection
    N2_ramanx=2.68E-30 #N2 Raman Xsection
    N2_concentration=0.78 # N2 fraction of atmosphere

    h2conc = np.divide(h2data,n2data)*N2_ramanx*N2_concentration/H2_ramanx
    return h2conc

# don't change these if doing multiple runs
tstart = 2990 #int(input('first time bin to keep - 1510 for current setup:  '))
tend = 3050 #int(input('last time bin - 1600 for current setup:  '))
tinc = 50 #float(input('bin size in timetagger in ps:  '))
nbins = 3200 #int(input('number of time bins for correlation (2000):  '))
# tinc distance is 1/2 twt times speed of light
zinc = 0.150*tinc

resume=input('resume from previous runfile (paused_10mrun.npz) ?(Y/N)')    
if resume == 'Y':
    prev_state=np.load('paused_10mrun.npz')
    yvec=prev_state['yvec']
    xvec=prev_state['xvec']
    h23d=prev_state['h23d']
    h2raw=prev_state['h2raw']
    n2raw=prev_state['n2raw']
    
    #yvec = yvec, xvec = xvec, h23d = h23d, h2raw = h2raw, n2raw = n2raw, binwidth = binwidth, n_bins = n_bins)
else:
# setup the experiment
    xs = float(input('starting x position offset from the nozzle in mm? NB software will assume symmetry around nozzle at 0:   '))
    xinc = float(input('x increment between measurements in mm:  '))
    ys = float(input('starting height below laser spot centre in mm:  '))
    yinc = float(input('y increment between rows of measurement in mm:  '))
    yf = float(input('maximum distance below laser nozzle will be placed:  '))


# setup acquistion coordinate array
    nx = int(np.ceil(xs/xinc)*2)+1
    ny = int(np.ceil(yf-ys)/yinc)+1
    nt = int(np.ceil(tend - tstart + 1))
    h23d = np.zeros((nx,ny,nbins))# ratio data
    h2raw = np.zeros((nx,ny,nbins))
    n2raw = np.zeros((nx,ny,nbins))

    xvec=np.linspace(-1*xs, xs , num = nx)
    yvec=np.linspace(ys,yf,num=ny)
#    tvec=np.linspace(tstart,tend,num=nt)
#    zvec=np.linspace(0,zinc*nt,num=nt)

# initialise timetagger
tagger = TimeTagger.createTimeTagger()
tagger.setTriggerLevel(channel=-1, voltage=-0.65)
tagger.setTriggerLevel(channel=2, voltage=0.75)
tagger.setTriggerLevel(channel=3, voltage=0.75)
# use conditional filtering to minimise data bottleneck
tagger.setConditionalFilter(trigger=[2, 3], filtered=[1], hardwareDelayCompensation = True)
tagger.setDelayHardware(1, -10000)
# create synchronised measurement object
synchronized = TimeTagger.SynchronizedMeasurements(tagger)
sync_tagger_proxy = synchronized.getTagger()

correlation12 = TimeTagger.Correlation(tagger=sync_tagger_proxy,
                                     channel_1=2,
                                     channel_2=1,
                                     binwidth=50,
                                     n_bins=nbins)
correlation13 = TimeTagger.Correlation(tagger=sync_tagger_proxy,
                                     channel_1=3,
                                     channel_2=1,
                                     binwidth=50,
                                     n_bins=nbins)

# take background reading for N2. Do a few runs and average them
# number of stacks for background signal
#nstack = 3
#resp=input('run background calibration?(Y/N)')
#if resp == 'Y':
    
##initialise background array
#    bgN2array=np.zeros((nstack,nbins))
#    bgH2array=np.zeros((nstack,nbins))
#    for k in range(nstack):
#        print('background calibration run number ',k+1,' of ',nstack)
#        synchronized.startFor(int(60E12))
#        synchronized.waitUntilFinished()
#        bgN2array[k,:]=correlation13.getData()
#        bgH2array[k,:]=correlation12.getData()
#        plt.figure()
#        plt.plot(bgN2array[k,:], label = "raw N2 channel")
#        plt.plot(bgH2array[k,:], label = "raw H2 channel")
#        plt.show()
#    np.savez('bg_cals.npz',bgN2array=bgN2array,bgH2array=bgH2array)
#
#else:
#    print('loading previous cals')
#    prevcals=np.load('bg_cals.npz')
#    bgN2array=prevcals['bgN2array']
#    bgH2array=prevcals['bgH2array']
#        
#print('averaging background ratios')
## create temp storage
#temp_bg=bgN2array
#for k in range(nstack):
#   temp_bg[k,:]=calc_h2(bgN2array[k,:],bgH2array[k,:])  
#   
#gdata= np.mean(temp_bg, axis = 0)
#gsd = np.std(temp_bg, axis = 0)
#plt.figure()

#plt.plot(bgdata[tstart:tend], label="mean bg H2")
#plt.xlabel('bin')
#plt.ylabel('counts')
#plt.plot(bgsd[tstart:tend], label="std")
#plt.legend()
#plt.title('background raw counts')
#plt.show()
    

# use break to exit loop and continue to jump past previously acquired data.    
    
    
# start run
pauseflag='n'
m=0
for j in yvec:
    n=0
    for i in xvec:
        # test for previous data
        if max(n2raw[n,m,:]) != 0. :
            pass
        else:
            print('position nozzle at ',i,' x ',j,' y')
            pauseflag=input('enter any key when finished moving nozzle or p to pause acquisition')
            if pauseflag == 'p':
                np.savez('paused_10mrun.npz',yvec = yvec, xvec = xvec, h23d = h23d, h2raw = h2raw, n2raw = n2raw)
                break
            else :                  
                print('running measurement for 1 min')
                synchronized.startFor(capture_duration=int(60E12))
                synchronized.waitUntilFinished()
                data12=correlation12.getData()
                data13=correlation13.getData()
                h2raw[n,m,:]=data12
                n2raw[n,m,:]=data13
                # remove bg H2
                      
                temp=calc_h2(data13,data12) #-bgdata
                hvec=temp[tstart-1:tend]
                print('done')
                plt.figure()
                plt.plot(data12*10, label=" H2raw")
                plt.plot(data13, label= "N2raw")
                plt.xlabel('timebins')
                plt.ylabel('rawdata')
                plt.legend()
                plt.title(' N2 and H2 channels')
                plt.show()
                # assign data
                h23d[n,m,:]=temp
                #hvec[:2900]=0
                #20hvec[3150:]=0
                plt.figure()
                plt.plot(hvec, label="H2 molar fraction")
                plt.xlabel('channel')
                plt.show()
        n=n+1
        print('\a') # beep
    if pauseflag == 'p':
        break
    m=m+1

# save 3D data 
np.savez('H2vol10m.npz', h23d = h23d, h2raw = h2raw, n2raw = n2raw)
#text_file = '3dh2data.txt'
#np.savetxt(text_file,h23d, delimiter = ' ')
# Close the connection to the Time Tagger.
TimeTagger.freeTimeTagger(tagger)


