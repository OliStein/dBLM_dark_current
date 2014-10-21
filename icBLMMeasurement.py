'''Various Imports'''
import threading #Enables the threading.Timer function to time the execution
import numpy as np
import matplotlib.pyplot as plt
import visa as pv  #Handles the GPIB communication
import time as tm  #Only used for sleep command and getting the timestamp
import pandas as pd  #Data frame for data management.
import keithley_func as kf


#Important global variable to halt processing.
global KillSignal


class icBLM:
    def __init__(self):
        #Generate various arrays for measurement.
        self.outArray = pd.DataFrame({'Q':[1e-20],
                                 't':[0]},#tm.time()]},
                                 columns = ['Q', 't'])
        
        self.TriggersPerMeasurement = 12
        self.SamplesPerTrigger =100 #Shouldn't be changed.
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
        self.kt.write('system:lsync:state 0')
        self.kt.write('sense:function \'charge\'')
        self.kt.write('sense:charge:range 2e-6')
        self.kt.write('sense:charge:nplc 0.01')
        self.kt.write('sense:charge:digits 7')
        self.kt.write('calculate:state 0')
        self.kt.write(':display:enable 0')
        
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
    
    #Setup plot for showing. It's still undecided what it should show.
    #   I'm thinking two plots on top of each other, one with the primary value,
    #   and one with the background offset signal (The latter three)
filename = 'Measurement_icBLM'+str(int(tm.time()))
ic = icBLM()
nMeasurement = 0
while nMeasurement < 1: #Important setting - the maximum number of measurements wanted per run.
    ic.kt.write('trace:feed:control next')
    ic.kt.write('init')
    isMeasuring = True
    t0 = tm.time()
    while isMeasuring == True:
        n = bin(int(str(ic.kt.ask(':status:measurement:event?'))[:-1]))[2:]
        try:
            if n[-10] == '1':
                print 'Maaling faerdiggjort - gemmer i array'
                #Functionality for saving the recently measured array in the large array.
                #
                #
                # ##################
                #
                #
                q = kf.list2pandasCharge(ic.kt.ask_for_values('trace:data?'))
                ic.outArray = ic.outArray.append(q, ignore_index = True)
                isMeasuring = False #Ends the loop.
                
        except IndexError:
            pass
    nMeasurement = nMeasurement + 1
    ic.outArray.to_pickle(filename)


plt.plot(ic.outArray['t'], ic.outArray['Q'], 'x')
plt.show()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    