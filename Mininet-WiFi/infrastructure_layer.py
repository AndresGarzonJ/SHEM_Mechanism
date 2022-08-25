#!/usr/bin/python

"""
#########################################################
NOTA:   El traspaso se puede reducir aun más cuando se limitan las frecuencias a escanear
        En /home/mininet/mininet-wifi/mn_wifi/link.py/def wpaFile(self, ap_intf):
                cmd += '   scan_freq=2412\n'
                cmd += '   freq_list=2412\n'
#########################################################
Password MySQL: kamisama123

Este script tiene implementado 5 gnbs, cada uno con 3 slices
    cada gnb tiene las siguientes interfaces
        gnbj-wlan1                  IP=10.j.k.0/24  Mac = 02:00:00:00:j:00 k=0     NO se puede conectar a esta interfaz
        gnbj-wlan1-0    -- slice1   IP=10.j.k.0/24  Mac = 02:00:00:00:j:01 k=1
        gnbj-wlan1-1    -- slice2   IP=10.j.k.0/24  Mac = 02:00:00:00:j:02 k=2
        gnbj-wlan1-2    -- slice3   IP=10.j.k.0/24  Mac = 02:00:00:00:j:02 k=2

        eth             -- 192.168.0.20j   donde j=id_gnb, k=id_slice
        
        SLICING
            Slicing 1 - sv2n_1, con 10M en 10.x.1.x en gnbj-wlan1-0
            Slicing 2 - sv2n_2, con 25M en 10.x.2.x en gnbj-wlan1-1
            Slicing 3 - sv2n_3, con 35M en 10.x.3.x en gnbj-wlan1-2

Tiene 3 carros
    Cada carro tiene una sola interfaz wlan. 
        car_id  car0, entonces car_id=0
        IP      10.j.k.{car_id + 100}
        MAC     02:00:00:00:{car_id}:00


Tiene 1 un servidor Radius          IP: 192.168.0.210

Tiene 3 servidores MEC (sv2n)       
        sv2n_1                      IP: 192.168.0.220
        sv2n_2                      IP: 192.168.0.221
        sv2n_3                      IP: 192.168.0.222

Para ejecutar este script debe tener en cuenta las siguientes 3 banderas
    sudo python proyecto.py flag1 flag2 flag3
    sudo python proyecto.py -sumo -conSlicing -gnb1ConSlicing
        -sumo           -- habilita el mapa sumo
        -conSlicing     -- habilita que los gnb2,3,4,5 tengan 3 slice cada uno
        -gnb1ConSlicing -- habilita que el gnb1 tengan 1 slice cada uno


#########################################################
Comandos: 

Iniciales
sudo systemctl stop  network-manager.service
sudo systemctl   stop  apache2.service
sudo systemctl stop  apache-htcacheclean.service

# Terminal 1
alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu
sudo mn -c
sudo python test_1_infrastructure_layer.py -sumo -conSlicing -gnb1ConSlicing
sudo python test_1_infrastructure_layer.py -sumo -conSlicing -gnb1ConSlicing 2> log_ejecucion.txt

# Terminal 2
alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu
source bin/activate
#deactivate
cd src && alias python=python2
sudo PYTHONPATH=. ./bin/ryu-manager ryu/app/wifi.py ryu/app/simple_switch_13.py
sudo PYTHONPATH=. ./bin/ryu-manager --ofp-tcp-listen-port 6653 ryu/app/wifi.py ryu/app/simple_switch_13.py

# Termianl 3
sudo su
ps aux  --sort pmem
killall python && sync && echo 3 > /proc/sys/vm/drop_caches
cd /home/mininet/mininet-wifi/util/
./m car0 wpa_cli -i car0-wlan0

# Termianl 4
sudo su
cd /home/mininet/mininet-wifi/util/
./m car0 iw dev car0-wlan0 link

# Termianl 5
sudo su
cd /home/mininet/mininet-wifi/util/
./m gnb3 hostapd_cli -i gnb3-wlan1

############################ Opcionales
cd /home/mininet/mininet-wifi/ && sudo make install

# check versions
pip list
dpctl -V
freeradius -v
ovs-vswitchd --version
ovs-ofctl --version
iperf --version
mn --version
uname -a
wpa_supplicant -v
hostapd -v


# Check versions - En el entorno virtual de Ryu
cd /home/mininet/v2x-slicing/single/ryu/src/bin
sudo python ryu-manager --version
pip list

#########################################################
############### Prueba Network Slicing ##################
#########################################################
#/home/mininet/mininet-wifi/util/m car0 iperf -c 192.168.0.220 -p 5566 -i 1 -t 300 >> /home/mininet/v2x-slicing/single/ryu/data-log/car0_iperf.log

sudo su

# Crear las terminales
    # opcional puede agregar "-i 1" para que iperf muestre segundo a segundo los datos tx
    /home/mininet/mininet-wifi/util/m sv2n_1 iperf -p 5001 -s -u
    /home/mininet/mininet-wifi/util/m car0 iperf -p 5001 -t 5 -c 192.168.0.220 -u -b54M

    /home/mininet/mininet-wifi/util/m sv2n_2 iperf -p 5002 -s -u
    /home/mininet/mininet-wifi/util/m car0 iperf -p 5002 -t 5 -c 192.168.0.221 -u -b54M

    /home/mininet/mininet-wifi/util/m sv2n_3 iperf -p 5003 -s -u
    /home/mininet/mininet-wifi/util/m car0 iperf -p 5003 -t 5 -c 192.168.0.222 -u -b54M

# Ejecutar el script
    alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu/ 
    sudo python prueba_iperf.py {id_car}


# Si desea cambiar de gNB/slice
    ./m car0 wpa_cli -i car0-wlan0 roam 00:00:00:05:00:02
    ./m gnb1 hostapd_cli -i gnb1-wlan1 deauthenticate 00:00:00:00:00:01

    ./m car0 ifconfig car0-wlan0 10.1.0.101
    ./m car0 ip route add 192.168.0.0/24 via 10.1.0.1
    ./m car0 ip route del 192.168.0.0/24
    ./m car0 ifconfig car0-wlan0 10.1.2.101
    ./m car0 ip route add 192.168.0.0/24 via 10.1.2.1

#########################################################
Notas:

El script car1.py es ejecutado por los carros para la comunicacion con el controlador SDN. Este script
recibe (en su ejecucion) 5 banderas

    car1.py flag1 flag2 flag3 flag4 flag5 flag6
        flag1   Son los numeros de la mac del carro - 02:00:00:00:{flag1}:00
        flag2   threshold_latency slice 1
        flag3   threshold_latency slice 2
        flag4   threshold_latency slice 3
        flag5   conSlicing, esto evita que las beacom enviadas de gnbj-wlan1, se han enviadas al controlador,
                es decir, {gnb2-wlan1,gnb3-wlan1,gnb4-wlan1,gnb5-wlan1} NO sera un canditado para hacer el traspaso.
        flag6   gnb1ConSlicing, esto evita que las beacom enviadas de gnb1-wlan1, se han enviadas al controlador,
                es decir, gnb1-wlan1 NO sera un canditado para hacer el traspaso.

alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu && source bin/activate && /home/mininet/mininet-wifi/util/m car0 python /home/mininet/v2x-slicing/single/ryu/car1.py 1 50 20 10 -conSlicing -gnb1ConSlicing

sudo fuser -k 6653/tcp

wlan.sa == 02:00:00:00:01:00 || wlan.da == 02:00:00:00:01:00 || wlan.da == 02:00:00:00:04:02|| wlan.da == 02:00:00:00:03:01

wlan.sa == 02:00:00:00:01:00 || wlan.da == 02:00:00:00:01:00
wlan.fc.type == 0 && wlan.fc.subtype==8

deactivate

alias python=python2  && /home/mininet/mininet-wifi/util/m gnb3 hostapd_cli -i gnb3-wlan1

#Terminal 3
sudo fuser -k 6653/tcp
#########################################################
+++++ Crear simulación de tráfico
https://www.youtube.com/watch?v=XY-YJ6FtTX4
sumo.dlr.de/docs/Tutorials/Driving_in_Circles.html

++++ Crear retorno Sumo
1. Ejecutar en la terminal -- para crear el mapa personalizado
/usr/share/sumo/bin/netedithighway.secondary

2. Cargar la red

3. Añadir otra carretera con sus propios nodos

4. Luego con "Move Mode" ubica los nodos en la posicion deseada, sin fucionar los nodos

5. En *.net.xml, añadir la conección entre los dos extremos (calles) que quieres hacer el retorno
    <!-- Retorno -->
    <connection from="rcalle0" to="calle0" fromLane="1" toLane="1" dir="l" state="m"/>

6. Crear el *.add.xml
#########################################################

Handover example supported by bgscan (Background scanning) and wmediumd.

ieee 802.11r can be enabled adding the parameters below:

dpid='8', datapath='user',  mobility_domain='a1b2', 

e.g. ap1 = net.addAccessPoint('ap1', ..., 
mobility_domain='a1b2',...)

Consider https://w1.fi/cgit/hostap/plain/wpa_supplicant/wpa_supplicant.conf
for more information about bgscan
"""
import os, sys
import time
from sys import version_info as py_version_info

