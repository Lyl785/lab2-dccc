from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp, ipv4, tcp, udp, icmp


class SimpleSwitch13(app_manager.RyuApp):
 OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

 def __init__(self, *args, **kwargs):
  super(SimpleSwitch13, self).__init__(*args, **kwargs)
  self.mac_to_port = {'10.0.0.1': '10:00:00:00:00:01', '10.0.0.2': '10:00:00:00:00:02', '10.0.0.3': '10:00:00:00:00:03', '10.0.0.4': '10:00:00:00:00:04'}


 def clockwise_outport(self, dpid, src, dst):
  if (dpid, dst) in {(1, '10:00:00:00:00:01'), (2, '10:00:00:00:00:02'), (3, '10:00:00:00:00:03'), (4, '10:00:00:00:00:04')}:
   return 1
  return 2


 def couter_clockwise_outport(self, dpid, src, dst):
  if (dpid, dst) in {(1, '10:00:00:00:00:01'), (2, '10:00:00:00:00:02'), (3, '10:00:00:00:00:03'), (4, '10:00:00:00:00:04')}:
   return 1
  return 3


 @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
 def switch_features_handler(self, ev):
  datapath = ev.msg.datapath
  ofproto = datapath.ofproto
  parser = datapath.ofproto_parser
  match = parser.OFPMatch()
  actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
  self.add_flow(datapath, 0, match, actions)


 def add_flow(self, datapath, priority, match, actions):
  ofproto = datapath.ofproto
  parser = datapath.ofproto_parser
  inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
  mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
  datapath.send_msg(mod)


 @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
 def _packet_in_handler(self, ev):
  msg = ev.msg
  datapath = msg.datapath
  ofproto = datapath.ofproto
  parser = datapath.ofproto_parser
  in_port = msg.match['in_port']
  pkt = packet.Packet(msg.data)
  eth = pkt.get_protocol(ethernet.ethernet)
  dst = eth.dst
  src = eth.src
  dpid = datapath.id
  pkt_arp = pkt.get_protocol(arp.arp)
  pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
  pkt_icmp = pkt.get_protocol(icmp.icmp)
  pkt_tcp = pkt.get_protocol(tcp.tcp)
  pkt_udp = pkt.get_protocol(udp.udp)

  if dst.split(":")[0] != '33' and not pkt_arp:
   print(pkt)

  # ARP
  if pkt_arp:
   mypkt = packet.Packet()
   mypkt.add_protocol(ethernet.ethernet(ethertype=0x0806, src=self.mac_to_port[pkt_arp.dst_ip], dst=src))
   mypkt.add_protocol(arp.arp(dst_mac = pkt_arp.src_mac, dst_ip = pkt_arp.src_ip, opcode = arp.ARP_REPLY, src_mac = self.mac_to_port[pkt_arp.dst_ip], src_ip = pkt_arp.dst_ip))
   self._send_packet(datapath, in_port, mypkt)

  elif pkt_ipv4:
    # ICMP
   if pkt_icmp:
     # calc out port
    print('[ICMP]', dpid, src, dst)
    out_port = self.clockwise_outport(dpid, src, dst)  # icmp go clockwise
    match = parser.OFPMatch(eth_type=0x0800,eth_dst=dst)
    actions = [parser.OFPActionOutput(port=out_port)]
    self.add_flow(datapath, 1, match, actions)
    self._send_packet(datapath, out_port, pkt)

   elif pkt_tcp:
    print('[TCP]')
    if pkt_tcp.dst_port == 8080 and (src == '10:00:00:00:00:02' or src == '10:00:00:00:00:04'):
     print(" [HTTP][TCP][H2/H4]")
     mypkt = packet.Packet()
     mypkt.add_protocol(ethernet.ethernet(ethertype=eth.ethertype, src=dst, dst=src))
     mypkt.add_protocol(ipv4.ipv4(src=pkt_ipv4.dst,dst=pkt_ipv4.src,proto=6)) # proto=6 for TCP
     mypkt.add_protocol(tcp.tcp(src_port=pkt_tcp.dst_port, dst_port=pkt_tcp.src_port, ack=pkt_tcp.seq + 1, bits=0b010100))

     self._send_packet(datapath, 1, mypkt)

     match = parser.OFPMatch(eth_type=0x0800, ip_proto=6, eth_src=src, tcp_dst=pkt_tcp.dst_port)
     actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
     self.add_flow(datapath, 100, match, actions)

    # NON-HTTP TCP # go clockwise
    else:

     print(' [normal TCP]', dpid, src, dst, "tcp_dst:", pkt_tcp.dst_port, "tcp_src:", pkt_tcp.src_port)
     out_port = self.clockwise_outport(dpid, src, dst) # icmp go clockwise

     match = parser.OFPMatch(eth_type=0x0800, ip_proto=6, eth_src=src, eth_dst=dst, tcp_dst=pkt_tcp.dst_port)
     actions = [parser.OFPActionOutput(port=out_port)]
     self.add_flow(datapath, 1, match, actions)
     self._send_packet(datapath, out_port, pkt)

   # UDP
   elif pkt_udp:
    print('[UDP]')

    if src != '10:00:00:00:00:01' and src != '10:00:00:00:00:04':
 # go counter-clockwise
     out_port = self.couter_clockwise_outport(dpid, src, dst) # icmp go clockwise

     match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, eth_src=src, eth_dst=dst, udp_dst=pkt_udp.dst_port)
     actions = [parser.OFPActionOutput(port=out_port)]
     self.add_flow(datapath, 1, match, actions)
     self._send_packet(datapath, out_port, pkt)

    else: # if HOST1 or HOST4 # drop
     print("[UDP] to drop")
     match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, eth_src=src, eth_dst=dst, udp_dst=pkt_udp.dst_port)
     actions = [] # drop
     self.add_flow(datapath, 10, match, actions)

   # don't send packet
   else:
    print(pkt)

 def _send_packet(self, datapath, port, pkt):
  ofproto = datapath.ofproto
  parser = datapath.ofproto_parser
  pkt.serialize()

  data = pkt.data
  actions = [parser.OFPActionOutput(port=port)]
  out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER, in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=data)
  datapath.send_msg(out)
