# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from joy import *

"""
class PosablePlan( Plan, PoseRecorder ):
    def __init__(self,app):
        Plan.__init__(self,app)
        PoseRecorder.__init__(app.robot.values())
    
    def setBehavior(self, period, count, rate, csv ):
        pass
    
    def behavior( self, evt ):
        Play back the current recording one or more times.

           INPUT:
             period -- float / None -- duration for entire recording
               if period is None, the recording timestamps are used
             count -- integer -- number of times to play
             rate -- float -- delay between commands sent (sec)
            
        # playback current pose for a given amount of time and with a given period
        if not self.plan:
          raise ValueError("No recording -- .snap() poses first!")
          return
        gait = asarray(self.plan,int)
        gaitfun = interp1d( gait[:,0], gait[:,1:].T ) # Gait interpolater function
        dur = gait[-1,0]-gait[0,0]
        if period is None:
          period = self.plan[-1][0] - self.plan[0][0]
        t0 = now()
        t1 = t0
        while t1-t0 < period*count:
            t1 = now()
            phi = (t1-t0)/period
            phi %= 1.0
            goal = gaitfun(phi*dur).round()
            print "\rphi: %.2f: " % phi, " ".join([
                "%6d" % g for g in goal
            ])
            self._set_pose( goal )	
            yield self.forDuration(rate)
"""
       
class InchMoveApp( JoyApp ):
  # Load both patterns from their CSV files
  FORWARD = loadCSV("movements/forward.csv")
  SMALL_STEP = loadCSV("movements/small_step.csv")
  SHARP_LEFT = loadCSV("movements/sharp_left.csv")
  SLOW_LEFT = loadCSV("movements/slow_left.csv")
  SHARP_RIGHT = loadCSV("movements/sharp_right.csv")
  SLOW_RIGHT = loadCSV("movements/slow_right.csv")

  def onStart(self):
    self.slowleftplan = SheetPlan(self, self.SLOW_LEFT)
    self.slowleftplan.setRate(2) # 2 means twice as fast
    self.slowleftplan.onStart = lambda : progress("Slow Left: starting") 
    self.slowleftplan.onStop = lambda : progress("Slow Left: done") 

    self.slowrightplan = SheetPlan(self, self.SLOW_RIGHT)
    self.slowrightplan.setRate(2)
    self.slowrightplan.onStart = lambda : progress("Slow Right: starting") 
    self.slowrightplan.onStop = lambda : progress("Slow Right: done")

    self.sharpleftplan = SheetPlan(self, self.SHARP_LEFT) 
    self.sharpleftplan.setRate(2)
    self.sharpleftplan.onStart = lambda : progress("Sharp Left: starting") 
    self.sharpleftplan.onStop = lambda : progress("Sharp Left: done") 

    self.sharprightplan = SheetPlan(self, self.SHARP_RIGHT) 
    self.sharprightplan.setRate(2)
    self.sharprightplan.onStart = lambda : progress("Sharp Right: starting") 
    self.sharprightplan.onStop = lambda : progress("Sharp Right: done") 

    self.forwardplan = SheetPlan(self, self.FORWARD) 
    self.forwardplan.setRate(2)
    self.forwardplan.onStart = lambda : progress("Forward: starting") 
    self.forwardplan.onStop = lambda : progress("Forward: done")  

    self.smallstepplan = SheetPlan(self, self.SMALL_STEP) 
    self.smallstepplan.setRate(1)
    self.smallstepplan.onStart = lambda : progress("Small Step: starting") 
    self.smallstepplan.onStop = lambda : progress("Small Step: done")  

  def onEvent(self,evt):
    if evt.type != KEYDOWN:
      return
    # assertion: must be a KEYDOWN event
    currentplan = self.forwardplan
    if evt.key == K_q:
        self.slowleftplan.start()
	currentplan = self.slowleftplan
    elif evt.key == K_e:
        self.slowrightplan.start()
	currentplan = self.slowrightplan
    elif evt.key == K_a:
        self.sharpleftplan.start()
	currentplan = self.sharpleftplan
    elif evt.key == K_d:
        self.sharprightplan.start()
	currentplan = self.slowrightplan
    elif evt.key == K_w:
        self.forwardplan.start()
	currentplan = self.forwardplan
    elif evt.key == K_z:
        self.smallstepplan.start()
	currentplan = self.smallstepplan
    elif evt.key == K_s:
        currentplan.stop()
    elif evt.key == K_SPACE:
	self.stop()

if __name__=="__main__":
  robot = None
  scr = None

  args = list(sys.argv[1:])
  while args:
    arg = args.pop(0)
    if arg=='--mod-count' or arg=='-c':
      N = int(args.pop(0))
      robot = dict(count=N)

  app = InchMoveApp(robot = robot, scr = scr)
  app.run()
