# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from joy import *

# !! This is only used to go Forward and then Right using one key !! #
class MoveUpRight( Plan ):
  """
  ShaveNHaircutPlan shows a simple example of sequential composition:
  its behavior is to run the shave plan followed by the haircut plan.
  """
  def __init__(self,app,up,right,*arg,**kw):
    Plan.__init__(self,app,*arg,**kw)
    self.up = up
    self.right = right
    
  def behavior( self ):
    progress("Both: Move Foward")
    yield self.up
    progress("Both: Move Right")
    yield self.right
    progress("Both: done")
    
class InchMoveApp( JoyApp ):
  # Load both patterns from their CSV files
  UP = loadCSV("move_up.csv")
  RIGHT = loadCSV("move_right.csv")
  LEFT = loadCSV("move_left.csv")

  def __init__(self,upSpec,rightSpec,leftSpec,*arg,**kw):
    JoyApp.__init__(self, *arg,**kw)
    self.upSpec = upSpec
    self.rightSpec = rightSpec
    self.leftSpec = leftSpec

  def onStart(self):
    #
    #
    self.upplan = SheetPlan(self, self.UP, x=self.upSpec ) 
    # give us start and stop messages; in your own code you can omit these 
    self.upplan.onStart = lambda : progress("Move Foward: starting") 
    self.upplan.onStop = lambda : progress("Move Forward: done") 
    #
    #
    self.rightplan = SheetPlan(self, self.RIGHT, x=self.rightSpec )
    # give us start and stop messages; in your own code you can omit these 
    self.rightplan.onStart = lambda : progress("Turn Right: starting") 
    self.rightplan.onStop = lambda : progress("Turn Right: done") 
    
    self.leftplan = SheetPlan(self, self.LEFT, x=self.leftSpec ) 
    # give us start and stop messages; in your own code you can omit these 
    self.leftplan.onStart = lambda : progress("Turn Left: starting") 
    self.leftplan.onStop = lambda : progress("Turn Left: done") 
    #
    # Set up a ShaveNHaircutPlan using both of the previous plans
    #
    self.up_right = ShaveNHaircutPlan(self, self.upplan, self.rightplan)

  def onEvent(self,evt):
    if evt.type != KEYDOWN:
      return
    # assertion: must be a KEYDOWN event 
    if evt.key == K_u:
      if ( not self.rightplan.isRunning()
           and not self.leftplan.isRunning() ):
        self.upplan.start()
    elif evt.key == K_r:
      if ( not self.upplan.isRunning()
           and not self.leftplan.isRunning() ):
        self.rightplan.start()
    elif evt.key == K_l:
      if ( not self.upplan.isRunning()
           and not self.rightplan.isRunning() ):
        self.leftplan.start()
    elif evt.key == K_ESCAPE:
        self.stop()

if __name__=="__main__":
  robot = None
  scr = None
  upSpec = "#up "
  rightSpec = "#right "
  leftSpec = "#left "
  args = list(sys.argv[1:])
  while args:
    arg = args.pop(0)
    if arg=='--mod-count' or arg=='-c':
      N = int(args.pop(0))
      robot = dict(count=N)
    elif arg=='--up' or arg=='-u':
      upSpec = args.pop(0)
      if upSpec[:1]==">": scr = {}
    elif arg=='--right' or arg=='-r':
      rightSpec = args.pop(0)
      if rightSpec[:1]==">": scr = {}
    elif arg=='--left' or arg=='-l':
      leftSpec = args.pop(0)
      if leftSpec[:1]==">": scr = {}
    elif arg=='--help' or arg=='-h':
      sys.stdout.write("""
  Usage: %s [options]
  
    'Shave and a Haircut' example of running Plan-s in parallel and in
    sequence. The example shows that plans can run in parallel, and that
    Plan behaviors (e.g. the ShaveNHaircutPlan defined here) can use other
    plans as sub-behaviors, thereby "calling them" sequentially.
    
    When running, the demo uses the keyboard. The keys are:
      's' -- start "Shave"
      'h' -- start "Haircut"
      'b' -- start "Both", calling "Shave" and "Haircut" in sequence
      'escape' -- exit program
      
    Options:      
      --mod-count <number> | -c <number>
        Search for specified number of modules at startup
      
      --shave <spec> | -s <spec>
      --haircut <spec> | -h <spec>
        Specify the output setter to use for 'shave' (resp. 'haircut')
        
        Typical <spec> values would be:
         '#shave ' -- to print messages to the terminal with '#shave ' as prefix
         '>x' -- send to Scratch sensor 'x'
         'Nx3C/@set_pos' -- send to position of CKBot servo module with ID 0x3C
        
        NOTE: to use robot modules you MUST also specify a -c option

    NOTE NOTE: I was too lazy to modify this, use -u, -r, -l for up, right, left commands
        
    """ % sys.argv[0])
      sys.exit(1)
    # ENDS cmdline parsing loop
  
  app = InchMoveApp(upSpec,rightSpec,leftSpec,robot=robot,scr=scr)
  app.run()
