import os
import time
from multiprocessing import Process, Value, Queue
import RPi.GPIO as GPIO

FILL = 12
HEAT = 10
POUR = 8
FLOW = 16
EMPTY = 18
FULL_ = 22

MIN_FILL = 0.5
LO_PAUSE = 0.01
HI_PAUSE = 0.0001
CYCLE_TIME = 0.1

class CoffeeMachine:
    liveV = Value('b',True)
    measureV = Value('i',0)
    fullV = Value('b',False)
    fillingV = Value('b',False)
    flowQ = Queue()

    filling = False
    flow_prev = True
    fill_since = time.time()
    flow_since = fill_since

    def off(self):
        GPIO.output(FILL,False)
        GPIO.output(HEAT,False)
        GPIO.output(POUR,False)
        print "Machine turned off."
        
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(FILL,GPIO.OUT)
        GPIO.setup(HEAT,GPIO.OUT)
        GPIO.setup(POUR,GPIO.OUT)
        
        self.off()

        GPIO.setup(FLOW,GPIO.IN)     
        GPIO.setup(EMPTY,GPIO.IN)     
        GPIO.setup(FULL_,GPIO.IN)    

        self.proc = Process(target = self.coffeeLoop, args = ())
        self.proc.start()
        print "CoffeeMachine initialised."

    def __del__(self): self.off()

    def coffeeLoop(self):
        try:
            while self.liveV.value:
                try:
                    full = not GPIO.input(FULL_)
                    empty = GPIO.input(EMPTY)
                    flow = GPIO.input(FLOW)
                    t = time.time()
                    
                    GPIO.output(HEAT, not empty)
                    
                    if self.measureV.value != 0: #pouring
                        GPIO.output(POUR,True)
                        
                        if flow != self.flow_prev: #flowmeter state transition
                             self.flow_prev = flow
                             if flow: 
                                self.flowQ.put((self.measureV.value, t - self.flow_since))
                                self.flow_since = t
                                self.measureV.value -= 1
                                
                        if flow: time.sleep(HI_PAUSE)
                        else: time.sleep(LO_PAUSE)        
                        
                    else: #not pouring
                        GPIO.output(POUR,False)

                        if full == self.filling and (t - self.fill_since > MIN_FILL):
                            self.filling = not self.filling
                            GPIO.output(FILL, self.filling)
                       
                        if full != self.filling: self.fill_since = t
                        
                        self.fullV.value = full
                        self.fillingV.value = self.filling
                        
                        time.sleep(CYCLE_TIME)
                        
                except: self.off()
        finally: self.off()

    def close(self): self.liveV.value = False

    def pour(self, dose = -1):
        while not self.flowQ.empty(): self.flowQ.get() #reset stats
        self.measureV.value = dose
        
    def stop(self):
        self.measureV.value = 0
        n = 0
        while not self.flowQ.empty():
            self.flowQ.get()
            n += 1
        return n

    def flowStats(self):
        t = 0
        n = -1
        min = 10000
        max = 0
        while not self.flowQ.empty():
            (x,d) = self.flowQ.get()
            print d
            n += 1
            if n>0:
                t += d
                if d<min: min=d
                if d>max: max=d
        if n<=0: return "No flow records"        
        else: return (n,min,t/n,max)

