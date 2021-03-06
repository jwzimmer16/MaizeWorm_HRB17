"""
The CKBot.pololu python module provides classes used to communicate with CKBot robot modules connected to a Pololu Maestro Device (rather than CAN) using a protocol similar to the Robotics Bus Protocol. These classes are primarily used to interface with the CKBot.logical python module found in the Modlab CKBot repository. For more information on
the low-level interface, please refer to the Pololu Maestro Device User Manual found at http://www.pololu.com/docs/0J40/all

NOTE: Our implementation assumes the Pololu Maestro Device is set receive commands in Pololu Mode. 

Main uses of this module:
(*) control CKBot robot modules (specifically the servos) connected to a Pololu Maestro device
(*) mimics the behaviour of the CAN Bus, except using the Pololu Maestro Device as a communications channel, can currently only
send position and go_slack commands

Example 1 - Pololu robot module only: 
nodes = {0:0x23, 5:0x65}
bus = pololu.Bus()
p = pololu.Protocol(bus = bus, nodes = nodes)
p.send_cmd(0x23,4,1000)  

Example 2 - Integrate with CKBot.logical python module:
import logical
nodes = {0xD1:0, 0xA7:1, 0xDA:2} 
bus = pololu.Bus()  #J on mac for now do .Bus("/dev/tty.usbserial-A70041hF")
p = pololu.Protocol(bus = bus, nodes = nodes)
c = logical.Cluster(p)
c.populate(3,{0xD1:'head', 0xA7:'mid', 0xDA:'tail'})
c.at.head.set_pos(1000)

Both examples sets the position of the 0x23 robot module, connected to Pololu Maestro channel 0, to 1000 (10 degrees from the  neutral position)
"""

from time import time as now
from sys import platform as SYS_PLATFORM
import struct
import commands

from ckmodule import Module, AbstractNodeAdaptor, AbstractProtocol, AbstractBus, progress, AbstractServoModule
from port2port import newConnection

DEBUG=[]

class Bus(AbstractBus):
  """
  Concrete class that provides the functionality
  needed to send messages to a pololu controller
  over a serial connection. 

  It is responsible for correctly formatting certain inputs
  to Pololu-understandable formats as documented in the Pololu
  Maestro User Manual located at http://www.pololu.com/docs/0J40/all
  """

  def __init__(self, port = 'tty={ "glob":"/dev/ttyACM0", "baudrate":38400, "timeout":0.1}', crc_enabled=False, *args,**kw):
    """
    Initialize a Pololu Bus class

    INPUT:
    port -- port / connection specification (see port2port.Connection)
    
    ATTRIBUTES:
    ser -- connection handle
    """
    AbstractBus.__init__(self,*args,**kw)
    self.ser = newConnection( port )
    self.port = port
    self.crc_enabled = crc_enabled
    self.DEBUG = DEBUG

  def get_errors(self):
    """
    Retrieve error messages from the Pololu Maestro device using the protocol outlined by the Pololu Maestro documentation

    WARNING: This method will hang if there is a faulty serial connection
    """
    if self.ser is not None:
      self.write((0xA1,0))
    
      while not self.ser.inWaiting():
        continue

      high = self.ser.read()
      while self.ser.inWaiting():
        low = high
        high = self.ser.read()
    
      return low | (high << 8)
      
  def open( self ):
    if not self.ser.isOpen():
      raise IOError("Serial port is not open")
      
  def write(self, val):
    """
    Write data to the pololu controller over serial
    
    INPUT:
    val -- tuple -- tuple of ints to write to serial
    """
    
    if self.ser is None:
      raise IOError("Serial port is not open")
      
    # Format the values into serial-writable string
    packed_cmd = [ struct.pack("B", val_part) \
                     for val_part in val ]
    cmd_str = "".join(packed_cmd)

    if self.crc_enabled:
      cmd_str = self.crc7(cmd_str) # Calculate and append Cyclic Redundancy Check byte
    if 'w' in self.DEBUG:
      print "Ser WR>",repr(cmd_str)
    self.ser.write(cmd_str)            

  def close(self):
    """
    Close serial connection to the pololu controller if
    a connection has been made
    """
    if self.ser is not None:
      self.ser.close()
      self.ser = None
  
  def crc7(self,comstr):
    """
    This function calculates and appends the Cyclic Redundancy Check (CRC7) byte for error checking
    """
    l = len(comstr)   

    int_tuple = struct.unpack('B'*len(comstr), comstr)
    divd = self.__bitrev(int_tuple)

    if(l>4):
      print " This CRC function currently does not support strings > 4 chars"
      return 0
    
    divd = self.__bitrev(ord(comstr[0]))

        # put the chars in an integer 
    for i in range(1,l):
      new = self.__bitrev(ord(comstr[i]))
      divd <<= 8
      divd = divd | new

        #crc = 0b10001001<<(8*(l-1))
      #hex instead
      crc = int('10001001',2)<<(8*(l-1)) #J binary literals don't work in python 2.5
      lsbcheck = 0x80 << (8*(l-1))
    
      for i in range(0,8*l):
        if(divd & lsbcheck == lsbcheck):
          divd = divd ^ crc
          divd = divd << 1
        else:
          divd = divd<<1

      divd = divd>>(8*(l-1))
      divd = self.__bitrev(divd)
      s = chr(divd & 0xff)

      return comstr + s

  def __bitrev(self,bytes):
    """
    Creates a lookup table of reversed bit orders

    Input: 
       bytes -- tuple -- tuple of 1 byte values to be reversed
    Output:
       bitrev_table -- dict
    """
    bytes = sum(bytes)         # Sums the bytes
    bin_repr = bin(bytes)[2:]  # Convert to binary string, remove "0b" at the beginning of the string
    bin_repr = bin_repr[::-1]  # Reverse all digits
    bin_repr = "0b%s" % bin_repr
    
    return int(bin_repr,2)     # Convert back to int, and return
      

