# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
import subprocess
import os
import logging
import sys

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet as packet_temp 
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import wifi
from ryu.lib.packet import tcp
from ryu.lib.packet import udp 
from ryu.lib.packet import ether_types


MODULE_PATH = "/home/mininet/v2x-slicing/single/folder_SHEM_mechanism"
sys.path.append(MODULE_PATH)
from SHEM_mechanism import Shem


    
class wifiAPP(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(wifiAPP, self).__init__(*args, **kwargs)
        
        self.n_Vehicles = 12
        self.threshold_load = 2
        self.threshold_rssi_handover = -70
        self.mn_wifi_dir = '/home/mininet/mininet-wifi/util/m'
        self.obj_SHEM = Shem(self.n_Vehicles,self.threshold_load,self.threshold_rssi_handover,self.mn_wifi_dir)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)
            print("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)
        
        msg = ev.msg
        pkt = packet_temp.Packet(msg.data)
        _ipv4 = pkt.get_protocol(ipv4.ipv4)

        if hasattr(_ipv4, 'proto'):
            if _ipv4.proto == 17 and _ipv4.dst == '192.168.0.200':  # UDP
                _wifi = pkt.get_protocol(wifi.WiFiMsg)

                self.obj_SHEM.monitoring(_wifi)

                