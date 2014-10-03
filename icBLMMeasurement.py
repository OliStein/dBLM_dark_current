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
    #   It should take four measurements on external trigger
    #   Download to the pc, save the data,
    #   and wait for the next trigger.
    
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