class Protocol( AbstractProtocol ):
  """
  This is a concrete class that provides all the 
  functionality needed to send messages to a pololu 
  controller over a "pololu bus". This protocol follows
  the specifications provided by the Pololu Maestro 
  Documentation found at:
  http://www.pololu.com/docs/0J40/all
  
  For use with the Pololu Maestro 12pin, Firmware Version1.1
  
  It is meant to mimic the can.Protocol class, except
  for the pololu device rather than a CAN network
  
  This converts CKBot Module-specific commands into
  Pololu equivalents, and maintains the state of the
  Pololu device and its handles to modules via fake heartbeats
  u
  WARNING: Current version has only been tested with the 
  12-pin Pololu Maestro Firmwarev1.1 and does NOT support Pololu-styled 
  commands (supports only MiniSSC2 and Compact), support for Pololu-styled 
  commands will be included in a future release perhaps
  """

  # Pololu Protocol Sync Value (must be 0xAA)
  # This is also to initialize the Maestro to begin receiving commands using the PololuProtocol
  POLOLU_BYTE = 0xAA

  def __init__(self, bus=None, nodes=None, *args,**kw):
    """
    Initialize a pololu.Protocol
    
    INPUT:
    bus -- pololu.Bus -- Serial bus used to communicate with Pololu Device
    nodes -- dictionary -- key:module node_id, value:pololu controller number
      
    ATTRIBUTES:
    heartbeats -- dictionary -- key:nid, value:(timestamp)
    msgs -- dictionary -- a fake representation of a dictionary message, used so the pololu.Protocol can "dock" onto existing Cluster interfaces (provides the Module version)
    pna -- dictionary -- table of NodeID to ProtocolNodeAdaptor mappings

    FUTURE:
    buses -- may be a list of buses (Protocol can communicate with multiple buses by changing servonums)
    """
    AbstractProtocol.__init__(self,*args,**kw)
    if bus is None:
      self.bus = Bus()
    else:
      self.bus = bus
    if nodes is None:
      # By default, map all of the maestro to 0x10..0x1C
      nodes = dict(zip(range(0x10,0x1C),range(12)))
    self.nodes = nodes
    self.heartbeats = {} # Gets populated by update
    self.msgs = {}
    self.pnas = {}

    self.pololu_setup() # Must be called before the Maestro can begin to respond to commands

  def pololu_setup(self):
    """
    Initialize the Pololu Maestro device to receive commands using Pololu Mode
    """
    ##V: This seems to be in an odd location...
    self.bus.write( (self.POLOLU_BYTE,) )
    
  def send_cmd(self, cmd_type, nid, cmd):
    """
    Sends command to the Pololu Maestro via the Bus. 
    
    INPUTS:
    nid -- int -- Node ID to send the command to
    cmd -- tuple of ints -- tuple of integer command values to send
    cmd_type -- int -- Type of command (MiniSSC2, Pololu, and Compact types are supported)
    """

    channel = self.nodes[nid] # Extract channel from node ID to channel map

    # Correctly format the command
    ##V: This seems to be fishy...
    cmd = list(cmd)
    cmd.insert(0, cmd_type)
    cmd.insert(1, channel)
    cmd = tuple(cmd)
      
    self.bus.write(cmd)
    
  def hintNodes( self, nodes ):
    """
    Specify which nodes to expect on the bus
    """
    self.nodes = set(nodes)
    
  def update(self):
    """
    Updates the pololu.Protocol state that mimics the behaviour of can.Protocol. It updates
    timestamps of heartbeats heard on the bus.
    """
    # sets the of value all the entries in the heartbeats dictionary to the current time
    # This allows Cluster to believe that all the modules connected through Pololu are alive
    timestamp = now()
    dummydata = 0 # dummy data
    
    for nid in self.nodes.iterkeys():
      self.heartbeats[nid] = (timestamp, dummydata)
    
    # We have no incomplete messages
    return 0

  def generatePNA(self, nid):
    """
    Generates a pololu.ProtocolNodeAdaptor, associating a pololu protocol with 
    a specific node id and returns it
    """ 
    pna = ProtocolNodeAdaptor(self, nid)
    self.pnas[nid] = pna
    return pna

