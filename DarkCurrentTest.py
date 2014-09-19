import threading
import numpy as np
import matplotlib.pyplot as plt
import visa as pv
import time as tm
import pandas as pd

global KillSignal

def do_every (interval, worker_func, iterations = 0):
    if iterations != 1 and KillSignal == False:
        handle = threading.Timer (
            interval,
            do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]
            )
        handle.start ()

    if KillSignal == False: 
        worker_func ()
    #return handle
  
  
class darkcurrent:
    def __init__(self):
        self.PresentOutArray = []
        self.PresentVoltage = 0
        self.TotalOutArray = pd.DataFrame({'u':[1e-15],'i':[1e-15],'t':[tm.time()]}, 
                                            columns = ['u','i','t'])
        self.TotalOutArrayLine = 0 #Takes care of the row number of the out array. (Individual
                                    #voltages, basically)
        self.PreviousVoltage = 0
        self.StartVoltage = 50
        self.EndVoltage = 70
        self.StepVoltage = 2
        self.nUpdates = (self.EndVoltage - self.StartVoltage)/self.StepVoltage
        self.newData = False
        self.CondensedOutArray = np.zeros(int((self.EndVoltage - self.StartVoltage)/self.StepVoltage)+5)
        self.STOPSIGNAL = False
        self.PlotSetup()
        self.KeithleySetup()
        KillSignal = False
        
        
        #Setup the keithley to: 
            #Current measurement
            #Enable the voltage source
            #Average over 10PLCs    
    def KeithleySetup(self): #DONE
        #Generate resourcemanager, and initiate instrument on GPIB::24.
        rm = pv.ResourceManager()
        self.kt = rm.get_instrument('GPIB::24')
        self.kt.write('*IDN?')
        print '\n\n\n', self.kt.read(), 'is initiated - Prepare for vogon poetry!\n\n\n'
        tm.sleep(2)
        #General resets
        self.kt.write('*rst')
        self.kt.write('*cls')
        self.kt.write('system:zcheck 0')
        self.kt.write('sense:function \'current\'')
        self.kt.write('sense:current:range 2e-6')
        tm.sleep(3)
        self.kt.write('sense:current:nplc 10')
        self.kt.write('sense:current:digits 6')
        self.kt.write('calculate:state 0')
        self.kt.write('system:lsync:state 0') 
        
        #Setup voltage source, initialise at 0.
        self.kt.write('source:voltage:mconnect 1')
        self.kt.write('source:voltage 0')
        self.kt.write('output 1')
        #Generate reference measurement:
        #self.kt.write('sense:current:reference:state 1')
            
        #Mainly for demonstration purposes:
        self.kt.write('trigger:source immediate')
        #The beginning of everything. Widely regarded as a bad move.
        self.kt.write('initiate:continuous 1')   
        tm.sleep(3)
        
        
    def PlotSetup(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.semilogy(abs(self.TotalOutArray['t']), abs(self.TotalOutArray['i']), 'x')
        plt.ylim(0, 2e-8)
        plt.xlim(tm.time(), tm.time() + 60 * self.nUpdates)
        
        
    def Measure(self):
        #print self.TotalOutArray
        measurement = self.kt.ask_for_values('fetch?')
        self.CondensedOutArray[self.TotalOutArrayLine] = measurement[0]
        # Appending the present current measurement and time:
        u = self.kt.ask_for_values('source:voltage?')[0]
        i = measurement[0]
        t = tm.time()
        Addition = pd.DataFrame({'u': [u], 'i': [i], 't':[t]}, columns = ['u','i','t'])
        self.TotalOutArray = self.TotalOutArray.append(Addition, ignore_index = True)
        self.newData = True
        #print u, i, t
        #pass
        #Make a one shot measurement of the current, averaged a bit, with the keithley.
    
    def Replot(self):
        print 'Redrawing plot'
        self.points.set_data(self.TotalOutArray['u'], self.TotalOutArray['i'])
        #self.points.set_ydata(self.TotalOutArray['i'])
        plt.draw()
        #print self.TotalOutArray['u'], self.TotalOutArray['i']
        plt.pause(0.1)
        tm.sleep(1)
        #pass
        #Update the plot to reflect the new changes.
    
    def UpdateParameters(self):
        #If updates are detected:
        if self.PresentVoltage != self.PreviousVoltage:
            #Update the voltage on the Keithley
            self.kt.write('source:voltage '+str(self.PresentVoltage))
            #Increment the TotalOutArrayLine count.
            self.TotalOutArrayLine = self.TotalOutArrayLine + 1
            #Reset PresentOutArray
            #print 'Voltage updated: ', self.PresentVoltage, 'volts'

        #If no updates are detected:
        self.PreviousVoltage = self.PresentVoltage
        #print 'Nothing Changed, voltage = ', self.PresentVoltage
        #Check for haywire current
        self.DetectHaywire()
    
    def ChangeVoltage(self): #DONE! Wouhuu!
        #Implementation of stop signal:
        if self.STOPSIGNAL != True:    
            self.PresentVoltage = np.arange(self.StartVoltage,
                        self.EndVoltage, self.StepVoltage)[self.TotalOutArrayLine] 
            #Start Voltage, Stop Voltage, Step Voltage
            #print 'The present voltage changes to ', self.PresentVoltage, 'volts'
        
        
    def DetectHaywire(self):
        #Simulate Haywire Signal:
        #if  np.max(self.CondensedOutArray) > 1e-6:
         #   self.STOPSIGNAL = True
            
        #Be ready to react on the stopsignal.
        if self.STOPSIGNAL == True:
            #self.PresentVoltage = 0 #It should be considered if it isn't nice to know.
            self.kt.write('output 0')
            print '\n\n\t Stop signal received\n\n'
            print self.CondensedOutArray
        

        

dc = darkcurrent()
    
KillSignal = False

# Check for updates in the set of parameters, and implement them if it does so
upd = do_every (0.25, dc.UpdateParameters)

tm.sleep(0.25)
# Measure the current every second
msre = do_every (1, dc.Measure)

tm.sleep(0.25)
# Update the voltage. This is basically the time at each plateau
cv = do_every (60, dc.ChangeVoltage, dc.nUpdates)


# Replot the output when there's new data
plt.ion()
while True: #dc.TotalOutArrayLine + 10 < dc.nUpdates:
    if dc.newData == True:
        dc.line.set_xdata(dc.TotalOutArray['t'])
        dc.line.set_ydata(dc.TotalOutArray['i'])
        dc.fig.canvas.draw()
        dc.fig.canvas.flush_events()
        plt.pause(0.1)
        dc.newData = False
        print 'New data in array'
        
        
KillSignal = True
plt.ioff()   
raw_input('\n\n\n\tScript finished. Press enter to exit...\n\n\n')