from mininet.node import RemoteController 
#from mininet.node import Controller
#OVSSwitch: a switch using the Open vSwitch OpenFlow-compatible switch implementation (openvswitch.org).
#from mn_wifi.node import OVSSwitch, OVSKernelAP #--- OVSKernelAP = OVSAP --ovs no es compatible con inNamespace 
#from mn_wifi.node import OVSSwitch, UserAP #---UserAP=BOFUSS   https://github.com/CPqD/ofsoftswitch13
#---OVSKernelSwitch = OVSSwitch

# Conexion entre AP-Controlador https://gist.github.com/ramonfontes/7beddaf5eebbfd35750efd7974bf22e4
#sudo util/install.sh -3f installs Bofuss

from mininet.term import makeTerm, cleanUpScreens
from mininet.log import setLogLevel #, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from mininet.link import TCLink
from mn_wifi.sumo.runner import sumo
from mininet.log import error, debug, info

from mn_wifi.node import UserAP
MODULE_PATH_0 = "/home/mininet/v2x-slicing/single/ryu/lib/python2.7/site-packages/mysql"
sys.path.append(os.path.dirname(os.path.expanduser(MODULE_PATH_0)))
import mysql.connector
from BD.conn import MySQLDB
from random import randint

### Este codigo esta haciendo ping entre
# sta --- gnb --- srad1
# sta --- gnb --- sv2n_1


