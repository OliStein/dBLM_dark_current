import numpy as np
import threading #Enables the threading.Timer function to time the execution
import time as tm


class ResourceManager:
    class get_instrument:
        def do_every(self, interval, worker_func, iterations = 0):
            #Enter loop only if the killsignal is not raised. Loop reschedules the next.
            if iterations != 1 and KillSignal == False:
                threading.Timer(
                    interval,
                    #Calls itself, to schedule the next scheduling of execution. Clever.
                    self.do_every,
                    [interval, worker_func, 0 if iterations == 0 else iterations-1]
                    ).start()
                #Run you clever boy. And remember!
                
                #print 'Pulse simulated'
        
        def __init__(self, inputStr = None):
            print 'Instrument instance created: '+str(inputStr)
            print 'Generating standard step output'
            self.stdOutput = [1e-8]*20 + [1]*100
            
            global KillSignal
            KillSignal = False
            
            self.ready_flag = 0
            self.nTriggers = 1
            
        def write(self, inputStr = None):
            print 'Write command: '+str(inputStr)
            if inputStr[0:10] == ':trigger:c':
                self.nTriggers = int(inputStr.split()[-1])
            if inputStr == 'init':
                self.do_every(1000, self.set_ready_flag(), 1)
                #self.set_ready_flag()
                print 'Starting pulse process'
                self.t0 = tm.time()
        
        def read(self, inputStr = None):
            print 'Read command: '+str(inputStr)
            return 'DUMMY'
                
        def ask(self, inputStr = None):
            if inputStr == ':status:measurement:event?':
                if self.ready_flag == 1:
                    KillSignal = True #Halts further processes
                    return '2047n' #Clever code for I'm done.
                    print 'Ask request: ' + str(inputStr) + ' succesfull'
                    self.ready_flag = 0
                else:
                    return '00000n' #This won't float any boats.
                    print 'newermind'
            else:
                print 'Ready for anal!'
                    
            
        def ask_for_values(self, inputStr = None):
            print 'Ask_for_values request: ' + str(inputStr)
            stepOut = self.stdOutput*1
            timebig = range(len(stepOut))
            timeOut = [timebig[i] * 0.001 for i in range(len(timebig))]
            vecOut = [[stepOut[i], timeOut[i], timebig[i]] for i in timebig] #Generates long lists.
            return sum(vecOut, []) #Flattens the data and returns.
            
        def set_ready_flag(self):
            tm.sleep(1)
            self.ready_flag = 1
            print 'ready_flag raised'
            
        