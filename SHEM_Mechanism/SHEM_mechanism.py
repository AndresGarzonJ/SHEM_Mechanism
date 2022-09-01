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
#import numpy as np
import time
from threading import Thread


from shutil import copyfile
#from ryu.lib.packet import radius

#import mecanismoML_5_1

import logging
import sys



logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
MODULE_PATH_2 = "/home/mininet/v2x-slicing/single/ryu/lib/python2.7/site-packages/scapy"
sys.path.append(os.path.dirname(os.path.expanduser(MODULE_PATH_2)))
#from scapy import all as scapy
from scapy.all import *

class getAttr(object):
    ######################## Test ############################
    n_Cars = 12
    threshold_load = 2
    threshold_rssi_handover = -70
    ######################## Test ############################ 

    time_scanning_temp = {0:None, 1:None,2:None,3:None,4:None,5:None,6:None,7:None,8:None,9:None}
    currentAP = {0:'DISCONNECTED',1:'DISCONNECTED',2:'DISCONNECTED',3:'DISCONNECTED',4:'DISCONNECTED',5:'DISCONNECTED',6:'DISCONNECTED',7:'DISCONNECTED',8:'DISCONNECTED',9:'DISCONNECTED'}
    HM_state = {0:'0',1:'0',2:'0',3:'0',4:'0',5:'0',6:'0',7:'0',8:'0',9:'0'}
    time_completion_phase = {0:None,1:None,2:None,3:None,4:None,5:None,6:None,7:None,8:None,9:None}
    #client1 = '00-00-00-00-00-01'
    
