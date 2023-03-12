#!/usr/bin/python
"""
This setup the topology in lab2-part3
"""
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.util import dumpNodeConnections
from mininet.link import Link, Intf, TCLink
import os 
from time import sleep
import sys

class Topology(Topo):
    
    core_sw = []
    edge_sw = []
    hosts = []
    
    def __init__(self):
        
        "Create Topology."
        self.numCore = N/2
        self.numEdge = N
        self.numHost = 2*((N/2)**2)
        
        # Initialize topology
        Topo.__init__(self)
          
        #### There is a rule of naming the hosts and switch, so please follow the rules like "h1", "h2" or "s1", "s2" for hosts and switches!!!!
        
        # Add core switches
        self.makeSwitch(self.numCore, 1, self.core_sw)
        
        # Add edge switches
        self.makeSwitch(self.numEdge, 2, self.edge_sw)
      
        # Add hosts
        for i in range(1, self.numHost+1):
            self.hosts.append(self.addHost('h'+str(i)))
        
        # Add links
        for i in range(0, self.numEdge):
            for j in range(0, self.numCore):
                self.addLink(self.core_sw[j], self.edge_sw[i])

        for i in range(0, self.numEdge):
            for j in range(0, self.numCore):
                self.addLink(self.edge_sw[i], self.hosts[(self.numCore * i) + j])
        
    def makeSwitch(self, m, l, switchType):
        for i in range(1, m+1):
            switchType.append(self.addSwitch('s' + str(l) + str(i)))

        
# This is for "mn --custom"
topos = { 'mytopo': ( lambda N : Topology() ) }


# This is for "python *.py"
if __name__ == '__main__':
    setLogLevel( 'info' )
            
    topo = Topology()
    net = Mininet(topo=topo, link=TCLink)       # The TCLink is a special setting for setting the bandwidth in the future.
    
    # 1. Start mininet
    net.start()
    
    # Wait for links setup (sometimes, it takes some time to setup, so wait for a while before mininet starts)
    print "\nWaiting for links to setup . . . .",
    sys.stdout.flush()
    for time_idx in range(3):
        print ".",
        sys.stdout.flush()
        sleep(1)
    
    # 2. Start the CLI commands
    info( '\n*** Running CLI\n' )
    CLI( net )
    
    # 3. Stop mininet properly
    net.stop()
    ### If you did not close the mininet, please run "mn -c" to clean up and re-run the mininet 