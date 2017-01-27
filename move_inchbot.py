# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from joy import *
    
class InchMoveApp( JoyApp ):
  # Load both patterns from their CSV files
  FORWARD = loadCSV("movements/forward.csv")
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
    self.forwardplan.setRate(1)
    self.forwardplan.onStart = lambda : progress("Forward: starting") 
    self.forwardplan.onStop = lambda : progress("Forward: done")  

  def onEvent(self,evt):
    if evt.type != KEYDOWN:
      return
    # assertion: must be a KEYDOWN event 
    if evt.key == K_q:
        self.slowleftplan.start()
    elif evt.key == K_e:
        self.slowrightplan.start()
    elif evt.key == K_a:
        self.sharpleftplan.start()
    elif evt.key == K_d:
        self.slowrightplan.start()
    elif evt.key == K_w:
        self.forwardplan.start()
    elif evt.key == K_s:
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
