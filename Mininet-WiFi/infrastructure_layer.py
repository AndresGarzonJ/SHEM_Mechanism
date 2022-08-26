#!/usr/bin/python

"""
Este script tiene implementado 3 gnbs, cada uno con 3 slices
    cada gnb tiene las siguientes interfaces
        gnbj-wlan1                           IP=10.{j}.{k}.0/24  Mac = 02:00:00:00:j:00 k=0     Esta interfaz es deshabilitada
        gnbj-wlan1-0    -- Slice 1           IP=10.{j}.{k}.0/24  Mac = 02:00:00:00:j:01 k=1
        gnbj-wlan1-1    -- Slice 2           IP=10.{j}.{k}.0/24  Mac = 02:00:00:00:j:02 k=2
        gnbj-wlan1-2    -- Slice 3           IP=10.{j}.{k}.0/24  Mac = 02:00:00:00:j:02 k=2
        eth             -- 192.168.0.20{j}   donde j=id_gnb, k=id_slice 
        
        SLICING
            Slice 1 - Non-V2N, con 10M en 10.x.1.x en gnbj-wlan1-0
            Slice 2 - V2N-1,   con 25M en 10.x.2.x en gnbj-wlan1-1
            Slice 3 - V2N-2,   con 35M en 10.x.3.x en gnbj-wlan1-2

    Cada carro tiene una sola interfaz wlan. 
        car_id  car0, entonces car_id=0
        IP      10.j.k.{car_id + 100}
        MAC     02:00:00:00:{car_id}:00 , car_id en base 16


Tiene 1 un servidor Radius          IP: 192.168.0.210

Tiene 3 servidores de aplicaciones       
        sNon-V2N                    IP: 192.168.0.220
        sv2n_1                      IP: 192.168.0.221
        sv2n_2                      IP: 192.168.0.222

Para ejecutar este script debe:

    #Terminal 1
    sudo systemctl stop  network-manager.service
    sudo systemctl stop  apache2.service
    sudo systemctl stop  apache-htcacheclean.service
    alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu
    sudo mn -c
    sudo python test_2_802_11_rsna_6cars.py -sumo -conSlicing -gnb1ConSlicing -test1

    # Terminal 2
    alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu
    source bin/activate
    cd src && alias python=python2
    sudo PYTHONPATH=. ./bin/ryu-manager ryu/app/wifi.py ryu/app/simple_switch_13.py
    #deactivate  

    # Termianl Opcional
    sudo su
    ps aux  --sort pmem
    killall python && sync && echo 3 > /proc/sys/vm/drop_caches
    cd /home/mininet/mininet-wifi/util/
    ./m car0 wpa_cli -i car0-wlan0

    # Termianl 4
    sudo su
    cd /home/mininet/mininet-wifi/util/
    ./m car0 iw dev car0-wlan0 link




############### Test1 - Network Slicing

#/home/mininet/mininet-wifi/util/m car0 iperf -c 192.168.0.220 -p 5566 -i 1 -t 300 >> /home/mininet/v2x-slicing/single/ryu/data-log/car0_iperf.log

# Crear las terminales
    alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu/ 
    sudo python test1_NS_iperf.py {id_car}



############### Note
inputs_collection.py es ejecutado por los carros para la comunicacion 
con el controlador SDN. Este script recibe 4 banderas

    inputs_collection.py flag1 flag2 flag3 flag4
        flag1   Son los numeros de la mac del carro - 02:00:00:00:{flag1}:00
        flag2   threshold_latency slice Non-V2N
        flag3   threshold_latency slice V2N-1
        flag4   threshold_latency slice V2N-2


"""
import os, sys
import time
from sys import version_info as py_version_info
from mininet.node import RemoteController 
from mininet.term import makeTerm, cleanUpScreens
from mininet.log import setLogLevel
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from mininet.link import TCLink
from mn_wifi.sumo.runner import sumo
from mininet.log import error, debug, info