class Msg(object):
    """ 
    A concrete class representing a FAKE completed response to a Robotics Bus 
    Dictionary Object request.

    ATTRIBUTES:
      payload -- partial dictionary object assembled from segments
      timestamp -- time when full dictionary object response is received
      incomplete_msg -- contains individual segments of the dictionary object 
        response
    """
    def __init__(self, incomplete_msg, payload, timestamp):
        self.payload = payload
        self.timestamp = timestamp
        self.incomplete_msg = incomplete_msg

#Belongs in pololu.py -- mimics can.ProtocolNodeAdaptor
class ProtocolNodeAdaptor( AbstractNodeAdaptor ):
  """
  Utilizes the protocol along with nid to create 
  an interface for a specific module
  """

 # MiniSSCII Protocol Sync Value (must ALWAYS be 0xFF) specified by Pololu Documentation
  MINISSC2_BYTE = 0xFF
  
  # Compact Protocol Sync Value (must be 0x9F)
  COMPACT_BYTE = 0x8F
  
  # Pololu Protocol Sync Value (must be 0xAA)
  # This is also to initialize the Maestro to begin receiving commands using the PololuProtocol
  POLOLU_BYTE = 0xAA
    
  ##V: Need to put this in a proper location
  SLACK_MESSAGE = 0

  def __init__(self, protocol, nid):
    self.p = protocol
    self.nid = nid

  def go_slack(self):
    cmd = ( self.SLACK_MESSAGE, )
    self.p.send_cmd(self.COMPACT_BYTE, self.nid, cmd)

  def set_pos(self, target):
    """
    Sends a command to the Pololu device over serial via the
    pololu.Protocol.send_cmd()
    
    INPUT:
    cmd_type -- int -- command type specified by the Pololu User Manual 
    (see pololu.Protocol.send_cmd for more info.)
    
    data -- int -- the payload data to send to the module
    """
      
    # Essentially passes on the call to the protocol, includes the nid
    cmd = ( target, )
    self.p.send_cmd(self.MINISSC2_BYTE, self.nid, cmd)

  def get_typecode( self ):
    return "PolServoModule"
    
## Safety/range values goes in here
class ServoModule( AbstractServoModule ):
  """
  ServoModule Class has the basic functionality of ServoModules, with some exceptions listed below:
  
  - Pololu Modules cannot get_pos or is_slack
  - The Pololu Device allows for:
  - servo parameter settings
  - set speed
  - set neutral
  and various options for setting positions. We currently only use absolute 
  positions however. For more information refer to the Pololu User Manual
  on p.6
  """
  def __init__(self, node_id, typecode, pna, *argv, **kwarg):
    AbstractServoModule.__init__(self, node_id, typecode, pna, *argv, **kwarg )
    self._attr.update(
      go_slack="1R",
      set_pos="2W",
      get_pos="1R",
      is_slack="1R"
      )

    ##V: How should these be initialized? I just initialize them in set_pos / go_slack for now
    self.slack = None; # Initialized to True or False
    self.pos = None; # Initialized to start position of module

  @classmethod
  def _deg2pol(cls, angle):
    """
    Returns a correctly scaled module position
    
    INPUT:
    angle -- int -- between 9000 to -9000, in 100ths of degrees, 0 is neutral
    
    OUTPUT:
    corrected_angle -- int -- scaled between 0 and 255, 127 is neutral
    """
    scale = 1.0*(255-0)/(9000--9000) # Constant scale factor
    corrected_angle = int(scale*angle + 127)
    return corrected_angle
  
  def is_slack(self):
    """
    Returns true if the module is slack, none if go_slack has not been called yet.
    
    WARNING: This function does NOT actually read states from the pololu device, returns an attribute that is updated by calls to set_pos and go_slack. If any external communications fail, then this function may report incorrect states 
    """
    return self.slack
  
  def get_pos(self):
    """
    Returns the 'believed' position of the module, none if set_pos has not been called yet.
    
    WARNING: This function does NOT actually read states from the pololu device, returns an attribute that is updated by calls to set_pos and go_slack. If any external communications fail, then this function may report incorrect states
    """
    return self.pos

  def go_slack(self):
    """
    Equivalent of setting a ServoModule slack. This is referred to as "off"
    as specified in the Pololu User Manual under the Command 0
    """            
    # Send the command via the PNA
    self.pna.go_slack()

    # Module should now be slack
    self.slack = True

  def set_pos(self, pos):
    """
    Sets the position of a pololu module. 
    
    Uses the Pololu Set Absolute Position (Command 4)
    specified by the Pololu User Manual
    
    INPUT:
    pos -- int -- the desired position of the module, value between 9000 and -9000
    
    """ 
    # Ensures value is between 9000 and -9000 
    if pos > 9000 or pos < -9000:
      raise ValueError("Value out of bounds. Must be between 9000 and -9000.")

    corrected_pos = self._deg2pol(pos)

    # Send Position Command 
    self.pna.set_pos(corrected_pos)
      
    # Module should now not be slack
    self.slack = False

    # Module should now be at this position
    self.pos = pos
