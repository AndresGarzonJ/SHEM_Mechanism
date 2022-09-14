'!/usr/bin/env python2.7'

import logging
import os, sys
import collections
from threading import Thread, Event 

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
MODULE_PATH_2 = "/home/mininet/v2x-slicing/single/ryu/lib/python2.7/site-packages/scapy"
sys.path.append(os.path.dirname(os.path.expanduser(MODULE_PATH_2)))
from scapy.all import *
#from scapy import *
import time

j_k_list = {}
j_k_rssi_load_t = {}
load_j_k_t_1 = 999
rssi_j_k_id_car_t_1 = -90
load_j_k_t = 999
rssi_j_k_id_car_t = -90
flag_first_send = 0
flag_time_start = 0
flag_time_scan = 0
time_Start = 0
time_ref_scan = 0
time_Scan = 0


######################## Parameters for testing - Start
time_send = 1.5
time_scan_flag = 5
######################## Parameters for testing - End

id_t_s_asociacion = 0
id_t_r_asociacion = 0
id_t_s_re_asociacion = 0
id_t_r_re_asociacion = 0
id_t_s_sondeo = 0
id_t_r_sondeo = 0
id_t_des_asociacion = 0
id_t_autenticacion = 0
id_t_des_autenticacion = 0
id_t_action = 0
id_t_action_no_ack = 0

nSlice = 0
 
