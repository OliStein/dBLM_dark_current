'''Various Imports'''
import threading #Enables the threading.Timer function to time the execution
import numpy as np
import matplotlib.pyplot as plt
import visa as pv  #Handles the GPIB communication
import time as tm  #Only used for sleep command and getting the timestamp
import pandas as pd  #Data frame for data management.


#Important global variable to halt processing.
global KillSignal


class icBLM:
    def __init__(self):
    #Generate various arrays for measurement.
    
    #Setup Keithley for measurement.
    rm = pv.ResourceManager()
    kt = rm.get_instrument('GPIB::24')
    kt.write('*IDN?')
    print '\n\n\n', kt.read(), 'is initiated - Prepare for vogon poetry!\n\n\n'
    kt.write('*rst')
    kt.write('*cls')
    #Setup system stuff
    kt.write('system:zcheck 0')
    kt.write('sense:function \'charge\'')
    kt.write('sense:charge:range 2e-9')
    kt.write('sense:charge:nplc 0.01')
    kt.write('sense:charge:digits 7')
    kt.write('calculate:state 0')
    #kt.write(':display:enable 0')
    #Trigger setup:
    kt.write(':arm:layer1:source immediate')
    kt.write(':arm:layer2:count 10') #The number is very important here!
    kt.write(':arm:layer2:source tlink')
    kt.write(':arm:layer2:tconfigure:asynchronous:iline 5') #Set the input
    # line for the triglink
    kt.write(':trigger:count 10')
    #kt.write('initiate:continuous 1')
    kt.write('trace:points 100')
    kt.write('trace:feed:control next')
    
    #Setup plot for showing. It's still undecided what it should show.
    #   I'm thinking two plots on top of each other, one with the primary value,
    #   and one with the background offset signal (The latter three)
    
ic = icBLM()

while nMeasurement <= 50 #Important setting - the maximum number of samples wanted per run.
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
            print 'nMeasurement = ' + nMeasurement
            nMeasurement = nMeasurement + 1
    except IndexError:
        pass