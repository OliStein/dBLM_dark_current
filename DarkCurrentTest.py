

'''Various Imports'''
import threading #Enables the threading.Timer function to time the execution
import numpy as np
import matplotlib.pyplot as plt
import visa as pv  #Handles the GPIB communication
import time as tm  #Only used for sleep command and getting the timestamp
import pandas as pd  #Data frame for data management.


#Important global variable to halt processing.
global KillSignal

#Function to reschedule and run other functions.
#The one function to rule them all!
#Continues 4-evarh if iterations not specified.
def do_every(interval, worker_func, iterations = 0):
    #Enter loop only if the killsignal is not raised. Loop reschedules the next.
    if iterations != 1 and KillSignal == False:
        handle = threading.Timer(
            interval,
            #Calls itself, to schedule the next scheduling of execution. Clever.
            do_every,
            [interval, worker_func, 0 if iterations == 0 else iterations-1]
            )
        #Run you clever boy. And remember!
        handle.start()

    #Or. Well. Only run if you're allowed to
    # - prevents execution with killsignal flag.
    if KillSignal == False:
        worker_func()





class darkcurrent:
    #Initiation is mainly used to setup the various flags and arrays, the keithley and plot.
    def __init__(self):
        #Definition of the present voltage variable
        self.PresentVoltage = 0
        #Initiate the dataframe, with 'fake' zero-values.
        self.TotalOutArray = pd.DataFrame({'u':[1e-15], 
                                           'i':[1e-15], 
                                           't':[tm.time()]},
                                           columns = ['u', 'i', 't'])
        #Takes care of the row number of the out array. (Individual
        self.TotalOutArrayLine = 0 
        #For book-keeping, basically.
        self.PreviousVoltage = 0

        ### IMPORTANT: INITAL VOLTAGE OF MEASUREMENT IS SET HERE:
        self.StartVoltage = 60
        ### IMPORTANT: FINAL VOLTAGE OF MEASUREMENT IS SET HERE:
        self.EndVoltage = 180
        ### IMPORTANT: STEP IN VOLTAGE OF MEASUREMENT IS SET HERE:
        self.StepVoltage = 10
        
        #List of voltages to be generated is set here.
        #The weird addition is to get the last datapoint measured as well.
        self.Voltages = np.arange(self.StartVoltage,
                                self.EndVoltage+self.StepVoltage,
                                self.StepVoltage)
                                
        #The number of voltage updates made during the coming measurement.
        self.nUpdates = int((self.EndVoltage - self.StartVoltage)/self.StepVoltage)
        #Superfluous array. Should be written out of the program.
        #It is used to keep a condensed edition of the array in, for a 
        #Previous plotting function. Not relevant anymore.
        self.CondensedOutArray = np.zeros(int(
                    (self.EndVoltage - self.StartVoltage)/self.StepVoltage)+5)
                    
        #Sets the filename the values will be saved in.
        self.filename = 'MeasurementDarkCurrent'+str(int(tm.time()))
        
        #Calls the plot setup function, to initiate the plot
        self.PlotSetup()
        #Calls the setup function for the Keithley
        self.KeithleySetup()
        
        ##FLAGS:
        #To take care of the step-down in range, as the voltage is increased.
        self.VoltageIncreased = False
        #Note to self: The stop/kill signals should be branched/merged better.
        self.STOPSIGNAL = False
        KillSignal = False
        #Introduced to save cpu cycles in plotting. 
        self.newData = False


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
        #Turn off zerocheck
        self.kt.write('system:zcheck 0')
        #Set current Measurement
        self.kt.write('sense:function \'current\'')
        #Set initial current, to max 20 uA
        self.kt.write('sense:current:range 2e-5')
        #Integrate over 10 PLC
        self.kt.write('sense:current:nplc 10')
        #Aquire in maximum resolution (7 digits)
        self.kt.write('sense:current:digits 7')
        #Disable math.
        self.kt.write('calculate:state 0')

        #Setup voltage source, initialise at 0.
        #Measurement connect. Simplifies cabling. Check Keithley manual.
        self.kt.write('source:voltage:mconnect 1')
        #Initiate voltage source at 0V
        self.kt.write('source:voltage 0')
        #Adjust the necessary range for the Voltage source.
        self.kt.write('source:voltage:range '+str(self.EndVoltage))
        #Enable the voltage source output.
        self.kt.write('output 1')
        #Set trigger continous, to keep the data coming regularly
        self.kt.write('trigger:source immediate')
        #The beginning of everything. Widely regarded as a bad move.
        self.kt.write('initiate:continuous 1')


    def PlotSetup(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.semilogy(abs(self.TotalOutArray['t']),
                                      abs(self.TotalOutArray['i']),
                                      'x')
        plt.ylim(5e-11, 2e-8)
        plt.xlim(tm.time(), tm.time() + 60 * self.nUpdates)


    def Measure(self):
        #print self.TotalOutArray
        try:
            measurement = self.kt.ask_for_values('fetch?')
        except pv.VisaIOError:
            print 'A problem has arisen. Waiting a bit, and clearing communication channels'
            self.kt.write('*cls')  #Clears error queue if something goes wrong.
            tm.sleep(2)
            self.kt.write('*cls') # just to be sure..
        self.CondensedOutArray[self.TotalOutArrayLine] = measurement[0]
        # Appending the present current measurement and time:
        u = self.kt.ask_for_values('source:voltage?')[0]
        i = measurement[0]
        t = tm.time()
        Addition = pd.DataFrame({'u':[u], 'i':[i], 't':[t]}, columns = ['u', 'i', 't'])
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

    def ChangeVoltage(self):
        #Implementation of stop signal:
        if self.STOPSIGNAL != True:
            try:
                self.PresentVoltage = self.Voltages[self.TotalOutArrayLine]
            except IndexError:
                print 'End of voltage list reached.'
                self.STOPSIGNAL = True
                KillSignal = True
                self.kt.write('output 0')

            #Terminates the program cleanly, at the end of the measurement.
            '''if self.TotalOutArrayLine > self.nUpdates-1:
                self.STOPSIGNAL = True
                KillSignal = True
                self.kt.write('output 0')'''

            self.TotalOutArray.to_pickle(self.filename)


    def DetectHaywire(self):
        ###Detect haywire on the previous few measurements increasing
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

        ###Detect haywire on maximum current (1mA)
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


    def sendEmail(self, body):
        import smtplib
        from email.MIMEMultipart import MIMEMultipart
        from email.MIMEText import MIMEText
        fromaddr = 'experimentdummy@gmail.com'
        recipients = ['c.buhl@cern.ch', 'oliver.stein@cern.ch', 'florian.burkart@cern.ch']
        toaddr = 'c.buhl@cern.ch'
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = 'Experiment Email Notification'
        msg.attach(MIMEText(body, 'plain'))


        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login('experimentdummy', 'yourpetsname')
        text = msg.as_string()
        for toaddr in recipients:
            server.sendmail(fromaddr, toaddr, text)
        server.quit()


dc = darkcurrent()

KillSignal = False

# Check for updates in the set of parameters, and implement them if it does so
do_every(0.25, dc.UpdateParameters)

tm.sleep(0.25)
# Measure the current every second
do_every(1, dc.Measure)

tm.sleep(0.25)
# Update the voltage. This is basically the time at each plateau
#<<<<<<< HEAD
cv = do_every (3600, dc.ChangeVoltage) #240 is 4 minutes
#=======
#do_every(1800, dc.ChangeVoltage) #240 is 4 minutes
#>>>>>>> 38881f697d091d11acd2b49ac08c25a42d87e066


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
dc.sendEmail('Experiment finished succesfully')
raw_input('\n\n\n\tScript finished. Press enter to exit...\n\n\n')
