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
  
  
def sendmail(body):
    import smtplib
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    fromaddr = 'experimentdummy@gmail.com'
    toaddr = 'c.buhl@cern.ch'
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = 'Experiment Email Notification'
    msg.attach(MIMEText(body, 'plain'))
   
   
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('experimentdummy', 'yourpetsname')
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)

  
  
class darkcurrent:
    def __init__(self):
        self.PresentOutArray = []
        self.PresentVoltage = 0
        self.TotalOutArray = pd.DataFrame({'u':[1e-15],'i':[1e-15],'t':[tm.time()]}, 
                                            columns = ['u','i','t'])
        self.TotalOutArrayLine = 0 #Takes care of the row number of the out array. (Individual
                                    #voltages, basically)
        self.PreviousVoltage = 0
        self.StartVoltage = 60
        self.EndVoltage = 180
        self.StepVoltage = 10
        #The weird addition is to get the last datapoint measured as well.
        self.Voltages = np.arange(self.StartVoltage, self.EndVoltage+self.StepVoltage, self.StepVoltage)
        self.VoltageIncreased = False
        self.nUpdates = int((self.EndVoltage - self.StartVoltage)/self.StepVoltage)
        self.newData = False
        self.CondensedOutArray = np.zeros(int((self.EndVoltage - self.StartVoltage)/self.StepVoltage)+5)
        self.STOPSIGNAL = False
        self.PlotSetup()
        self.KeithleySetup()
        KillSignal = False
        self.filename = 'MeasurementDarkCurrent'+str(int(tm.time()))
        
        
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
        self.kt.write('sense:current:range 2e-5')
        tm.sleep(3)
        self.kt.write('sense:current:nplc 10')
        self.kt.write('sense:current:digits 7')
        self.kt.write('calculate:state 0')
        #self.kt.write('system:lsync:state 0') 
        
        #Setup voltage source, initialise at 0.
        self.kt.write('source:voltage:mconnect 1')
        self.kt.write('source:voltage 0')
        self.kt.write('source:voltage:range '+str(self.EndVoltage))
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
        plt.ylim(5e-11, 2e-8)
        plt.xlim(tm.time(), tm.time() + 60 * self.nUpdates)
        
        
    def Measure(self):
        #print self.TotalOutArray
        try: 
            measurement = self.kt.ask_for_values('fetch?')
        except(pv.VisaIOError):
            print 'A problem has arisen. Waiting a bit, and clearing communication channels'
            self.kt.write('*cls')  #Clears error queue if something goes wrong.
            tm.sleep(2)
            self.kt.write('*cls') # just to be sure..
        self.CondensedOutArray[self.TotalOutArrayLine] = measurement[0]
        # Appending the present current measurement and time:
        u = self.kt.ask_for_values('source:voltage?')[0]
        i = measurement[0]
        t = tm.time()
        Addition = pd.DataFrame({'u': [u], 'i': [i], 't':[t]}, columns = ['u','i','t'])
        self.TotalOutArray = self.TotalOutArray.append(Addition, ignore_index = True)
        self.newData = True
        
        #Increase sensitivity if the measurement comes below 1e-9A:
        if measurement[0] < 1e-9 and self.VoltageIncreased == True:
            self.kt.write('sense:current:range 1e-8') #one order of magnitude is given in spare.
            self.VoltageIncreased = False
    
    def Replot(self):
        print 'Redrawing plot'
        self.points.set_data(self.TotalOutArray['u'], self.TotalOutArray['i'])
        plt.draw()
        plt.pause(0.1)
        tm.sleep(1)
        #Update the plot to reflect the new changes.
    
    def UpdateParameters(self):
        #If updates are detected:
        if self.PresentVoltage != self.PreviousVoltage:
            #Update the voltage on the Keithley
            self.kt.write('source:voltage '+str(self.PresentVoltage))
            #Increment the TotalOutArrayLine count.
            self.TotalOutArrayLine = self.TotalOutArrayLine + 1
            #increase the dynamic range again.
            self.kt.write('sense:current:range 2e-5')
            self.VoltageIncreased = True
            print 'Voltage increased to ' + str(self.PresentVoltage)

        #If no updates are detected:
        self.PreviousVoltage = self.PresentVoltage
        
        #Check for haywire current
        self.DetectHaywire()
    
    def ChangeVoltage(self): #DONE! Wouhuu!
        #Implementation of stop signal:
        if self.STOPSIGNAL != True:
            try:
                self.PresentVoltage = self.Voltages[self.TotalOutArrayLine]
            except(IndexError):
                print 'End of voltage list reached.'
                self.STOPSIGNAL = True
                KillSignal = True
                self.kt.write('output 0')
                        
            #Terminates the program cleanly, at the end of the measurement.
            '''if self.TotalOutArrayLine > self.nUpdates-1:
                self.STOPSIGNAL = True
                KillSignal = True
                self.kt.write('output 0')'''
            #Start Voltage, Stop Voltage, Step Voltage
            #print 'The present voltage changes to ', self.PresentVoltage, 'volts'
            
            self.TotalOutArray.to_pickle(self.filename)
        
        
    def DetectHaywire(self):
        #Simulate Haywire Signal:
        #if  np.max(self.CondensedOutArray) > 1e-6:
         #   self.STOPSIGNAL = True

        ''' Detect haywire on the previous few measurements increasing'''
        HaywireCount = 0
        for i in np.diff(self.TotalOutArray['i'][-16:]): #More than 2/3 of the measurements must be increasing  to trigger.
            # In the case that one of the entries are more than 0:
            if i > 0:
                HaywireCount = HaywireCount + 1
        if HaywireCount > 5: 
            #print 'Warning. Positive di/dt detected. ', HaywireCount,'/10' 
            pass
        if HaywireCount > 10 and sum(self.TotalOutArray['i'][-2:] > 1e-5):
            print '\n\n\t ERROR. HAYWIRE DETECTED \n\t Script stopped.\n'
            self.STOPSIGNAL = True
            KillSignal = True
        
        '''Detect haywire on maximum current (1mA)'''
        if 1 > np.max(self.TotalOutArray['i']) > 1e-4:
            print '\n\n\t ERROR. ABOVE MAX CURRENT DETECTED.\n\t Script stopped.\n'
            self.STOPSIGNAL = True
            KillSignal = True
         
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
cv = do_every (1800, dc.ChangeVoltage) #240 is 4 minutes


# Replot the output when there's new data
plt.ion()
while KillSignal == False and dc.STOPSIGNAL == False: #dc.TotalOutArrayLine + 10 < dc.nUpdates:
    if dc.newData == True:
        dc.line.set_xdata(dc.TotalOutArray['t'])
        dc.line.set_ydata(dc.TotalOutArray['i'])
        dc.fig.canvas.draw()
        dc.fig.canvas.flush_events()
        plt.pause(0.1)
        dc.newData = False
        #print 'New data in array'
        
        
KillSignal = True
plt.ioff()
sendmail('Experiment finished succesfully')
raw_input('\n\n\n\tScript finished. Press enter to exit...\n\n\n')