class Sniffer(Thread):
    def __init__(self):
        super().__init__()
        self.id_car = str(sys.argv[1])
        self.n_Cars = int(sys.argv[2])
        self.lat_req_car = int(sys.argv[3])
        self.latency_servers = {}
        self.latency_servers[0] = (int(sys.argv[4])) # Para wlan1
        self.latency_servers[1] = (int(sys.argv[4])) # Para wlan1-0
        self.latency_servers[2] = (int(sys.argv[5])) # Para wlan1-1
        self.latency_servers[3] = (int(sys.argv[6])) # Para wlan1-2
        
        self.mac_gnb = {}
        self.mac_gnb[0] = "02:00:00:00:%s:00" % format(self.n_Cars,'02x')   # gnb1-wlan1
        self.mac_gnb[1] = "02:00:00:00:%s:00" % format(self.n_Cars+1,'02x') # gnb2-wlan1
        
        self.mac_Car = "0002:00:00:00:%s:00" % format(int(self.id_car),'02x')

        
        print("****** MAC-Cliente: %s" % (self.mac_Car))
        self.mn_wifi_dir = '/home/mininet/mininet-wifi/util/m'

        self.daemon = True
        self.socket = None
        self.interface = "car%s-mon0" % self.id_car
        self.stop_sniffer = Event()

    def run(self):
        self.socket = conf.L2listen(
            type=ETH_P_ALL,
            iface=self.interface,
            filter="type Management")

        sniff(
            opened_socket=self.socket,
            prn=self.execute_packet,
            stop_filter=self.should_stop_sniffer)

    def join(self,timeout=None):
        self.stop_filter.set()
        super().join(timeout)

    def should_stop_sniffer(self,packet):
        return self.stop_sniffer.isSet()

    def execute_packet(self,pkt):
        global flag_time_start
        global flag_time_scan
        global flag_first_send
        global time_Start
        global time_Scan
        global time_ref_scan

        global j_k_list
        global j_k_rssi_load_t
        global load_j_k_t_1
        global rssi_j_k_id_car_t_1
        global load_j_k_t
        global rssi_j_k_id_car_t

        global source_mac_j_k_t_1

        global id_t_s_asociacion
        global id_t_r_asociacion
        global id_t_s_re_asociacion
        global id_t_r_re_asociacion
        global id_t_s_sondeo
        global id_t_r_sondeo
        global id_t_des_asociacion
        global id_t_autenticacion
        global id_t_des_autenticacion
        global id_t_action
        global id_t_action_no_ack
        
        global nSlice




        if pkt.haslayer(Dot11):
            target_mac_j_k = None
            slice_id = 0
            
            if pkt.subtype == 8 and pkt.addr3 not in self.mac_gnb.values():
                if flag_time_start== 0:
                    time_Start = time.time()
                    flag_time_start == 1
            
                if flag_time_scan== 0:
                    # Tiempo ref para escanear
                    time_ref_scan = time.time()
                    flag_time_scan == 1


                if (time.time() - time_ref_scan) > time_scan_flag :
                    n_scan_results = \
                        int(subprocess.check_output('%s car%s wpa_cli -i car%s-wlan0 '
                                                    'scan_results | wc -l'
                                                    % (self.mn_wifi_dir, self.id_car, self.id_car),
                                                    shell=True))
                    if n_scan_results < 6:
                        print("* Scan")
                        os.system('%s car%s wpa_cli -i car%s-wlan0 scan > /dev/null 2>&1' % (self.mn_wifi_dir,self.id_car,self.id_car))
                        flag_time_scan= 0
                else:
                    flag_time_scan= 1
                
                                
                target_mac_j_k = pkt.addr3
                #print("###########")
                #print(pkt.addr3)
                j=0
                k=0
                j = int(target_mac_j_k[-5:-3],16) - self.n_Cars + 1
                k = int(target_mac_j_k[15:],16)

                #####################
                #if k != 0:
                #slice_id = (j*10)+k
                slice_id= int(str(j) + str(k))
                if slice_id not in j_k_list.keys(): ## Agrega la informacion del NUEVO slice
                    latency_server = self.latency_servers[k]            
                    ############## Load
                    try:
                        if k != 0:
                            load_j_k_t_1 = \
                                int(subprocess.check_output('%s gnb%s '
                                                            'hostapd_cli -i gnb%s-wlan1-%s '
                                                            'list_sta | wc -l'
                                                            % (self.mn_wifi_dir, j, j, k-1),
                                                            shell=True))
                        else:
                            load_j_k_t_1 = \
                                int(subprocess.check_output('%s gnb%s '
                                                            'hostapd_cli -i gnb%s-wlan1 '
                                                            'list_sta | wc -l'
                                                            % (self.mn_wifi_dir, j, j),
                                                            shell=True))

                    except:
                        load_j_k_t_1=999
                    
                    ############## Rssi
                    try:
                       rssi_j_k_id_car_t_1 = pkt.dBm_AntSignal
                    except:
                        rssi_j_k_id_car_t_1 = -100

                    ############## Add slice
                    #j_k_list[slice_id] = ("%s" % (target_mac_j_k),"%s" % (str(latency_server)),"%s" % (str(load_j_k_t_1)),"%s" % (str(rssi_j_k_id_car_t_1)))
                    j_k_list[slice_id] = ["%s" % (target_mac_j_k),"%s" % (str(latency_server)),"%s" % (str(load_j_k_t_1)),"%s" % (str(rssi_j_k_id_car_t_1))]
                else:
                    ## ACTUALIZA la informacion del slice
                    try:
                       rssi_j_k_id_car_t = pkt.dBm_AntSignal
                    except:
                        rssi_j_k_id_car_t = -100

                    try:
                        if k != 0:
                            load_j_k_t = \
                                int(subprocess.check_output('%s gnb%s '
                                                            'hostapd_cli -i gnb%s-wlan1-%s '
                                                            'list_sta | wc -l'
                                                            % (self.mn_wifi_dir, j, j, k-1),
                                                            shell=True))
                        else:
                            load_j_k_t = \
                                int(subprocess.check_output('%s gnb%s '
                                                            'hostapd_cli -i gnb%s-wlan1 '
                                                            'list_sta | wc -l'
                                                            % (self.mn_wifi_dir, j, j),
                                                            shell=True))

                    except:
                        load_j_k_t=999
                    #j_k_rssi_load_t[slice_id] = ("%s" % (str(rssi_j_k_id_car_t)) ,"%s" % (str(load_j_k_t)))
                    j_k_rssi_load_t[slice_id] = ["%s" % (str(rssi_j_k_id_car_t)) ,"%s" % (str(load_j_k_t))]

                
                if (time.time() - time_Start) > time_send:
                    cmd = ["%s car%s iw dev "
                           "car%s-wlan0 link | grep Connected | "
                           "awk 'NR==1{print $3}'" % (self.mn_wifi_dir, self.id_car, self.id_car)]
                    address = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
                    (out, err) = address.communicate()
                    source_mac_j_k = str(out).split('\n')[0][2:-3]
                    print("* source_mac_j_k: %s" % source_mac_j_k)
                                        
                    nSlice = len(j_k_rssi_load_t)
                    
                    if source_mac_j_k != "":
                        # Actualiza el rssi_t del slice conectado
                        try:
                            cmd1 = ["%s car%s iw dev "
                                   "car%s-wlan0 link | grep signal | "
                                   "awk 'NR==1{print $2}'" % (self.mn_wifi_dir, self.id_car, self.id_car)]
                            address1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
                            (out1, err1) = address1.communicate()
                            temp_source_signal_j_k = int(str(out1).split('\n')[0][2:-3])

                            j_source = int(source_mac_j_k[-5:-3],16) - self.n_Cars + 1
                            k_source = int(source_mac_j_k[15:],16)
                            slice_id_connected = int(str(j_source) + str(k_source))
                            source_mac_j_k_t_1 = source_mac_j_k
                        except:
                            return

                        try:
                            j_k_rssi_load_t[slice_id_connected][0] = temp_source_signal_j_k
                        except:
                            return

                        print("* rssi: %s" % temp_source_signal_j_k)

                        time_Scan = time.time() - time_Start


                        msg = "%s,%s,%s,%s,%s" % (str(self.mac_Car),self.lat_req_car, nSlice, time_Scan, source_mac_j_k)


                        # Ordenar j_k_rssi_load_t por clave
                        j_k_rssi_load_t_ordenado = collections.OrderedDict(sorted(j_k_rssi_load_t.items()))

                        for idSlice in j_k_rssi_load_t_ordenado:
                            msg += ",%s" % (str(idSlice))                    # slice_id
                            msg += ",%s" % (j_k_list[idSlice][0])            #      target_mac_j_k
                            msg += ",%s" % (j_k_list[idSlice][1])            #      latency_server
                            msg += ",%s" % (j_k_list[idSlice][2])            #      load_j_k_t_1
                            msg += ",%s" % (j_k_rssi_load_t[idSlice][1])     #      load_j_k_t
                            msg += ",%s" % (j_k_list[idSlice][3])            #      rssi_j_k_id_car_t_1
                            msg += ",%s" % (j_k_rssi_load_t[idSlice][0])     #      rssi_j_k_id_car_t
                        msg += ",\n"

                        # Peso = A*Intensidad + B*Latencia_Umbral_Servidor + C*Carga
                        #with open('/home/mininet/v2x-slicing/single/ryu/data-log/dataset.txt','a') as file:
                        #    file.write(msg)
                        #mac_Car, nSlice, time_Scan,source_mac_j_k,slice_id,target_mac_j_k,latency_server,load_j_k_t_1,load_j_k_t,rssi_j_k_id_car_t_1,rssi_j_k_id_car_t,\n

                        #file.write('car%s,%s,%s,%s,%s,%s,%s,\n' % (
                        #    self.id_car,str(idSlice),j_k_list[idSlice][1],j_k_list[idSlice][3],j_k_rssi_load_t[idSlice][0],j_k_list[idSlice][2],j_k_rssi_load_t[idSlice][1]))
                        #id_car, slice_id, threshold_latency_server,rssi_j_k_id_car_t_1,rssi_j_k_id_car_t,load_j_k_t_1,load_j_k_t

                        # mac_Car
                        # nSlice
                        # time_Scan
                        # source_mac_j_k

                        # target_mac_j_k
                        # latency_server
                        # load_j_k_t_1
                        # load_j_k_t
                        # rssi_j_k_id_car_t_1
                        # rssi_j_k_id_car_t


                        #nSlice = 0
                        #j_k_list = {}
                        #j_k_rssi_load_t = {}
                        j_k_list.clear()
                        j_k_rssi_load_t.clear()

                        packet = IP(src="10.%s.%s.%s" % (j_source,k_source,int(self.id_car)+100),
                                    dst="192.168.0.200")/UDP(sport=8000, dport=8002)/msg
                        #packet = IP(src="10.%s.%s.%s" % (j_source,k_source,int(self.id_car)+100),
                        #            dst="192.168.0.200")/TCP(sport=8000, dport=8002)/msg
                        #send(packet, verbose=0, iface="car%s-wlan0" % id_car, loop=0, count=1, realtime=True)
                        send(packet, verbose=0, iface="car%s-wlan0" % self.id_car, count=1)
                        #send(packet, iface="car%s-wlan0" % self.id_car, count=1)
                        print ("%s" % msg)
                        
                        flag_time_start = 0
                    else:
                        print("* Error - source_mac_j_k - vacio ")
                        try:
                            # El vehiculo ha perdido la conexion
                            j_source_t_1 = int(source_mac_j_k_t_1[-5:-3],16) - self.n_Cars + 1
                            k_source_t_1 = int(source_mac_j_k_t_1[15:],16)
                            os.system('%s gnb%s hostapd_cli -i gnb%s-wlan1-%s disassociate %s > /dev/null 2>&1' % (self.mn_wifi_dir, j_source_t_1, j_source_t_1,str(k_source_t_1-1),self.mac_Car))
                            source_mac_j_k_t_1 = None
                        except:
                            if flag_first_send == 0:
                                return
                            pass

                        # Des-Asociar el vehiculo del gNB anterior

                        #if (time.time() - time_Start) > time_send: 
                        j_k_rssi_load_t_ordenado = collections.OrderedDict(sorted(j_k_rssi_load_t.items()))
                        # Hacer con while
                        for idSlice in j_k_rssi_load_t_ordenado:
                            if int(j_k_rssi_load_t[idSlice][0]) <= -85:
                                print("Traspaso a %s - %s " % (idSlice,j_k_list[idSlice][0]))

                                os.system('%s car%s wpa_cli -i car%s-wlan0 set_network 0 bssid %s > /dev/null 2>&1' % (self.mn_wifi_dir,self.id_car,self.id_car,j_k_list[idSlice][0]))
                                cmd_t = ["%s car%s wpa_cli -i car%s-wlan0 roam %s" % (self.mn_wifi_dir,self.id_car,self.id_car,j_k_list[idSlice][0])]
                                res_roam = subprocess.Popen(cmd_t, stdout=subprocess.PIPE, shell=True)
                                (out_t, err_t) = res_roam.communicate()
                                #print("* out_t %s" % out_t)
                                #print("* err_t %s" % err_t)

                                out_t_t= str(out_t)
                                if out_t_t.find("OK") > - 1:
                                    j_tarjet = int(j_k_list[idSlice][0][-5:-3],16) - self.n_Cars + 1
                                    k_tarjet = int(j_k_list[idSlice][0][15:],16)
                                    os.system('%s car%s ifconfig car%s-wlan0 10.%s.%s.%s netmask 255.255.255.0 > /dev/null 2>&1' % (self.mn_wifi_dir,self.id_car,self.id_car,j_tarjet,k_tarjet,int(self.id_car)+100))
                                    os.system('%s car%s ip route add 10.%s.0.0/16 dev car%s-wlan0 > /dev/null 2>&1' % (self.mn_wifi_dir,self.id_car,j_tarjet,self.id_car))
                                    os.system('%s car%s ip route add 192.168.0.0/24 dev car%s-wlan0 > /dev/null 2>&1' % (self.mn_wifi_dir,self.id_car,self.id_car))                                    
                                    """
                                    car0 ifconfig car0-wlan0 10.1.1.100 netmask 255.255.255.0 > /dev/null 2>&1
                                    car0 ip route add 10.1.0.0/16 dev car0-wlan0 > /dev/null 2>&1
                                    car0 ip route add 192.168.0.0/24 dev car0-wlan0 > /dev/null 2>&1
                                    """
                                    source_mac_j_k_t_1 = j_k_list[idSlice][0]
                                    #time.sleep(0.6)
                                    # Se borra el contenido del archivo del traspaso realizado
                                    print("* Traspaso exitoso - log_wpa borrado")
                                    with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (self.id_car),'w') as file2: pass
                                    
                                    j_k_list.clear()
                                    j_k_rssi_load_t.clear()
                                    j_k_rssi_load_t_ordenado.clear()
                                    flag_time_start= 0
                                    # Terminar el ciclo for
                                    break
                                else:
                                    print("* Error Traspaso - log_wpa borrado")
                                    source_mac_j_k_t_1 = None
                                    # Se borra el contenido del archivo del traspaso realizado
                                    with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (self.id_car),'w') as file2: pass
                                    #os.system('%s car%s wpa_cli -i car%s-wlan0 roam %s > /dev/null 2>&1' % (self.mn_wifi_dir,self.id_car,self.id_car,j_k_list[idSlice][0]))
                        flag_time_start= 0
                else:                
                    flag_time_start= 1

                    #####################
                    # Espacio de estados
                    # Latencia del servidor (Ls1, Ls2, Ls3)
                    # Carga - N Carros por slice (j,k) = (gNB,slice)
                        # En el tiempo t
                        # En el tiempo t-1
                    # Intensidad de senal por slice (j,k) = (gNB,slice)
                        # En el tiempo t
                        # En el tiempo t-1

                    ###### Matriz
                    #        rssi carga latencia
                    #AP1
                    #AP2
                    #.
                    #.
                    #.
                    
                    # Informacion a enviar en un paquete IP
                    # String mac_carro - 12 bytes
                    # String MAC_Slice_Conectado - 12 bytes
                    # Entero numerosSliceTotalEncontrados = 1 bytes 
                    # Entero tiempo_procesamiento = 2 bytes



                    #mac_AP_j_k - 12 bytes
                    #rssi_t    - 3 bytes
                    #rssi_t_1  - 3 bytes
                    #carga_t   - 3 bytes
                    #carga_t_1 - 3 bytes
                    ### Total por slice - 24 bytes

                    # Tenemos 1436 (1460 - 24) bytes disponibles
                    # Nos alcanza para 59 slices

sniffer = Sniffer()
sniffer.start()

try:
    while True:
        time.sleep(100)
except KeyboardInterrupt:
    print("** Stop sniffing")
    sniffer.join(2.0)

    if sniffer.isAlive():
        sniffer.socket.close()