# Conexion entre AP-Controlador https://gist.github.com/ramonfontes/7beddaf5eebbfd35750efd7974bf22e4
#sudo util/install.sh -3f installs Bofuss
from mn_wifi.node import UserAP

def topology(flag,flag2,flag3,flag4):
    
    os.system('rm radius.txt')
    os.system('rm /run/hostapd/gnb*')
    os.system('rm log_wpa/*')
    
    ######################## Parameters for testing
    n_Cars = 12         # Total number of vehicles in the network
    n_Cars_test = 6     # Vehicles that operate with our mechanism
    nSlices = 3

    reqQoS_Apps = {} # [latency,bw_slice, bw_car]
    reqQoS_Apps[1]=[50,100000,10000] # Non-V2N App
    reqQoS_Apps[2]=[20,250000,25000] # V2N-1 App
    reqQoS_Apps[3]=[10,300000,30000] # V2N-2 App

    reqQoS_Cars = {}
    reqQoS_Cars[0]=[reqQoS_Apps[1][0]]
    reqQoS_Cars[1]=[reqQoS_Apps[1][0]]
    reqQoS_Cars[2]=[reqQoS_Apps[2][0]]
    reqQoS_Cars[3]=[reqQoS_Apps[2][0]]
    reqQoS_Cars[4]=[reqQoS_Apps[3][0]]
    reqQoS_Cars[5]=[reqQoS_Apps[3][0]]

    ######################## Create a network infrastructure
    debug("*** Create a network\n")
    net = Mininet_wifi(controller=RemoteController,link=wmediumd, wmediumd_mode=interference,accessPoint=UserAP)

    debug("*** Creating vehicles\n")
    cars = []
    for x in range(0, n_Cars):
        cars.append(x)

    for x in range(0, n_Cars_test):
        cars[x] = net.addCar('car%s' %(int(x)),  wlans=1, encrypt='wpa2', range = 100,
            radius_passwd='sdnteam', radius_identity='joe%s'% int(x), inNamespace=True)
        time.sleep(0.5)
    
    for x in range(n_Cars_test, n_Cars):
        cars[x] = net.addCar('car%s' %(int(x)),  wlans=1, encrypt='wpa2', range = 100,
            radius_passwd='sdnteam', radius_identity='joe%s'% int(x), inNamespace=True,
            bgscan_threshold=-60, s_interval=3, l_interval=6, bgscan_module="simple") 
        time.sleep(0.5)
        
    debug("*** Creating gNBs\n")
    kwargs = {'protocols':'OpenFlow13', 'ssid': 'handover', 'encrypt': 'wpa2', 'mode': 'g','passwd': '123456789a','authmode': '80211r', 'ieee80211r':'yes','mobility_domain': 'a1b2', 'radius_server': '192.168.0.210'}
    
    gnb1 = net.addAccessPoint('gnb1', channel='1', vssids=['handover,handover,handover'], bssid_list={0:('gnb1','02:00:00:00:%s:00' % format(n_Cars,'02x'),'192.168.0.201',n_Cars,nSlices,flag2,flag3),1:('gnb2','02:00:00:00:%s:00' % format(n_Cars+1,'02x'),'0')}, dpid='1', position='1150,30,0', **kwargs)
    time.sleep(1)
    gnb2 = net.addAccessPoint('gnb2', channel='1', vssids=['handover,handover,handover'], bssid_list={0:('gnb2','02:00:00:00:%s:00' % format(n_Cars+1,'02x'),'192.168.0.202',n_Cars,nSlices,flag2,flag3),1:('gnb1','02:00:00:00:%s:00' % format(n_Cars,'02x'),'0')}, dpid='2', position='1390,30,0', **kwargs)
    
    debug("*** Creating switches\n")
    sre21 = net.addSwitch('sre21', dpid='6')
    sbr20 = net.addSwitch('sbr20', dpid='7')
    sat10 = net.addSwitch('sat10', dpid='8')
    s13 = net.addSwitch('s13', dpid='9')
    s23 = net.addSwitch('s23', dpid='10')
    
    debug("*** Creating servers\n")
    srad1 = net.addHost('srad1',         ip='192.168.0.210/24', mac='22:22:22:22:22:01')    # FreeRadius Server
    sNon-V2N =  net.addHost('sNon-V2N',  ip='192.168.0.220/24', mac='33:33:33:33:33:01')    # Non-V2N Application Server
    sv2n_1 =  net.addHost('sv2n_1',  ip='192.168.0.221/24', mac='44:44:44:44:44:01')        #V2N-1 Application Server
    sv2n_2 =  net.addHost('sv2n_2',  ip='192.168.0.222/24', mac='55:55:55:55:55:01')        #V2N-2 Application Server
    time.sleep(1)

    debug("*** Connection to Ryu controller\n")
    c1 = net.addController('c1', controller=RemoteController, ip='127.0.0.1', port=6653)
    time.sleep(1)
        
    debug("*** Configuring Propagation Model\n")
    # https://mininet-wifi.github.io/propagation/
    net.setPropagationModel(model="logDistance", exp=3.1)
    time.sleep(1)

    debug("*** Configuring wifi nodes\n")
    net.configureWifiNodes()
    time.sleep(1)
    
    debug("*** Creating links")
    net.addLink(s13, sre21,  1, 2)
    net.addLink(s13, sat10,  2, 1)
    net.addLink(s23, sre21,  1, 3)
    net.addLink(s23, sat10,  2, 2)
    net.addLink(sre21, sbr20,  1, 1)
    net.addLink(sbr20, sNon-V2N, 2, 0)
    net.addLink(sbr20, sv2n_1, 3, 0)
    net.addLink(sbr20, sv2n_2, 4, 0)
    net.addLink(sat10, srad1,  6, 0)
    time.sleep(0.5)
    net.addLink(gnb1, s13, 5 , 3)
    time.sleep(0.5)
    net.addLink(gnb2, s23, 5, 3)
    time.sleep(0.5)


    ######################## Connection with SUMO
    net.useExternalProgram(program=sumo, port=8813,
                           config_file='/home/mininet/mininet-wifi/mn_wifi/sumo/data/scenario_2gnb.sumocfg',
                           extra_params=["--breakpoints 00:00:01  --start --delay 1000 --window-size 650,600 --window-pos 1700,100"], clients=1, exec_order=0)
    
    ######################## Start the network infrastructure
    debug("*** Start the network infrastructure")
    net.build()
    time.sleep(2)
    c1.start()
    time.sleep(2)
    s13.start([c1])
    time.sleep(1)
    s23.start([c1])
    time.sleep(1)
    sre21.start([c1])
    time.sleep(1)
    sbr20.start([c1])
    time.sleep(1)
    sat10.start([c1])
    time.sleep(1)
    gnb1.start([c1])
    time.sleep(1)
    gnb2.start([c1])
    time.sleep(1)
    
    ######################## Setting IP addressing
    for x in range(0, n_Cars):
        cars[x].setIP('10.1.1.%s/24' % (x+100), intf="car%s-wlan0" % (x))
    
    #cars[0].setIP('10.1.1.100/24', intf="car0-wlan0")
    #cars[1].setIP('10.1.1.101/24', intf="car1-wlan0")
    #cars[2].setIP('10.1.2.102/24', intf="car2-wlan0")
    #cars[3].setIP('10.1.2.103/24', intf="car3-wlan0")
    #cars[4].setIP('10.1.3.104/24', intf="car4-wlan0")
    #cars[5].setIP('10.1.3.105/24', intf="car5-wlan0")

    gnb1.cmd('ifconfig gnb1-wlan1   10.1.0.1 netmask 255.255.255.0')
    gnb1.cmd('ifconfig gnb1-wlan1-0 10.1.1.1 netmask 255.255.255.0')
    gnb1.cmd('ifconfig gnb1-wlan1-1 10.1.2.1 netmask 255.255.255.0')
    gnb1.cmd('ifconfig gnb1-wlan1-2 10.1.3.1 netmask 255.255.255.0')
    gnb1.cmd('ifconfig gnb1-eth5    10.1.4.1 netmask 255.255.255.0')
    gnb1.cmd('ifconfig gnb1-eth5:0  192.168.0.201 netmask 255.255.255.0')
    time.sleep(1)

    gnb2.cmd('ifconfig gnb2-wlan1   10.2.0.1 netmask 255.255.255.0')
    gnb2.cmd('ifconfig gnb2-wlan1-0 10.2.1.1 netmask 255.255.255.0')
    gnb2.cmd('ifconfig gnb2-wlan1-1 10.2.2.1 netmask 255.255.255.0')
    gnb2.cmd('ifconfig gnb2-wlan1-2 10.2.3.1 netmask 255.255.255.0')
    gnb2.cmd('ifconfig gnb2-eth5    10.2.4.1 netmask 255.255.255.0')
    gnb2.cmd('ifconfig gnb2-eth5:0 192.168.0.202 netmask 255.255.255.0')
    time.sleep(1)

    # Enable - Linux IP forwarding
    gnb1.cmd('sysctl net.ipv4.ip_forward=1')
    time.sleep(0.5)
    gnb2.cmd('sysctl net.ipv4.ip_forward=1')
    time.sleep(0.5)

    ######################## Enabling monitor interface for beacon sniffing
    for x in range(0, n_Cars_test):    
        cars[x].cmd('iw dev car%s-wlan0 interface add car%s-mon0 type monitor'% (x,x))
        time.sleep(1)
        cars[x].cmd('ip link set car%s-mon0 up'% x)
        time.sleep(1)
    

    ######################## Starting FreeRadius server
    debug("*** Starting FreeRadius server")
    os.system('xterm -hold -title "srad1" -e "/home/mininet/mininet-wifi/util/m srad1 freeradius -X" &')
    time.sleep(1)

    ######################## Establishing Flow Rules
    # Redirect to Ryu controller, the IP packets sent by the car (monitoring) 
    s13.cmd('ovs-ofctl add-flow s13 in_port=3,priority=65535,dl_type=0x0800,nw_dst=192.168.0.200,actions=output:controller')
    s23.cmd('ovs-ofctl add-flow s23 in_port=3,priority=65535,dl_type=0x0800,nw_dst=192.168.0.200,actions=output:controller')
    
    sat10.cmd('ovs-ofctl add-flow sat10 in_port=1,actions=output:6')
    sat10.cmd('ovs-ofctl add-flow sat10 in_port=2,actions=output:6')
    
    s13.cmd('ovs-ofctl add-flow s13 in_port=3,priority=65535,dl_type=0x0800,nw_dst=192.168.0.210,actions=output:2')
    s13.cmd('ovs-ofctl add-flow s13 in_port=2,actions=output:3')
    s13.cmd('ovs-ofctl add-flow s13 in_port=1,actions=output:3')
    
    s23.cmd('ovs-ofctl add-flow s23 in_port=3,priority=65535,dl_type=0x0800,nw_dst=192.168.0.210,actions=output:2')
    s23.cmd('ovs-ofctl add-flow s23 in_port=2,actions=output:3')
    s23.cmd('ovs-ofctl add-flow s23 in_port=1,actions=output:3')
    
    sre21.cmd('ovs-ofctl add-flow sre21 in_port=2,actions=output:1')
    sre21.cmd('ovs-ofctl add-flow sre21 in_port=3,actions=output:1')
    
    s13.cmd('ovs-ofctl add-flow s13 in_port=3,dl_type=0x0800,nw_dst=192.168.0.220,actions=output:1')
    s23.cmd('ovs-ofctl add-flow s23 in_port=3,dl_type=0x0800,nw_dst=192.168.0.220,actions=output:1')
    s13.cmd('ovs-ofctl add-flow s13 in_port=3,dl_type=0x0800,nw_dst=192.168.0.221,actions=output:1')
    s23.cmd('ovs-ofctl add-flow s23 in_port=3,dl_type=0x0800,nw_dst=192.168.0.221,actions=output:1')
    s13.cmd('ovs-ofctl add-flow s13 in_port=3,dl_type=0x0800,nw_dst=192.168.0.222,actions=output:1')
    s23.cmd('ovs-ofctl add-flow s23 in_port=3,dl_type=0x0800,nw_dst=192.168.0.222,actions=output:1')

    sbr20.cmd('ovs-ofctl add-flow sbr20 in_port=2,actions=output:1')   
    sbr20.cmd('ovs-ofctl add-flow sbr20 in_port=3,actions=output:1')   
    sbr20.cmd('ovs-ofctl add-flow sbr20 in_port=4,actions=output:1')
    sbr20.cmd('ovs-ofctl add-flow sbr20 in_port=1,dl_type=0x0800,nw_dst=192.168.0.220,actions=output:2')
    sbr20.cmd('ovs-ofctl add-flow sbr20 in_port=1,dl_type=0x0800,nw_dst=192.168.0.221,actions=output:3')
    sbr20.cmd('ovs-ofctl add-flow sbr20 in_port=1,dl_type=0x0800,nw_dst=192.168.0.222,actions=output:4')
    time.sleep(1)

    
    ######################## Test1 - Verify Network Slicing
    if flag4 == '-test1':
        os.system('xterm -hold -title "sNon-V2N" -e "/home/mininet/mininet-wifi/util/m sNon-V2N iperf -p 5001 -s -u" &')
        os.system('xterm -hold -title "sv2n_1"   -e "/home/mininet/mininet-wifi/util/m sv2n_1   iperf -p 5002 -s -u" &')
        os.system('xterm -hold -title "sv2n_2"   -e "/home/mininet/mininet-wifi/util/m sv2n_2   iperf -p 5003 -s -u" &')

    
    ######################## Establishing Flow Rules and data rate limiting according to the BW of the applications
    #### gNB1
    gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=1 drop:rate=%s' % reqQoS_Apps[1][2])
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=2 drop:rate=%s' % reqQoS_Apps[2][2])
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=3 drop:rate=%s' % reqQoS_Apps[3][2])
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=4 drop:rate=%s' % reqQoS_Apps[1][2])
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=5 drop:rate=%s' % reqQoS_Apps[2][2])
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=6 drop:rate=%s' % reqQoS_Apps[3][2])
    time.sleep(0.5)
    
    #Slice Non-V2N
    gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=3 in_port=2 meter:4 apply:output=5')
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=6 in_port=5,eth_type=0x800,ip_dst=10.1.1.0/24 meter:1 apply:output=2')
    time.sleep(0.5)        
    #Slice V2N-1
    gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=2 in_port=3 meter:5 apply:output=5')
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=5 in_port=5,eth_type=0x800,ip_dst=10.1.2.0/24 meter:2 apply:output=3')
    time.sleep(0.5)
    #Slice V2N-2
    gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=1 in_port=4 meter:6 apply:output=5')
    time.sleep(0.5)
    gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=4 in_port=5,eth_type=0x800,ip_dst=10.1.3.0/24 meter:3 apply:output=4')
    time.sleep(0.5)

    
    #### gNB2
    gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=1 drop:rate=%s' % reqQoS_Apps[1][2])
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=2 drop:rate=%s' % reqQoS_Apps[2][2])
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=3 drop:rate=%s' % reqQoS_Apps[3][2])
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=4 drop:rate=%s' % reqQoS_Apps[1][2])
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=5 drop:rate=%s' % reqQoS_Apps[2][2])
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=6 drop:rate=%s' % reqQoS_Apps[3][2])
    time.sleep(0.5)
    
    #Slice Non-V2N
    gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=3 in_port=2 meter:4 apply:output=5')
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=6 in_port=5,eth_type=0x800,ip_dst=10.2.1.0/24 meter:1 apply:output=2')
    time.sleep(0.5)
    #Slice V2N-1
    gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=2 in_port=3 meter:5 apply:output=5')
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=5 in_port=5,eth_type=0x800,ip_dst=10.2.2.0/24 meter:2 apply:output=3')
    time.sleep(0.5)
    #Slice V2N-2
    gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=1 in_port=4 meter:6 apply:output=5')
    time.sleep(0.5)
    gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=4 in_port=5,eth_type=0x800,ip_dst=10.2.3.0/24 meter:3 apply:output=4')
    time.sleep(0.5)


    ######################## Configuring routing on the servers
    debug( "*** Creating initial basic flows in network" )
    #To gNB1
    srad1.cmd('ip route add 10.1.0.0/16 via 192.168.0.201')
    sNon-V2N.cmd('ip  route add 10.1.1.0/24 via 192.168.0.201')
    sv2n_1.cmd('ip  route add 10.1.2.0/24 via 192.168.0.201')
    sv2n_2.cmd('ip  route add 10.1.3.0/24 via 192.168.0.201')
    
    #To gNB2
    srad1.cmd('ip route add 10.2.0.0/16 via 192.168.0.202')
    sNon-V2N.cmd('ip  route add 10.2.1.0/24 via 192.168.0.202')
    sv2n_1.cmd('ip  route add 10.2.2.0/24 via 192.168.0.202')
    sv2n_2.cmd('ip  route add 10.2.3.0/24 via 192.168.0.202')
    

    
    ######################## Configuring temporary routing in vehicles
    for x in range(0, n_Cars):   
        cars[x].cmd('ip route add 192.168.0.0/24 dev car%s-wlan0' % x)
        cars[x].cmd('ip route add 10.1.0.0/16 dev car%s-wlan0' % x)
    
    ######################## Execute the script in the vehicles, which collects and sends the inputs for our mechanism.
    for x in range(0, n_Cars_test):   
        os.system('xterm -hold -title "car%s" -e "alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu && source bin/activate && /home/mininet/mininet-wifi/util/m car%s python /home/mininet/v2x-slicing/single/ryu/inputs_collection.py %s %s %s %s %s %s %s %s" &' % (x,x,x,n_Cars,reqQoS_Cars[x][0],reqQoS_Apps[1][0],reqQoS_Apps[2][0],reqQoS_Apps[3][0]))
        time.sleep(1)
    
    
    debug("*** Running CLI\n")
    CLI(net)

    debug("*** Stopping network\n")
    os.system('sudo systemctl stop freeradius.service')
    os.system('sudo systemctl stop apache2.service')
    os.system('sudo fuser -k 1812/udp')
    os.system('sudo fuser -k 6653/tcp')
    os.system('pkill freeradius')
    if py_version_info < (3, 0):
        os.system('pkill -f SimpleHTTPServer')
    else:
        os.system('pkill -f http.server')
    os.system('pkill xterm')
    os.system('pkill -f \"xterm -title\"')
    net.stop()
    

if __name__ == '__main__':
    flag = sys.argv[1]
    flag2 = sys.argv[2]
    flag3 = sys.argv[3]
    flag4 = sys.argv[4]
    setLogLevel('debug')
    os.system('sudo fuser -k 1812/udp')
    os.system('sudo systemctl stop freeradius.service')
    os.system('fuser -k 6653/tcp')    
    os.system('rm -f radius.txt;')
    time.sleep(1)
    topology(flag,flag2,flag3,flag4)