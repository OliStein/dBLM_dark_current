'''Various Imports'''
import threading #Enables the threading.Timer function to time the execution
import numpy as np
import matplotlib.pyplot as plt
import visaTEST as pv  #Handles the GPIB communication
import time as tm  #Only used for sleep command and getting the timestamp
import pandas as pd  #Data frame for data management.
import keithley_func as kf


#Important global variable to halt processing.



def binarysearch(A, value, imax):
    imin = 0
    while imax >= imin:
        imid = int((imax+imin)/2)
        if A[imid] > value:
            imax = imid - 1
        elif A[imid] < value:
            imin = imid + 1
        else:
            break
    return imid

def cleverdiff(value, time):
    return np.append(np.diff(value) / np.diff(time), -0.5e-8) #introduces a non-important value, in the end,
                # to make sure the length matches up. 

class icBLM:
    def __init__(self):
        #Generate various arrays for measurement.
        self.outArray = pd.DataFrame({'Q':[1e-8],
                                 't':[1]},#tm.time()]},
                                 columns = ['Q', 't'])
        
        self.TriggersPerMeasurement = 1
        self.SamplesPerTrigger = 300 #Shouldn't be changed.
        self.SamplesPerMeasurement = self.TriggersPerMeasurement*self.SamplesPerTrigger
        
        
        #Setup Keithley for measurement.
        rm = pv.ResourceManager()
        self.kt = rm.get_instrument('GPIB::24')
        self.kt.write('*IDN?')
        print '\n\n\n', self.kt.read(), 'is initiated - Prepare for vogon poetry!\n\n\n'
        self.kt.write('*rst')
        self.kt.write('*cls')
        #Setup system stuff
        self.kt.write('system:zcheck 0')
        self.kt.write('system:zcheck 1')
        self.kt.write('system:zcheck 0')
        self.kt.write('system:lsync:state 0')
        self.kt.write('sense:function \'charge\'')
        self.kt.write('sense:charge:range 2e-8')
        self.kt.write('sense:charge:nplc 0.01')
        self.kt.write('sense:charge:digits 7')
        self.kt.write('calculate:state 0')
        self.kt.write(':display:enable 0')
        self.kt.write(':charge:adischarge:state 1')
        self.kt.write(':charge:adischarge:level 1.0e-8')
        
        #Trigger setup:
        self.kt.write(':arm:layer1:source immediate')
        
        '''Sets the number of triggers per Measurement (nMeasurement)'''
        self.kt.write(':arm:layer2:count ' + str(self.TriggersPerMeasurement)) #The number is very important here!
        
        self.kt.write(':arm:layer2:source tlink')
        self.kt.write(':arm:layer2:tconfigure:asynchronous:iline 5') #Set the input
                                                            # line for the triglink
        
        '''Sets the number of samples per trigger'''
        self.kt.write(':trigger:count ' + str(self.SamplesPerTrigger))
        
        self.kt.write('trace:points ' + str(self.SamplesPerMeasurement))
        self.kt.write('trace:tstamp:format absolute')
        self.kt.write('system:tstamp:type relative')
        self.kt.write('trace:elements tstamp')
        self.kt.write('trace:feed:control next')
        tm.sleep(3) #COMPUTER DO SOMETHING!
        
        
filename = 'Measurement_icBLM'+str(int(tm.time()))
ic = icBLM()
xout = []
yout = []

### GENERATE PLOT
fig = plt.figure()
ax = fig.add_subplot(111)
line, = ax.plot(xout, yout, 'x')
plt.ylim(1e-3,3) ###TO BE CHANGED!!
plt.xlim(tm.time(), tm.time() + 600)      ###TO BE CHANGED
plt.ion()




nMeasurement = 0
while nMeasurement < 600: #Important setting - the maximum number of measurements wanted per run.
    
    ### START MEASUREMENT
    ic.kt.write('trace:feed:control next')
    ic.kt.write('init')
    
    ### CONVERT THE DATA FILE TO STEPS. 
    ###    (THE ORDER SEEMS SILLY, BUT IT'S TO CALCULATE AND PLOT WHILE IT'S MEASURING.)
    #print ic.outArray
    #Setting the limit for a change. Likely to be somewhat higher in reality
    dQdTlim = np.amax(cleverdiff(ic.outArray.Q, ic.outArray.t))/4
    peaks = ic.outArray[cleverdiff(ic.outArray.Q, ic.outArray.t) > dQdTlim].values

    #Filters the found peaks, to only give the first element per step.
    tprev = 0.0 #start value
    peakTimes = []
    for i in range(len(peaks)):
        if peaks[i,1]-tprev > 0.01:
            peakTimes.append(peaks[i,1])
            tprev = peaks[i,1]
    #searches the indices for each of the steps.
    time = ic.outArray.t.values
    charge = ic.outArray.Q.values


    #Find the indices of the peaks
    peakIndices = []
    for i in peakTimes:
        peakIndices.append(binarysearch(time, i, len(time)))

    #Take the mean of the next 20pts of the dataset, from the indices.
    #Oh yearh, and add two, to skip the jump.
    chargeSteps = []
    for i in peakIndices:
        #Gives strange results if the median is used - due to lack of resolution
        # in test measurement.
        #The mean is the 20 measurements after, minus the ten before.
        mean = np.mean(charge[i+2:i+22]) - np.mean(charge[i-11:i-1])
        chargeSteps.append(mean)
    ### REGENERATE DATA
    xout.append(tm.time())
    yout.append(np.mean(chargeSteps))

    ### REPLOT DATA
    line.set_xdata(xout)
    line.set_ydata(np.array(yout) / 1)#1.602e-19)
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.1)
    
    ### DOWNLOAD DATA
    isMeasuring = True
    t0 = tm.time()
    while isMeasuring == True:
        n = 0
        n = bin(int(str(ic.kt.ask(':status:measurement:event?'))[:-1]))[2:]
        try:
            if n[-10] == '1':
                #print 'Measurement finished - saving in array as ' + filename
                #Functionality for saving the recently measured array in the large array.
                #
                #
                # ##################
                #
                #
                ic.outArray = kf.list2pandasCharge(ic.kt.ask_for_values('trace:data?'), t0)
                #ic.outArray = ic.outArray.append(q, ignore_index = True)
                isMeasuring = False #Ends the loop.
                
        except IndexError:
            pass
    nMeasurement = nMeasurement + 1
    #ic.outArray.to_pickle(filename)