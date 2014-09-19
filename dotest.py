import threading
import numpy as np
import matplotlib.pyplot as plt
import random as rd

def do_every (interval, worker_func, iterations = 0):
    if iterations != 1:
        handle = threading.Timer (
            interval,
            do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]
            )
        handle.start ()

    worker_func ()
    return handle
    
    
    
class plottest:
    def __init__(self):
        self.array = [1]
        self.plotInit()
        self.newData = False
        
    def rng(self):
        nmb = rd.random()
        self.array.append(nmb)
        self.newData = True
        
    def plotInit(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(1,self.array)
        self.ax.set_ylim([0,1])
        self.ax.set_xlim([0,10])
        
    def plotUpdate(self):
        self.line.set_xdata(range(len(self.array)))
        self.line.set_ydata(self.array)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(1)
        
        
plt.ion()
p = plottest()
rn = do_every(1, p.rng, 50)


while True:
    if p.newData == True:
        p.line.set_xdata(range(len(p.array)))
        p.line.set_ydata(p.array)
        p.fig.canvas.draw()
        p.fig.canvas.flush_events()
        plt.pause(1)
        p.newData = False
        
    else:
        pass
    
    
    
    
    
    
    
    
    
    
    
    
    