class wifiAPP(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(wifiAPP, self).__init__(*args, **kwargs)
        # Inicialice/Construir el objeto MecanismoML


    def routing_configuration(self,mn_wifi_dir,j_target,k_target,id_car):
        time_start_completion_phase = time.time()
        os.system('%s car%s ifconfig car%s-wlan0 10.%s.%s.%s netmask 255.255.255.0 > /dev/null 2>&1' % (mn_wifi_dir,id_car,id_car,j_target,k_target,int(id_car)+100))
        #print("car%s-wlan0 10.%s.%s.%s" % (id_car,j_target,k_target,int(id_car)+100))
        ##os.system('%s car%s ip route del 192.168.0.0/24' % (mn_wifi_dir,id_car,id_car,j_target,k_target,int(id_car)+100))
        #print('%s car%s ip route del 192.168.0.0/24' % (mn_wifi_dir,id_car,id_car,j_target,k_target,int(id_car)+100))
        os.system('%s car%s ip route add 10.%s.0.0/16 dev car%s-wlan0 > /dev/null 2>&1' % (mn_wifi_dir,id_car,j_target,id_car))
        #print('%s car%s ip route add 10.%s.0.0/16 dev car%s-wlan0' % (mn_wifi_dir,id_car,j_target,id_car))
        os.system('%s car%s ip route add 192.168.0.0/24 dev car%s-wlan0 > /dev/null 2>&1' % (mn_wifi_dir,id_car,id_car))
        #print('%s car%s ip route add 192.168.0.0/24 dev car%s-wlan0' % (mn_wifi_dir,id_car,id_car))
        return time_start_completion_phase

    def handover_process(self,mn_wifi_dir,j_source,k_source,mac_target,j_target,k_target,inter_handover,id_car,mac_Car):
        # inter_handover == 0, si el handover es a un gnb diferente
        #os.system('%s gnb%s hostapd_cli -i gnb%s-wlan1 ACCEPT_ACL ADD_MAC %s >/dev/null 2>&1' % (mn_wifi_dir, j_target, j_target, mac_Car))
        os.system('%s car%s wpa_cli -i car%s-wlan0 set_network 0 bssid %s > /dev/null 2>&1' % (mn_wifi_dir,id_car,id_car,mac_target))
        
        #if inter_handover == 0:
        #os.system('%s car%s wpa_cli -i car%s-wlan0 roam %s > /dev/null 2>&1' % (mn_wifi_dir,id_car,id_car,mac_target))        
        cmd_t = ["%s car%s wpa_cli -i car%s-wlan0 roam %s" % (mn_wifi_dir,id_car,id_car,mac_target)]
        res_roam = subprocess.Popen(cmd_t, stdout=subprocess.PIPE, shell=True)
        (out_t, err_t) = res_roam.communicate()
        
        out_t_t= str(out_t)
        if out_t_t.find("OK") > - 1:
            time.sleep(0.6)
            
            time_start_completion_phase = self.routing_configuration(mn_wifi_dir,j_target,k_target,id_car)
            os.system('%s gnb%s hostapd_cli -i gnb%s-wlan1-%s disassociate %s > /dev/null 2>&1' % (mn_wifi_dir, j_source, j_source,str(k_source-1),mac_Car))
            getAttr.time_completion_phase[id_car] =  time.time() - time_start_completion_phase
            #os.system('%s gnb%s hostapd_cli -i gnb%s-wlan1 ACCEPT_ACL DEL_MAC %s >/dev/null 2>&1' % (mn_wifi_dir, j_source, j_source, mac_Car))

            #Para usar gnb%s-wlan1 ACCEPT_ACL, modificar/descomentar home/mininet/mininet-wifi/mn_wifi/link.py (def configure_Slicing (self, cmd, intf, tag_vssids=False, id_vssids=999,nameInterface=""))
            #cmd += '\nmacaddr_acl=1'
            #sh('touch /home/mininet/v2x-slicing/single/ryu/hostapd-{}.accept'.format(nameInterface))
            #time.sleep(0.5)
            #cmd += '\naccept_mac_file=/home/mininet/v2x-slicing/single/ryu/hostapd-{}.accept'.format(nameInterface)                                    
        else:
            print("Car%s - Error Traspaso a [%s,%s] %s  -- log_wpa borrado" % (id_car,j_target,k_target,mac_target))
            # Se borra el contenido del archivo del traspaso realizado
            with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (id_car),'w') as file2: pass
        getAttr.HM_state[id_car] ='0'

        


    def calculate_handover_times(self,id_car,lat_req_car,source_mac_j_k):
        t_COMPLETED_AUTHENTICATING = 0.000000
        t_AUTHENTICATING_DISCONNECTED = 0.000000
        t_DISCONNECTED_SCANNING = 0.000000
        t_SCANNING_AUTHENTICATING = 0.000000
        t_AUTHENTICATING_ASSOCIATING = 0.000000
        t_ASSOCIATING_ASSOCIATED = 0.000000
        t_ASSOCIATED_COMPLETED=0.000000
        t_ASSOCIATED_4WAY_HANDSHAKE = 0.000000
        t_4WAY_HANDSHAKE_4WAY_HANDSHAKE = 0.000000
        t_4WAY_HANDSHAKE_GROUP_HANDSHAKE = 0.000000
        t_GROUP_HANDSHAKE_COMPLETED = 0.000000
        t_COMPLETED_COMPLETED = 0.000000
        t_COMPLETED_DISCONNECTED = 0.000000
        t_DISCONNECTED_DISCONNECTED = 0.000000

        HM_type=""

        time_preparation_phase = 0.000000
        time_execution_phase=0.000000
        #time_completion_phase = getAttr.time_completion_phase[id_car]
        
        time_total_HM=0.000000
        #time_disconnection=0.000000
        time_scanning=0.000000
        time_open_authorization=0.000000
        time_open_association=0.000000
        #time_4way_handshake_1=0.000000
        #time_4way_handshake_2=0.000000
        #time_4way_handshake_3=0.000000
        #time_4way_handshake_4=0.000000
        time_802_1X_4way_handshake=0.000000
        time_4way_handshake_group=0.000000

        #id_car_test = 0
        #if id_car == id_car_test:
        #    with open('/home/mininet/v2x-slicing/single/ryu/data-log/test_2_summary.txt','a') as file:
        #        file.write('##################################################\n')
        #        file.write('\n')
        #        file.write('\n')

        # Como cambio de slice (j,k), entonces se lee los logs para calcular los tiempos de traspaso
        with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (id_car),'r') as file:
            for linea in file.readlines():
                valores = {}
                state = ""

                if linea.find("car%s-wlan0:" % (id_car)) > - 1 and linea.find("State") > - 1:
                    valores=linea.split(": ")
                    state = valores[3][:-1]                  

                    if state == "COMPLETED -> AUTHENTICATING":
                        t_COMPLETED_AUTHENTICATING = float(valores[0])
                    elif state == "AUTHENTICATING -> DISCONNECTED":
                        t_AUTHENTICATING_DISCONNECTED = float(valores[0])
                    elif state == "DISCONNECTED -> SCANNING":
                        t_DISCONNECTED_SCANNING = float(valores[0])
                    elif state == "SCANNING -> AUTHENTICATING":
                        t_SCANNING_AUTHENTICATING = float(valores[0])
                    elif state == "AUTHENTICATING -> ASSOCIATING":
                        t_AUTHENTICATING_ASSOCIATING = float(valores[0])
                    elif state == "ASSOCIATING -> ASSOCIATED":
                        t_ASSOCIATING_ASSOCIATED = float(valores[0])
                    elif state == "ASSOCIATED -> COMPLETED":
                        t_ASSOCIATED_COMPLETED = float(valores[0])
                    elif state == "ASSOCIATED -> 4WAY_HANDSHAKE":
                        t_ASSOCIATED_4WAY_HANDSHAKE = float(valores[0])
                    elif state == "4WAY_HANDSHAKE -> 4WAY_HANDSHAKE":
                        t_4WAY_HANDSHAKE_4WAY_HANDSHAKE = float(valores[0])
                    elif state == "4WAY_HANDSHAKE -> GROUP_HANDSHAKE":
                        t_4WAY_HANDSHAKE_GROUP_HANDSHAKE = float(valores[0])
                    elif state == "GROUP_HANDSHAKE -> COMPLETED":
                        t_GROUP_HANDSHAKE_COMPLETED = float(valores[0])
                    elif state == "COMPLETED -> COMPLETED":
                        t_COMPLETED_COMPLETED = float(valores[0])                                            
                    elif state == "COMPLETED -> DISCONNECTED":
                        t_COMPLETED_DISCONNECTED = float(valores[0])
                    elif state == "DISCONNECTED -> DISCONNECTED":
                        t_DISCONNECTED_DISCONNECTED = float(valores[0])
                    else:
                        print(linea,end="")

                    #if id_car == id_car_test:
                    #    with open('/home/mininet/v2x-slicing/single/ryu/data-log/test_2_summary.txt','a') as file:                        
                    #        file.write(linea)
                        
                else:
                    pass

        # Se borra el contenido del archivo del traspaso realizado
        print("* log_wpa borrado")
        with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (id_car),'w') as file2: pass

        
        if t_AUTHENTICATING_DISCONNECTED > 0 and t_DISCONNECTED_DISCONNECTED < 0.00001 and t_COMPLETED_AUTHENTICATING > 0:
            HM_type = "inter-slice"
            #time_scanning = t_SCANNING_AUTHENTICATING - t_DISCONNECTED_SCANNING
            #time_open_authorization = (t_AUTHENTICATING_DISCONNECTED - t_COMPLETED_AUTHENTICATING) + (t_AUTHENTICATING_ASSOCIATING - t_SCANNING_AUTHENTICATING)
            time_open_authorization = (t_AUTHENTICATING_ASSOCIATING - t_COMPLETED_AUTHENTICATING)
            #time_disconnection = t_DISCONNECTED_SCANNING - t_AUTHENTICATING_DISCONNECTED
            time_open_association = t_ASSOCIATING_ASSOCIATED - t_AUTHENTICATING_ASSOCIATING
            #time_4way_handshake_1 = t_ASSOCIATED_4WAY_HANDSHAKE - t_ASSOCIATING_ASSOCIATED
            #time_4way_handshake_2 = t_4WAY_HANDSHAKE_4WAY_HANDSHAKE - t_ASSOCIATED_4WAY_HANDSHAKE
            #time_4way_handshake_3 = t_4WAY_HANDSHAKE_GROUP_HANDSHAKE - t_4WAY_HANDSHAKE_4WAY_HANDSHAKE
            #time_4way_handshake_4 = t_GROUP_HANDSHAKE_COMPLETED - t_4WAY_HANDSHAKE_GROUP_HANDSHAKE
            time_802_1X_4way_handshake = t_4WAY_HANDSHAKE_GROUP_HANDSHAKE - t_ASSOCIATING_ASSOCIATED
            time_4way_handshake_group = t_GROUP_HANDSHAKE_COMPLETED - t_4WAY_HANDSHAKE_GROUP_HANDSHAKE
            #time_preparation_phase = time_scanning
        elif t_ASSOCIATED_COMPLETED  > 0:
            HM_type = "intra-slice"
            time_open_authorization = t_AUTHENTICATING_ASSOCIATING - t_COMPLETED_AUTHENTICATING
            time_open_association = t_ASSOCIATED_COMPLETED - t_AUTHENTICATING_ASSOCIATING
            #time_completed_completed = t_COMPLETED_COMPLETED - t_ASSOCIATED_COMPLETED
        else:
            #t_DISCONNECTED_DISCONNECTED > 0:
            HM_type = "802.11_rsna"
            #time_disconnection = t_DISCONNECTED_SCANNING - t_DISCONNECTED_DISCONNECTED
            time_scanning = t_SCANNING_AUTHENTICATING - t_DISCONNECTED_SCANNING
            print("%f = %f - %f" % (time_scanning,t_SCANNING_AUTHENTICATING,t_DISCONNECTED_SCANNING))
            time_open_authorization = t_AUTHENTICATING_ASSOCIATING - t_SCANNING_AUTHENTICATING
            time_open_association = t_ASSOCIATING_ASSOCIATED - t_AUTHENTICATING_ASSOCIATING
            #time_4way_handshake_1 = t_ASSOCIATED_4WAY_HANDSHAKE - t_ASSOCIATING_ASSOCIATED
            #time_4way_handshake_2 = t_4WAY_HANDSHAKE_4WAY_HANDSHAKE - t_ASSOCIATED_4WAY_HANDSHAKE
            #time_4way_handshake_3 = t_4WAY_HANDSHAKE_GROUP_HANDSHAKE - t_4WAY_HANDSHAKE_4WAY_HANDSHAKE
            #time_4way_handshake_4 = t_GROUP_HANDSHAKE_COMPLETED - t_4WAY_HANDSHAKE_GROUP_HANDSHAKE        
            time_802_1X_4way_handshake = t_4WAY_HANDSHAKE_GROUP_HANDSHAKE - t_ASSOCIATING_ASSOCIATED
            time_4way_handshake_group = t_GROUP_HANDSHAKE_COMPLETED - t_4WAY_HANDSHAKE_GROUP_HANDSHAKE
                    
        
        time_preparation_phase = time_scanning
        time_execution_phase = (time_open_authorization + time_open_association + time_802_1X_4way_handshake + time_4way_handshake_group)
        time_total_HM = (time_preparation_phase + time_execution_phase + getAttr.time_completion_phase[id_car])
        

        #if time_total_HM >= 0:
        with open('/home/mininet/v2x-slicing/single/ryu/data-log/test_2_802_11_rsna.csv','a') as file:
            file.write('%s,car%s,%s,%s,%s,%f,%f,%f,%f,%f,%f,%f,%f,%f,\n' % (HM_type,id_car,lat_req_car,getAttr.currentAP[id_car],source_mac_j_k,time_total_HM,time_preparation_phase,time_execution_phase,getAttr.time_completion_phase[id_car],time_scanning,time_open_authorization,time_open_association,time_802_1X_4way_handshake,time_4way_handshake_group))

        """
        if id_car == 0:
            with open('/home/mininet/v2x-slicing/single/ryu/data-log/test_2_summary.txt','a') as file:
                #file.write('T_disconnection:   %f - %f = %f \n' % (time_disc,t_DISCONNECTED_SCANNING,           t_DISCONNECTED_DISCONNECTED))
                #file.write('T_scan:            %f - %f = %f \n' % (time_scan,t_SCANNING_AUTHENTICATING,         t_DISCONNECTED_SCANNING))
                #file.write('T_authentication:  %f - %f = %f \n' % (time_auth,t_AUTHENTICATING_ASSOCIATING,      t_SCANNING_AUTHENTICATING))
                #file.write('T_association:     %f - %f = %f \n' % (time_asso,t_ASSOCIATING_ASSOCIATED,          t_AUTHENTICATING_ASSOCIATING))
                #file.write('T_4way_handshake:  %f - %f = %f \n' % (time_4way,t_4WAY_HANDSHAKE_GROUP_HANDSHAKE,  t_ASSOCIATING_ASSOCIATED))
                #file.write('T_group_handshake: %f - %f = %f \n' % (time_4way_group,t_GROUP_HANDSHAKE_COMPLETED,     t_4WAY_HANDSHAKE_GROUP_HANDSHAKE))

                file.write('###################### %s ############################\n' % HM_type)
                file.write('\n')
                file.write('time_preparation_phase:   %f \n' % (time_preparation_phase))
                file.write('time_execution_phase:     %f \n' % (time_execution_phase))
                file.write('time_completion_phase:    %f \n' % (getAttr.time_completion_phase[id_car]))
                file.write('---------------------------------------\n')
                file.write('time_total_HM:           %f\n' % (time_total_HM))
                file.write('\n')
                file.write('\n')
                file.write('%f + %f + %f + %f \n' % (time_open_authorization,time_open_association,time_802_1X_4way_handshake,time_4way_handshake_group))
                file.write('%f + %f + %f \n'% (time_preparation_phase,time_execution_phase,getAttr.time_completion_phase[id_car]))
                file.write('\n')
                file.write('\n')
        else:
            pass
        """   


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)
            print("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)
        
        msg = ev.msg

        pkt = packet_temp.Packet(msg.data)

        mn_wifi_dir = '/home/mininet/mininet-wifi/util/m'

        _ipv4 = pkt.get_protocol(ipv4.ipv4)
        #print ("**** _ipv4: %s" % _ipv4)

        if hasattr(_ipv4, 'proto'):

            if _ipv4.proto == 17 and _ipv4.dst == '192.168.0.200':  # UDP

                _wifi = pkt.get_protocol(wifi.WiFiMsg)

                id_car=0
                time_scanning   = _wifi.time_Scan         # Tiempo que tardo el escaneo
                mac_Car         = _wifi.mac_Car           # La mac del carro
                id_car          = int(mac_Car[-5:-3],16)

                if time_scanning != getAttr.time_scanning_temp[id_car] and getAttr.HM_state[id_car] =='0':
                    getAttr.time_scanning_temp[id_car] = time_scanning
                    mac_Car = _wifi.mac_Car                     # La mac del carro
                    lat_req_car = int(_wifi.lat_req_car)        # QoS - Latencia requerida por el carro
                    nSlice = _wifi.nSlice                       # Numero de slices encontrados
                    source_mac_j_k = _wifi.source_mac_j_k       # mac_jk_conectado
                    j_k_list = _wifi.j_k_list                   # diccionario que contiene los datos de los slice
                        # slice_id
                            # target_mac_j_k
                            # latency_server
                            # load_j_k_t_1
                            # load_j_k_t
                            # rssi_j_k_car_id_t_1
                            # rssi_j_k_car_id_t
                    #print(mac_Car)
                    #print(nSlice)
                    #print(time_scanning)
                    #print(source_mac_j_k)
                    #print(j_k_list)
                    
                    ##############################################################################
                    # Comprueba si el carro esta conectado a un gnb
                    if source_mac_j_k != "DISCONNECTED":

                        j_source = 0
                        k_source = 0
                        j_target = 0
                        k_target = 0
                        id_car=0
                        jk_source=0

                        j_source = int(source_mac_j_k[-5:-3],16) - getAttr.n_Cars + 1
                        k_source = int(source_mac_j_k[15:],16)
                        # Obtiene el identificador de Slice
                        jk_source= int(str(j_source) + str(k_source))
                        #id_car = int(mac_Car[-2:])
                        id_car = int(mac_Car[-5:-3],16)

                        #if getAttr.currentAP[id_car] == '':
                        if getAttr.currentAP[id_car] != source_mac_j_k:
                            #self.calculate_handover_times(id_car,lat_req_car,source_mac_j_k)
                            if getAttr.currentAP[id_car] == "DISCONNECTED":
                                time_start_completion_phase = self.routing_configuration(mn_wifi_dir,j_source,k_source,id_car)
                                getAttr.time_completion_phase[id_car] = time.time() - time_start_completion_phase
                                
                            hilo_calculate_handover_times = Thread(target=self.calculate_handover_times, args=(id_car,lat_req_car,source_mac_j_k,), daemon=True)
                            hilo_calculate_handover_times.start()
                            getAttr.currentAP[id_car] = source_mac_j_k

                        # Faltaria evaluar o programar el caso de una red con densidad alta de gnb, dado que toca predecir la ruta/dirección
                        # Verifica las variables iniciadoras de traspaso
                        # Primera opcion de traspaso, intensidad de señal degradada
                        
                        #print("Car%s RSSI: %s" % (id_car, j_k_list[jk_source][5]))
                        if int(j_k_list[jk_source][5]) <= getAttr.threshold_rssi_handover:
                            #print("Tomando decision")
                            # Verificar si se esta alejando (rssi_t - rssi_t_1 = es menor que cero)
                            if (int(j_k_list[jk_source][5]) - int(j_k_list[jk_source][4])) < 0:
                                #print("Traspaso")
                                # Evaluar la load y rssi para seleccionar el slice_jk objetivo 
                                # 1. Evaluar la carga, es decir, encontrar el slice la menor carga
                                menorCarga = 100
                                jk_target_menor_carga = None
                                jk_target_LLC_menor_carga = None

                                for temp_idSlice in j_k_list:
                                    # Solamente Evalue los slices que estan en otros gnb j
                                    t_temp_idSlice = str(temp_idSlice)
                                    temp_j = t_temp_idSlice[:-1]
                                    if int(temp_j) != j_source:
                                        
                                        # Verificar si se esta acercando a ese slice, es decir, el rssi mejora
                                        if (int(j_k_list[temp_idSlice][5]) - int(j_k_list[temp_idSlice][4])) > 0:
                                            
                                            # Encontrar el slice la menor carga
                                            if menorCarga >= int(j_k_list[temp_idSlice][3]):
                                                menorCarga = int(j_k_list[temp_idSlice][3])
                                                jk_target_menor_carga = int(temp_idSlice)
                                                #print("Posible 1")
                                                
                                                # Verificar si ese slice es de baja latencia
                                                if  int(j_k_list[temp_idSlice][3]) < getAttr.threshold_load and lat_req_car <= int(j_k_list[temp_idSlice][1]):                                                    
                                                    #print("Posible 2")
                                                    jk_target_LLC_menor_carga = jk_target_menor_carga
                                                    
                                # Hacer el traspaso inter-gnb
                                # Como es traspaso hacia otro gnb, entonces toca deshautenticar
                                if jk_target_menor_carga == None:
                                    #print("1.0 Mantener conexion %s" % jk_source)
                                    print("",end="")
                                elif jk_target_LLC_menor_carga != None and jk_target_LLC_menor_carga != jk_source:
                                    print("Car%s - 1.1 Traspaso de %s a %s" % (id_car,jk_source,jk_target_LLC_menor_carga))
                                    # Traspaso a jk_target_LLC_menor_carga
                                    j_target = int(j_k_list[jk_target_LLC_menor_carga][0][-5:-3],16) - getAttr.n_Cars + 1
                                    k_target = int(j_k_list[jk_target_LLC_menor_carga][0][15:],16)

                                    hilo = Thread(target=self.handover_process, args=(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_LLC_menor_carga][0],j_target,k_target,0,id_car,mac_Car,), daemon=True)
                                    hilo.start()
                                    getAttr.HM_state[id_car] ='1'
                                    #self.handover_process(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_LLC_menor_carga][0],j_target,k_target,0,id_car,mac_Car)

                                elif jk_target_LLC_menor_carga != jk_target_menor_carga and jk_target_menor_carga != jk_source:
                                    print("Car%s - 1.2 Traspaso de %s a %s" % (id_car,jk_source,jk_target_menor_carga))
                                    # Traspaso a jk_target_menor_carga
                                    j_target = int(j_k_list[jk_target_menor_carga][0][-5:-3],16) - getAttr.n_Cars + 1
                                    k_target = int(j_k_list[jk_target_menor_carga][0][15:],16)

                                    hilo = Thread(target=self.handover_process, args=(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_menor_carga][0],j_target,k_target,0,id_car,mac_Car,), daemon=True)
                                    hilo.start()
                                    getAttr.HM_state[id_car] ='1'
                                    #self.handover_process(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_menor_carga][0],j_target,k_target,0,id_car,mac_Car)
                                else:
                                    #print("1.3 Mantener conexion %s" % jk_source)
                                    print("",end="")
                            # Verificar si se esta acercando (rssi_t - rssi_t_1 = es mayor que cero)
                            #elif (j_k_list[jk_source][5] - j_k_list[jk_source][4]) > 0:
                            #    print("No Traspaso")
                            elif  j_k_list[jk_source][4] == j_k_list[jk_source][5]:
                                #print("1.4 Sin desicion - Carro quieto")
                                print("",end="")
                            else:
                                #print("1.5 Sin desicion - Mejorando senal")
                                print("",end="")                                

                        # Segunda opcion de traspaso, dado que existe carga alta en el slice actual
                        elif int(j_k_list[jk_source][3]) > getAttr.threshold_load:
                            # Verificar si se esta alejando (rssi_t - rssi_t_1 = es menor que cero)
                            #if (int(j_k_list[jk_source][5]) - int(j_k_list[jk_source][4])) < 0:
                            #print("Traspaso")
                            # Evaluar la load y rssi para seleccionar el slice_jk objetivo 
                            # 1. Evaluar la carga, es decir, encontrar el slice la menor carga
                            menorCarga = 100
                            jk_target_menor_carga = None
                            jk_target_LLC_menor_carga = None
                            for temp_idSlice in j_k_list:
                                # Evalue los slices que estan en otros gnb j
                                #if temp_idSlice//10 != j_source:
                                
                                # Verificar si se esta acercando a ese slice, es decir, el rssi mejora
                                #if (j_k_list[temp_idSlice][5] - j_k_list[temp_idSlice][4]) > 0:

                                # Encontrar el slice con la menor carga
                                
                                if menorCarga >= int(j_k_list[temp_idSlice][3]):
                                    menorCarga = int(j_k_list[temp_idSlice][3])
                                    jk_target_menor_carga = int(temp_idSlice)
                                    # Verificar si ese slice es de baja latencia
                                    
                                    # 1/3 Cambio
                                    #if  lat_req_car <= int(j_k_list[temp_idSlice][1]):
                                    if  lat_req_car <= int(j_k_list[temp_idSlice][1]) and int(j_k_list[temp_idSlice][3]) < getAttr.threshold_load:
                                        jk_target_LLC_menor_carga = jk_target_menor_carga                                  
                                        
                                        #t_temp_idSlice = str(temp_idSlice)
                                        #temp_j = t_temp_idSlice[:-1]
                                        #temp_k = t_temp_idSlice[-1:]
                                        #if temp_j == j_source:                                    
                                        
                                        #if temp_idSlice//10 == j_source:
                                        #    break



                            # Hacer el traspaso intra/inter gnb
                            if jk_target_menor_carga == None:
                                #print("2.0 Mantener conexion %s" % jk_source)
                                print("",end="")
                            elif jk_target_LLC_menor_carga != None and jk_target_LLC_menor_carga != jk_source:
                                # 1. Traspaso a un slice LLC 
                                # 1.1 Verificar si el slice LLC es intra (dentro del mismo gnb)
                                t_temp_idSlice = str(jk_target_LLC_menor_carga)
                                temp_j = t_temp_idSlice[:-1]
                                #if jk_target_LLC_menor_carga//10 == j_source:
                                if int(temp_j) == j_source:
                                    print("Car%s - 2.1 Traspaso de %s a %s" % (id_car,jk_source,jk_target_LLC_menor_carga))
                                    # Traspaso a jk_target_LLC_menor_carga
                                    j_target = int(j_k_list[jk_target_LLC_menor_carga][0][-5:-3],16) - getAttr.n_Cars + 1
                                    k_target = int(j_k_list[jk_target_LLC_menor_carga][0][15:],16)
                                    
                                    hilo = Thread(target=self.handover_process, args=(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_LLC_menor_carga][0],j_target,k_target,1,id_car,mac_Car,), daemon=True)
                                    hilo.start()
                                    getAttr.HM_state[id_car] ='1'
                                    #self.handover_process(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_LLC_menor_carga][0],j_target,k_target,1,id_car,mac_Car)

                                else:
                                    print("Car%s - 2.2 Traspaso de %s a %s" % (id_car,jk_source,jk_target_LLC_menor_carga))
                                    # 1.2 Inter slice (entre diferentes gnb)
                                    ## Traspaso a jk_target_LLC_menor_carga
                                    j_target = int(j_k_list[jk_target_LLC_menor_carga][0][-5:-3],16) - getAttr.n_Cars + 1
                                    k_target = int(j_k_list[jk_target_LLC_menor_carga][0][15:],16)

                                    hilo = Thread(target=self.handover_process, args=(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_LLC_menor_carga][0],j_target,k_target,0,id_car,mac_Car,), daemon=True)
                                    hilo.start()
                                    getAttr.HM_state[id_car] ='1'
                                    #self.handover_process(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_LLC_menor_carga][0],j_target,k_target,0,id_car,mac_Car)

                                # 2/3 Cambio
                                # 2. Traspaso a un slice NO LLC
                            elif jk_target_LLC_menor_carga != jk_target_menor_carga and jk_target_menor_carga != jk_source:
                                # 2.1 Verificar si el slice NO LLC, es intra (dentro del mismo gnb)
                                t_temp_idSlice = str(jk_target_menor_carga)
                                temp_j = t_temp_idSlice[:-1]
                                if int(temp_j) == j_source:
                                    print("Car%s - 2.3 Traspaso de %s a %s" % (id_car,jk_source,jk_target_menor_carga))
                                    # Traspaso a jk_target_menor_carga
                                    j_target = int(j_k_list[jk_target_menor_carga][0][-5:-3],16) - getAttr.n_Cars + 1
                                    k_target = int(j_k_list[jk_target_menor_carga][0][15:],16)
                                    
                                    hilo = Thread(target=self.handover_process, args=(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_menor_carga][0],j_target,k_target,1,id_car,mac_Car,), daemon=True)
                                    hilo.start()
                                    getAttr.HM_state[id_car] ='1'
                                    #self.handover_process(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_menor_carga][0],j_target,k_target,1,id_car,mac_Car)
                                else:
                                    print("Car%s - 2.4 Traspaso de %s a %s" % (id_car,jk_source,jk_target_menor_carga))
                                    # Inter slice (entre diferentes gnb)
                                    # Traspaso a jk_target_menor_carga
                                    j_target = int(j_k_list[jk_target_menor_carga][0][-5:-3],16) - getAttr.n_Cars + 1
                                    k_target = int(j_k_list[jk_target_menor_carga][0][15:],16)

                                    hilo = Thread(target=self.handover_process, args=(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_menor_carga][0],j_target,k_target,0,id_car,mac_Car,), daemon=True)
                                    hilo.start()
                                    getAttr.HM_state[id_car] ='1'
                                    #self.handover_process(mn_wifi_dir,j_source,k_source,j_k_list[jk_target_menor_carga][0],j_target,k_target,0,id_car,mac_Car)
                                
                            else:
                                #print("2.5 Mantener conexion %s" % jk_target_menor_carga)
                                print("",end="")
                        else:
                            #print("0. Mantener conexion %s" % jk_source)
                            print("",end="")
                            
                        
                #elif _udp.src_port == 8001: #Controller to Controller
                #    #elif _tcp.src_port == 8001: #Controller to Controller
                #    _wifi = pkt.get_protocol(wifi.WiFiCtoCMsg)
                #   self.logger.info("wifiCtoC msg:: mac_Car %s, source_mac_j_k %s",
                #                     _wifi.mac_Car, _wifi.source_mac_j_k)