def topology(flag,flag2,flag3):
    
    os.system('rm radius.txt')
    os.system('rm /run/hostapd/gnb*')
    #os.system('rm data-log/*')
    os.system('rm log_wpa/*')
    #os.system('rm hostapd-gnb*')
    #os.system('rm /etc/hostapd-gnb*')

    ######################## Test ############################
    ######################## Test ############################
    # Al cambiar el numero de carros, entonces debe modificar - para habilitar los carros 
    # /home/mininet/mininet-wifi/mn_wifi/sumo/data/scenario.rou.xml
    # link.py           ---   cmd += '\nmax_num_sta=5' y cmd += '   scan_freq=2412\n' y cmd += '   freq_list=2412\n'
    # ryu/app/wifi.py   ---   getAttr.n_Cars y getAttr.threshold_load)
    # hostapd-gnb1-wlan1.accept
    # modificar/habilitar interfaces monitor de los carros
    # modificar la creacion de carros
    # terminales n_Cars_test de car1_thread.py        
    n_Cars = 2
    n_Cars_test = 1
    nSlices = 3

    reqQoS_V2N = {} # [threshold_latency,bw_slice, bw_car]
    reqQoS_V2N[1]=[50,100000,10000] # Prioridad baja
    reqQoS_V2N[2]=[20,250000,25000] # Prioridad Media
    reqQoS_V2N[3]=[10,300000,30000] # Prioridad Alta

    reqQoS_Cars = {}
    #for x in range(0, n_Cars_test):
    #    reqQoS_Cars[x]=[reqQoS_V2N[randint(2,3)][0]]
    reqQoS_Cars[0]=[reqQoS_V2N[1][0]]
    reqQoS_Cars[1]=[reqQoS_V2N[1][0]]
    reqQoS_Cars[2]=[reqQoS_V2N[2][0]]
    reqQoS_Cars[3]=[reqQoS_V2N[2][0]]
    reqQoS_Cars[4]=[reqQoS_V2N[3][0]]
    reqQoS_Cars[5]=[reqQoS_V2N[3][0]]

    debug("*** Create a network\n")
    #net = Mininet_wifi(controller=RemoteController, accessPoint=UserAP,allAutoAssociation=True)#,allAutoAssociation=False) #autoAssociation=False,
    net = Mininet_wifi(controller=RemoteController,link=wmediumd, wmediumd_mode=interference,accessPoint=UserAP)#,autoAssociation=False) #allAutoAssociation=True
    #disabledAutoAssociation=True

    #link=wmediumd, wmediumd_mode=interference

    debug("*** Creating nodes\n")

    """
    dhclient car0-wlan0
    car0.pexec('"dhclient car0-wlan0" &')
    """
    

    cars = []
    if flag == '-sumo':
        #cars = []
        for x in range(0, n_Cars):
            cars.append(x)

        for x in range(0, n_Cars_test):
            cars[x] = net.addCar('car%s' %(int(x)),  wlans=1, encrypt='wpa2', range = 100,
                radius_passwd='sdnteam', radius_identity='joe%s'% int(x), inNamespace=True)
        #inNamespace=True  -- Permite aplicar el limite de velocidad de datos -- Network Slicing
        #inNamespace=False -- Permite capturar paquetes con Wireshark
        
        for x in range(n_Cars_test, n_Cars):
            cars[x] = net.addCar('car%s' %(int(x)),  wlans=1, encrypt='wpa2', range = 100,
                radius_passwd='sdnteam', radius_identity='joe%s'% int(x), inNamespace=True,
                bgscan_threshold=-60, s_interval=3, l_interval=6, bgscan_module="simple") 
                # ip='10.1.0.%s/24'%(int(x)+101), mac='02:00:00:00:01:%02d:00' % (int(x)+1), 
            time.sleep(0.5)
        #cars[0] = net.addCar('car0',  wlans=1, ip='10.0.1.101/24', range = 50, mac='00:00:00:00:00:01', radius_passwd='sdnteam', encrypt='wpa2', radius_identity='joe1', inNamespace=False, bgscan_threshold=-60, s_interval=5, l_interval=10, bgscan_module="simple")
        #bgscan_threshold = Umbral dBm para iniciar el escaneo
        #s_interval= short bgscan interval in seconds 
        #signal= Umbral de intensidad de la senal
        
    else:
        # Esta opcion no se puede usar con sumo, dado que la posicion no varia
        # Por ende, debe usar  net.plotGraph(min_x=-50, min_y=-210, max_x=1090, max_y=210)
        ### py cars[0].setPosition('100,0,0')
        
        car0 = net.addStation('car0',  wlans=1, ip='10.0.1.101/24', encrypt=['wpa2'], position='0,0,0', range = 50, mac='00:00:00:00:00:01', radius_passwd='sdnteam', radius_identity='joe1', inNamespace=False)#, bgscan_threshold=-60, s_interval=5, l_interval=10, bgscan_module="simple")
        cars.append(car0)

    time.sleep(1)

    kwargs = {'protocols':'OpenFlow13', 'ssid': 'handover', 'encrypt': 'wpa2', 'mode': 'g','passwd': '123456789a','authmode': '80211r', 'ieee80211r':'yes','mobility_domain': 'a1b2', 'radius_server': '192.168.0.210'}
    
    if flag3 == '-gnb1ConSlicing':
        gnb1 = net.addAccessPoint('gnb1', channel='1', vssids=['handover,handover,handover'], bssid_list={0:('gnb1','02:00:00:00:%s:00' % format(n_Cars,'02x'),'192.168.0.201',n_Cars,nSlices,flag2,flag3),1:('gnb2','02:00:00:00:%s:00' % format(n_Cars+1,'02x'),'0')}, dpid='1', position='1150,30,0', **kwargs)
    else:
        gnb1 = net.addAccessPoint('gnb1', channel='1', bssid_list={0:('gnb1','02:00:00:00:%s:00' % format(n_Cars,'02x'),'192.168.0.201',n_Cars,nSlices,flag2,flag3),1:('gnb2','02:00:00:00:%s:00' % format(n_Cars+1,'02x'),'0')}, dpid='1', position='1150,30,0', **kwargs)
    
    time.sleep(1)

    if flag2 == '-conSlicing':
        gnb2 = net.addAccessPoint('gnb2', channel='1', vssids=['handover,handover,handover'], bssid_list={0:('gnb2','02:00:00:00:%s:00' % format(n_Cars+1,'02x'),'192.168.0.202',n_Cars,nSlices,flag2,flag3),1:('gnb1','02:00:00:00:%s:00' % format(n_Cars,'02x'),'0')}, dpid='2', position='1390,30,0', **kwargs)#, config='beacon_int=100')# 'ap_max_inactivity=6,' 'skip_inactivity_poll=1,' 'max_listen_interval=6')#, protocols='OpenFlow13') # range = [30,30] # Para 2 interfaces 
        time.sleep(1)
    else:
        gnb2 = net.addAccessPoint('gnb2', channel='1', bssid_list={0:('gnb2','02:00:00:00:%s:00' % format(n_Cars+1,'02x'),'192.168.0.202',n_Cars,nSlices,flag2,flag3),1:('gnb1','02:00:00:00:%s:00' % format(n_Cars,'02x'),'0')}, dpid='2', position='1390,30,0', **kwargs)#, config='beacon_int=100')# 'ap_max_inactivity=6,' 'skip_inactivity_poll=1,' 'max_listen_interval=6')#, protocols='OpenFlow13') # range = [30,30] # Para 2 interfaces 
        time.sleep(1)

    
    sre21 = net.addSwitch('sre21', dpid='6') #datapath='kernel' , protocols='OpenFlow13'
    sbr20 = net.addSwitch('sbr20', dpid='7')
    sat10 = net.addSwitch('sat10', dpid='8')
    s13 = net.addSwitch('s13', dpid='9')
    s23 = net.addSwitch('s23', dpid='10')
    #[]
    
    srad1 = net.addHost('srad1', ip='192.168.0.210/24', mac='22:22:22:22:22:01')
    time.sleep(1)
    sv2n_1 =  net.addHost('sv2n_1',  ip='192.168.0.220/24', mac='33:33:33:33:33:01')
    sv2n_2 =  net.addHost('sv2n_2',  ip='192.168.0.221/24', mac='44:44:44:44:44:01')
    sv2n_3 =  net.addHost('sv2n_3',  ip='192.168.0.222/24', mac='55:55:55:55:55:01')
    time.sleep(1)

    c1 = net.addController('c1', controller=RemoteController, ip='127.0.0.1', port=6653)
    #c1 = net.addController('c0', controller=InbandController, ip='192.168.0.200',port=6653)
    time.sleep(1)
        
    debug("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3.1) #mudou
    #net.setPropagationModel(model="logDistance", exp=4) #mudou
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
    net.addLink(sbr20, sv2n_1, 2, 0)
    net.addLink(sbr20, sv2n_2, 3, 0)
    net.addLink(sbr20, sv2n_3, 4, 0)
    net.addLink(sat10, srad1,  6, 0)

    time.sleep(0.5)
    if flag3 == '-gnb1ConSlicing':
        net.addLink(gnb1, s13, 5 , 3) # , bw=700
    else:
        net.addLink(gnb1, s13, 2, 3)

    if flag2 == '-conSlicing':
        time.sleep(0.5)
        net.addLink(gnb2, s23, 5, 3)
        time.sleep(0.5)
    else:
        time.sleep(0.5)
        net.addLink(gnb2, s23, 2, 3)
        time.sleep(0.5)
    


    if flag == '-sumo':
        #/usr/share/sumo/bin/netedit
        net.useExternalProgram(program=sumo, port=8813,
                               config_file='/home/mininet/mininet-wifi/mn_wifi/sumo/data/scenario_2gnb_1car.sumocfg',
                               extra_params=["--breakpoints 00:00:01,00:00:17  --start --delay 1000 --window-size 650,600 --window-pos 1700,100"], clients=1, exec_order=0)
        #                       extra_params=["--breakpoints 00:00:01,00:00:22,00:00:36,00:00:50,00:00:74  --start --delay 1000 --window-size 650,600 --window-pos 1700,100"], clients=1, exec_order=0)
        #                       extra_params=["--breakpoints 00:00:01,00:00:22  --start --delay 1000 --window-size 650,600 --window-pos 1700,100"], clients=1, exec_order=0)
        #                       extra_params=["--delay 1000 --window-size 650,600 --window-pos 1700,100"], clients=1, exec_order=0)
         
        #nodes = net.cars + net.aps
        #net.telemetry(nodes=nodes, data_type='position', min_x=-50, min_y=-300, max_x=2050, max_y=330)
        #net.plotGraph(min_x=-50, min_y=-300, max_x=2050, max_y=330)
    else:
        net.plotGraph(min_x=-50, min_y=-300, max_x=2050, max_y=330)


    debug("*** Starting network")
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

    
    
    if flag3 == '-gnb1ConSlicing':
        cars[0].setIP('10.1.1.100/24', intf="car0-wlan0")
        cars[1].setIP('10.1.1.101/24', intf="car1-wlan0")
        
        gnb1.cmd('ifconfig gnb1-wlan1   10.1.0.1 netmask 255.255.255.0')
        gnb1.cmd('ifconfig gnb1-wlan1-0 10.1.1.1 netmask 255.255.255.0')
        gnb1.cmd('ifconfig gnb1-wlan1-1 10.1.2.1 netmask 255.255.255.0')
        gnb1.cmd('ifconfig gnb1-wlan1-2 10.1.3.1 netmask 255.255.255.0')
        gnb1.cmd('ifconfig gnb1-eth5    10.1.4.1 netmask 255.255.255.0')
        gnb1.cmd('ifconfig gnb1-eth5:0 192.168.0.201 netmask 255.255.255.0')
        
    else:
        for x in range(0, n_Cars):
            cars[x].setIP('10.1.0.%s/24' % (int(x)+100), intf="car%s-wlan0" % x)
            
        gnb1.cmd('ifconfig gnb1-wlan1 10.1.0.1 netmask 255.255.255.0')
        gnb1.cmd('ifconfig gnb1-eth2 192.168.0.201 netmask 255.255.255.0')


    time.sleep(1)

    if flag2 == '-conSlicing':
        gnb2.cmd('ifconfig gnb2-wlan1   10.2.0.1 netmask 255.255.255.0')
        gnb2.cmd('ifconfig gnb2-wlan1-0 10.2.1.1 netmask 255.255.255.0')
        gnb2.cmd('ifconfig gnb2-wlan1-1 10.2.2.1 netmask 255.255.255.0')
        gnb2.cmd('ifconfig gnb2-wlan1-2 10.2.3.1 netmask 255.255.255.0')
        gnb2.cmd('ifconfig gnb2-eth5    10.2.4.1 netmask 255.255.255.0')
        gnb2.cmd('ifconfig gnb2-eth5:0 192.168.0.202 netmask 255.255.255.0')
    else:
        gnb2.cmd('ifconfig gnb2-wlan1 10.2.0.1 netmask 255.255.255.0')
        gnb2.cmd('ifconfig gnb2-eth2  10.2.1.1 netmask 255.255.255.0')
        gnb2.cmd('ifconfig gnb2-eth2:0 192.168.0.202 netmask 255.255.255.0')


    time.sleep(1)

    gnb1.cmd('sysctl net.ipv4.ip_forward=1')
    time.sleep(0.5)
    gnb2.cmd('sysctl net.ipv4.ip_forward=1')
    time.sleep(0.5)

    time.sleep(1)
    if flag == '-sumo':
        ######################## Test ############################
        ######################## Test ############################
        for x in range(0, n_Cars_test):    
            cars[x].cmd('iw dev car%s-wlan0 interface add car%s-mon0 type monitor'% (x,x))
            time.sleep(1)
            cars[x].cmd('ip link set car%s-mon0 up'% x)
            time.sleep(1)
    else:
        cars[0].cmd('iw dev car0-wlan0 interface add car0-mon0 type monitor')
        cars[0].cmd('ip link set car0-mon0 up')

    debug("*** Linea INICIO Radius")
    time.sleep(1)
    os.system('xterm -hold -title "srad1" -e "/home/mininet/mininet-wifi/util/m srad1 freeradius -X" &')
    time.sleep(1)
    debug("*** Linea FIN Radius")

    time.sleep(1)

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
    #sbr20.cmd('ovs-ofctl add-flow sbr20 in_port=1,actions=output:2') 
    time.sleep(1)
    

    if flag3 == '-gnb1ConSlicing':
        gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=1 drop:rate=%s' % reqQoS_V2N[1][2])
        time.sleep(0.5)
        gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=2 drop:rate=%s' % reqQoS_V2N[2][2])
        time.sleep(0.5)
        gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=3 drop:rate=%s' % reqQoS_V2N[3][2])
        time.sleep(0.5)
        gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=4 drop:rate=%s' % reqQoS_V2N[1][2])
        time.sleep(0.5)
        gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=5 drop:rate=%s' % reqQoS_V2N[2][2])
        time.sleep(0.5)
        gnb1.cmd('dpctl unix:/tmp/gnb1 meter-mod cmd=add,flags=1,meter=6 drop:rate=%s' % reqQoS_V2N[3][2])
        time.sleep(0.5)
        
        # Puerto Id_Meter Megas
        #gnb1.cmd('dpctl unix:/tmp/gnb1 queue-mod 2 1 54')
        #time.sleep(0.5)
        #gnb1.cmd('dpctl unix:/tmp/gnb1 queue-mod 3 2 54')
        #time.sleep(0.5)
        #gnb1.cmd('dpctl unix:/tmp/gnb1 queue-mod 4 3 54')
        #time.sleep(0.5)
        
        #gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=1 in_port=2,eth_type=0x800,ip_dst=192.168.0.200 apply:output=local')
        #gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,in_port=2,eth_type=0x800,ip_dst=192.168.0.200 apply:output=local')
        #gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=1 in_port=4 apply:output=5')
        #Slice 3
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=1 in_port=4 meter:6 apply:output=5')
        time.sleep(0.5)
        #Slice 2
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=2 in_port=3 meter:5 apply:output=5')
        time.sleep(0.5)
        #Slice 1
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=3 in_port=2 meter:4 apply:output=5')
        time.sleep(0.5)

        #gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod table=0,cmd=add in_port=1 goto:1')
        #gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod table=1,cmd=add eth_type=0x800,ip_dst=10.1.2.0/24 apply:output=2')
        #time.sleep(0.5)
        #Slice 3
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=4 in_port=5,eth_type=0x800,ip_dst=10.1.3.0/24 meter:3 apply:output=4')
        time.sleep(0.5)
        #Slice 2
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=5 in_port=5,eth_type=0x800,ip_dst=10.1.2.0/24 meter:2 apply:output=3')
        time.sleep(0.5)
        #Slice 1
        #sh dpctl unix:/tmp/gnb1 flow-mod table=0,cmd=add in_port=5, eth_type=0x800,ip_dst=10.1.2.0/24 meter:4 apply:output=2
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0,prio=6 in_port=5,eth_type=0x800,ip_dst=10.1.1.0/24 meter:1 apply:output=2')
        time.sleep(0.5)        
    else:
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0 in_port=1 apply:output=2')
        time.sleep(0.5)
        gnb1.cmd('dpctl unix:/tmp/gnb1 flow-mod cmd=add,table=0 in_port=2 apply:output=1')
        time.sleep(0.5)
    
    if flag2 == '-conSlicing':

        gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=1 drop:rate=%s' % reqQoS_V2N[1][2])
        time.sleep(0.5)
        gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=2 drop:rate=%s' % reqQoS_V2N[2][2])
        time.sleep(0.5)
        gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=3 drop:rate=%s' % reqQoS_V2N[3][2])
        time.sleep(0.5)
        gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=4 drop:rate=%s' % reqQoS_V2N[1][2])
        time.sleep(0.5)
        gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=5 drop:rate=%s' % reqQoS_V2N[2][2])
        time.sleep(0.5)
        gnb2.cmd('dpctl unix:/tmp/gnb2 meter-mod cmd=add,flags=1,meter=6 drop:rate=%s' % reqQoS_V2N[3][2])
        time.sleep(0.5)
        
        # Puerto Id_Meter Megas
        #gnb2.cmd('dpctl unix:/tmp/gnb2 queue-mod 2 1 54')
        #time.sleep(0.5)
        #gnb2.cmd('dpctl unix:/tmp/gnb2 queue-mod 3 2 54')
        #time.sleep(0.5)
        #gnb2.cmd('dpctl unix:/tmp/gnb2 queue-mod 4 3 54')
        #time.sleep(0.5)
        
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=1 in_port=2,eth_type=0x800,ip_dst=192.168.0.200 apply:output=local')
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,in_port=2,eth_type=0x800,ip_dst=192.168.0.200 apply:output=local')
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=1 in_port=4 apply:output=5')
        #Slice 3
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=1 in_port=4 meter:6 apply:output=5')
        time.sleep(0.5)
        #Slice 2
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=2 in_port=3 meter:5 apply:output=5')
        time.sleep(0.5)
        #Slice 1
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=3 in_port=2 meter:4 apply:output=5')
        time.sleep(0.5)

        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod table=0,cmd=add in_port=1 goto:1')
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod table=1,cmd=add eth_type=0x800,ip_dst=10.1.2.0/24 apply:output=2')
        #time.sleep(0.5)
        #Slice 3
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=4 in_port=5,eth_type=0x800,ip_dst=10.2.3.0/24 meter:3 apply:output=4')
        time.sleep(0.5)
        #Slice 2
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=5 in_port=5,eth_type=0x800,ip_dst=10.2.2.0/24 meter:2 apply:output=3')
        time.sleep(0.5)
        #Slice 1
        #sh dpctl unix:/tmp/gnb2 flow-mod table=0,cmd=add in_port=5, eth_type=0x800,ip_dst=10.1.2.0/24 meter:4 apply:output=2
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=6 in_port=5,eth_type=0x800,ip_dst=10.2.1.0/24 meter:1 apply:output=2')
        


        ############################ GNB2
        ##Slice 3
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=1 in_port=4 apply:output=5')
        #time.sleep(0.5)
        ##Slice 2
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=2 in_port=3 apply:output=5')
        #time.sleep(0.5)
        ##Slice 1
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=3 in_port=2 apply:output=5')
        #time.sleep(0.5)

        ##Slice 3
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=4 in_port=5,eth_type=0x800,ip_dst=10.2.3.0/24 apply:output=4')
        #time.sleep(0.5)
        ##Slice 2
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=5 in_port=5,eth_type=0x800,ip_dst=10.2.2.0/24 apply:output=3')
        #time.sleep(0.5)    
        ##Slice 1
        #gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0,prio=6 in_port=5,eth_type=0x800,ip_dst=10.2.1.0/24 apply:output=2')
        #time.sleep(0.5)

    else:
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0 in_port=1 apply:output=2')
        time.sleep(0.5)
        gnb2.cmd('dpctl unix:/tmp/gnb2 flow-mod cmd=add,table=0 in_port=2 apply:output=1')
        time.sleep(0.5)

    
    debug( "*** Creating initial basic flows in network" )
    if flag3 == '-gnb1ConSlicing':        
        #gnb1
        srad1.cmd('ip route add 10.1.0.0/16 via 192.168.0.201')
        sv2n_1.cmd('ip  route add 10.1.1.0/24 via 192.168.0.201')
        sv2n_2.cmd('ip  route add 10.1.2.0/24 via 192.168.0.201')
        sv2n_3.cmd('ip  route add 10.1.3.0/24 via 192.168.0.201')
    else:
        #gnb1
        srad1.cmd('ip route add 10.1.0.0/16 via 192.168.0.201')
        sv2n_1.cmd('ip  route add 10.1.0.0/24 via 192.168.0.201')
        sv2n_2.cmd('ip  route add 10.1.0.0/24 via 192.168.0.201')
        sv2n_3.cmd('ip  route add 10.1.0.0/24 via 192.168.0.201')
    
    if flag2 == '-conSlicing':
        #gnb2
        srad1.cmd('ip route add 10.2.0.0/16 via 192.168.0.202')
        sv2n_1.cmd('ip  route add 10.2.1.0/24 via 192.168.0.202')
        sv2n_2.cmd('ip  route add 10.2.2.0/24 via 192.168.0.202')
        sv2n_3.cmd('ip  route add 10.2.3.0/24 via 192.168.0.202')
    else:
        #gnb2
        srad1.cmd('ip route add 10.2.0.0/16 via 192.168.0.202')
        sv2n_1.cmd('ip  route add 10.2.0.0/24 via 192.168.0.202')
        sv2n_2.cmd('ip  route add 10.2.0.0/24 via 192.168.0.202')
        sv2n_3.cmd('ip  route add 10.2.0.0/24 via 192.168.0.202')
    

    
    if flag3 == '-gnb1ConSlicing':
        #os.system('xterm -hold -title "gnb1" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb1 hostapd_cli -i gnb1-wlan1" &')
        #time.sleep(0.5)
        #os.system('xterm -hold -title "gnb1-0" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb1 hostapd_cli -i gnb1-wlan1-0" &')
        #time.sleep(0.5)
        #os.system('xterm -hold -title "gnb1-1" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb1 hostapd_cli -i gnb1-wlan1-1" &')
        #time.sleep(0.5)
        #os.system('xterm -hold -title "gnb1-2" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb1 hostapd_cli -i gnb1-wlan1-2" &')
        time.sleep(0.5)
    else:
        #os.system('xterm -hold -title "gnb1" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb1 hostapd_cli -i gnb1-wlan1" &')
        time.sleep(0.5)

    
    if flag2 == '-conSlicing':
        #os.system('xterm -hold -title "gnb2" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb2 hostapd_cli -i gnb2-wlan1" &')
        #time.sleep(0.5)
        #os.system('xterm -hold -title "gnb2-0" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb2 hostapd_cli -i gnb2-wlan1-0" &')
        #time.sleep(0.5)
        #os.system('xterm -hold -title "gnb2-1" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb2 hostapd_cli -i gnb2-wlan1-1" &')
        time.sleep(0.5)
        #os.system('xterm -hold -title "gnb2-2" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb2 hostapd_cli -i gnb2-wlan1-2" &')
        #time.sleep(0.5) 
    else:
        os.system('xterm -hold -title "gnb2" -e "alias python=python2  && /home/mininet/mininet-wifi/util/m gnb2 hostapd_cli -i gnb2-wlan1" &')
        time.sleep(0.5)

    ####################################################################################
    #### LINEAS A ITERAR EN RYU CONTROLLER
    ####################################################################################
    #cars[0].cmd('ip route add 192.168.0.0/24 dev car0-wlan0')
    #cars[1].cmd('ip route add 192.168.0.0/24 dev car1-wlan0')
    #cars[2].cmd('ip route add 192.168.0.0/24 dev car2-wlan0')
   
    #cars[0].cmd('ip route add 10.1.0.0/16 dev car0-wlan0')
    #cars[1].cmd('ip route add 10.1.0.0/16 dev car1-wlan0')
    #cars[2].cmd('ip route add 10.1.0.0/16 dev car2-wlan0')

    for x in range(0, n_Cars):   
        cars[x].cmd('ip route add 192.168.0.0/24 dev car%s-wlan0' % x)
        cars[x].cmd('ip route add 10.1.0.0/16 dev car%s-wlan0' % x)
    
    ######################## Test ############################
    ######################## Test ############################
    #for x in range(0, n_Cars_test):   
    #    os.system('xterm -hold -title "car%s" -e "alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu && source bin/activate && /home/mininet/mininet-wifi/util/m car%s python /home/mininet/v2x-slicing/single/ryu/car1_thread.py %s %s %s %s %s %s %s %s" &' % (x,x,x,n_Cars,reqQoS_Cars[x][0],reqQoS_V2N[1][0],reqQoS_V2N[2][0],reqQoS_V2N[3][0],flag2,flag3))
    #    time.sleep(1)
    
    #os.system('xterm -hold -title "car0" -e "alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu && source bin/activate && /home/mininet/mininet-wifi/util/m car0 python /home/mininet/v2x-slicing/single/ryu/car1.py 0 3 50 20 10 -conSlicing -gnb1ConSlicing  > log_wpa/car0.log" &')
    
    """
sync && echo 3 > /proc/sys/vm/drop_caches
alias python=python2  && cd /home/mininet/v2x-slicing/single/ryu && source bin/activate

/home/mininet/mininet-wifi/util/m car0 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 0 32 20 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car1 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 1 32 20 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car2 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 2 32 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car3 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 3 32 10 50 20 10 -conSlicing -gnb1SinSlicing

/home/mininet/mininet-wifi/util/m car0 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 0 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car1 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 1 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car2 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 2 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car3 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 3 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car4 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 4 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car5 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 5 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car6 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 6 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car7 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 7 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car8 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 8 10 50 20 10 -conSlicing -gnb1SinSlicing
/home/mininet/mininet-wifi/util/m car9 python /home/mininet/v2x-slicing/single/ryu/car1_thread.py 9 10 50 20 10 -conSlicing -gnb1SinSlicing
    """

    time.sleep(1)
    
    debug("*** Running CLI\n")
    CLI(net) #mudou

    debug("*** Stopping network\n")
    #cars[0].cmd('airmong stop car0-wlan1')
    os.system('sudo systemctl stop freeradius.service')
    os.system('sudo systemctl stop apache2.service')
    # Ademas deshabilitar el modo promiscuo de la MV en VirtuaBox

    os.system('sudo fuser -k 1812/udp')
    os.system('sudo fuser -k 6653/tcp')
    os.system('pkill freeradius')
    if py_version_info < (3, 0):
        os.system('pkill -f SimpleHTTPServer')
    else:
        os.system('pkill -f http.server')
    os.system('pkill xterm')
    os.system('pkill -f \"xterm -title\"')

    #Para ver el consumo de memoria de los procesos
    #os.system('ps aux  --sort pmem')
    #Conocer el nombre del proceso, teniendo su pid
    #os.system('ps -p {valor-pid} -o comm=')
    # Matar los procesos llamados python (es decir, matar los hilos)
    #os.system('killall python')

    net.stop()
    

if __name__ == '__main__':
    flag = sys.argv[1]
    flag2 = sys.argv[2]
    flag3 = sys.argv[3]
    setLogLevel('debug')
    ##setLogLevel('info')
    dbRadius = MySQLDB()
    dbRadius.cleanUsersLogin()
    os.system('sudo fuser -k 1812/udp')
    os.system('sudo systemctl stop freeradius.service')
    #os.system('sudo /etc/init.d/network-manager stop')
    #os.system('sudo systemctl stop network-manager.service')
    os.system('fuser -k 6653/tcp')    
    os.system('rm -f radius.txt;')
    
    #os.system('xterm -hold -title "Ryu" -e "cd /home/mininet/ryu && sudo PYTHONPATH=. ./bin/ryu-manager ryu/app/simple_switch_13.py" &')
    #os.system('xterm -hold -title "Ryu" -e "cd /home/mininet/ryu && sudo PYTHONPATH=. ./bin/ryu-manager ryu/app/vanet_run.py ryu/app/simple_switch_13.py" &')
    time.sleep(1)
    topology(flag,flag2,flag3)