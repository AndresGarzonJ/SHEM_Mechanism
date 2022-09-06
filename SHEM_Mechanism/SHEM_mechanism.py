import subprocess
import os
import logging
import sys

import time
from threading import Thread


class Shem():    
    def __init__(self,n_Vehicles,threshold_load,threshold_rssi_handover,mn_wifi_dir):
        self.n_Vehicles = n_Vehicles
        self.threshold_load = threshold_load
        self.threshold_rssi_handover = threshold_rssi_handover
        self.mn_wifi_dir = mn_wifi_dir
        
        self.time_scanning_temp = {0:None, 1:None,2:None,3:None,4:None,5:None,6:None,7:None,8:None,9:None}
        self.currentgNB_slice = {0:'DISCONNECTED',1:'DISCONNECTED',2:'DISCONNECTED',3:'DISCONNECTED',4:'DISCONNECTED',5:'DISCONNECTED',6:'DISCONNECTED',7:'DISCONNECTED',8:'DISCONNECTED',9:'DISCONNECTED'}
        self.HM_state = {0:'0',1:'0',2:'0',3:'0',4:'0',5:'0',6:'0',7:'0',8:'0',9:'0'}
        self.time_completion_phase = {0:None,1:None,2:None,3:None,4:None,5:None,6:None,7:None,8:None,9:None}


    ########################## Monitoring ##############################################
    def monitoring(self,_wifi):
        time_scanning   = _wifi.time_Scan         # Scanning time performed by vehicle
        mac_vehicle         = _wifi.mac_vehicle           # Vehicle MAC
        id_vehicle          = int(mac_vehicle[-5:-3],16)  # Vehicle ID

        if time_scanning != self.time_scanning_temp[id_vehicle] and self.HM_state[id_vehicle] =='0':
            self.time_scanning_temp[id_vehicle] = time_scanning
            mac_vehicle = _wifi.mac_vehicle                     # La mac del carro
            lat_req_vehicle = int(_wifi.lat_req_vehicle)        # QoS - Latencia requerida por el carro
            nSlice = _wifi.nSlice                       # Numero de slices encontrados
            source_mac_j_k = _wifi.source_mac_j_k       # mac_jk_conectado
            j_k_list = _wifi.j_k_list                   # diccionario que contiene los datos de los slice
            # j_k_list[slice_id][x] :    
                # x:
                    # 0 - target_mac_j_k
                    # 1 - latency_server
                    # 2 - load_j_k_t_1
                    # 3 - load_j_k_t
                    # 4 - rssi_j_k_t_1
                    # 5 - rssi_j_k_t
            
            # Comprueba si el carro esta conectado a un gnb
            if source_mac_j_k != "DISCONNECTED":
                id_vehicle=0

                j_source = 0
                k_source = 0
                jk_source=0                

                j_source = int(source_mac_j_k[-5:-3],16) - self.n_Vehicles + 1
                k_source = int(source_mac_j_k[15:],16)
                jk_source= int(str(j_source) + str(k_source))
                id_vehicle = int(mac_vehicle[-5:-3],16)

                if self.currentgNB_slice[id_vehicle] != source_mac_j_k:
                    if self.currentgNB_slice[id_vehicle] == "DISCONNECTED":
                        time_start_completion_phase = self.routing_configuration(j_source,k_source,id_vehicle)
                        self.time_completion_phase[id_vehicle] = time.time() - time_start_completion_phase

                    thread_calculate_HM_times = Thread(target=self.calculate_HM_times, args=(id_vehicle,lat_req_vehicle,source_mac_j_k,), daemon=True)
                    thread_calculate_HM_times.start()
                    self.currentgNB_slice[id_vehicle] = source_mac_j_k
                self.evaluator(j_k_list,id_vehicle,mac_vehicle,jk_source,j_source,k_source,lat_req_vehicle)

    def calculate_HM_times(self,id_vehicle,lat_req_vehicle,source_mac_j_k):
        t_COMPLETED_AUTHENTICATING = 0.000000
        t_AUTHENTICATING_DISCONNECTED = 0.000000
        t_DISCONNECTED_SCANNING = 0.000000
        t_SCANNING_AUTHENTICATING = 0.000000
        t_AUTHENTICATING_ASSOCIATING = 0.000000
        t_ASSOCIATING_ASSOCIATED = 0.000000
        t_ASSOCIATED_COMPLETED=0.000000
        t_4WAY_HANDSHAKE_GROUP_HANDSHAKE = 0.000000
        t_GROUP_HANDSHAKE_COMPLETED = 0.000000
        t_DISCONNECTED_DISCONNECTED = 0.000000

        HM_type=""

        time_preparation_phase = 0.000000
        time_execution_phase=0.000000        
        time_total_HM=0.000000
        time_scanning=0.000000
        time_open_authorization=0.000000
        time_open_association=0.000000
        time_802_1X_4way_handshake=0.000000
        time_4way_handshake_group=0.000000


        # Como cambio de slice (j,k), entonces se lee los logs para calcular los tiempos de traspaso
        with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (id_vehicle),'r') as file:
            for linea in file.readlines():
                valores = {}
                state = ""

                if linea.find("car%s-wlan0:" % (id_vehicle)) > - 1 and linea.find("State") > - 1:
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
                    elif state == "4WAY_HANDSHAKE -> GROUP_HANDSHAKE":
                        t_4WAY_HANDSHAKE_GROUP_HANDSHAKE = float(valores[0])
                    elif state == "GROUP_HANDSHAKE -> COMPLETED":
                       t_GROUP_HANDSHAKE_COMPLETED = float(valores[0])
                    elif state == "DISCONNECTED -> DISCONNECTED":
                        t_DISCONNECTED_DISCONNECTED = float(valores[0])
                    else:
                        pass
                else:
                    pass

        # Se borra el contenido del archivo del traspaso realizado
        print("* log_wpa borrado")
        with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (id_vehicle),'w') as file2: pass

        
        if t_AUTHENTICATING_DISCONNECTED > 0 and t_DISCONNECTED_DISCONNECTED < 0.00001 and t_COMPLETED_AUTHENTICATING > 0:
            HM_type = "inter-slice"
            time_open_authorization = (t_AUTHENTICATING_ASSOCIATING - t_COMPLETED_AUTHENTICATING)
            time_open_association = t_ASSOCIATING_ASSOCIATED - t_AUTHENTICATING_ASSOCIATING
            time_802_1X_4way_handshake = t_4WAY_HANDSHAKE_GROUP_HANDSHAKE - t_ASSOCIATING_ASSOCIATED
            time_4way_handshake_group = t_GROUP_HANDSHAKE_COMPLETED - t_4WAY_HANDSHAKE_GROUP_HANDSHAKE
        elif t_ASSOCIATED_COMPLETED  > 0:
            HM_type = "intra-slice"
            time_open_authorization = t_AUTHENTICATING_ASSOCIATING - t_COMPLETED_AUTHENTICATING
            time_open_association = t_ASSOCIATED_COMPLETED - t_AUTHENTICATING_ASSOCIATING
        else:
            HM_type = "802.11_rsna"
            time_scanning = t_SCANNING_AUTHENTICATING - t_DISCONNECTED_SCANNING
            time_open_authorization = t_AUTHENTICATING_ASSOCIATING - t_SCANNING_AUTHENTICATING
            time_open_association = t_ASSOCIATING_ASSOCIATED - t_AUTHENTICATING_ASSOCIATING
            time_802_1X_4way_handshake = t_4WAY_HANDSHAKE_GROUP_HANDSHAKE - t_ASSOCIATING_ASSOCIATED
            time_4way_handshake_group = t_GROUP_HANDSHAKE_COMPLETED - t_4WAY_HANDSHAKE_GROUP_HANDSHAKE
                    
        
        time_preparation_phase = time_scanning
        time_execution_phase = (time_open_authorization + time_open_association + time_802_1X_4way_handshake + time_4way_handshake_group)
        time_total_HM = (time_preparation_phase + time_execution_phase + self.time_completion_phase[id_vehicle])
        
        with open('/home/mininet/v2x-slicing/single/ryu/data-log/test_2_802_11_rsna.csv','a') as file:
            file.write('%s,car%s,%s,%s,%s,%f,%f,%f,%f,%f,%f,%f,%f,%f,\n' % (HM_type,id_vehicle,lat_req_vehicle,self.currentgNB_slice[id_vehicle],source_mac_j_k,time_total_HM,time_preparation_phase,time_execution_phase,self.time_completion_phase[id_vehicle],time_scanning,time_open_authorization,time_open_association,time_802_1X_4way_handshake,time_4way_handshake_group))


    ########################## Evaluator ##############################################
    def evaluator(self,j_k_list,id_vehicle,mac_vehicle,jk_source,j_source,k_source,lat_req_vehicle):
        
        menorCarga = 100
        jk_target_menor_carga = None
        jk_target_LLC_menor_carga = None
        MAC_jk_target_menor_carga = None
        MAC_jk_target_LLC_menor_carga = None
        
        # Verifica las variables iniciadoras de traspaso
        # Primera opcion de traspaso, intensidad de señal degradada
        if int(j_k_list[jk_source][5]) <= self.threshold_rssi_handover:
            # Verificar si se esta alejando (rssi_t - rssi_t_1 = es menor que cero)
            if (int(j_k_list[jk_source][5]) - int(j_k_list[jk_source][4])) < 0:
                # Evaluar la load y rssi para seleccionar el slice_jk objetivo 
                # 1. Evaluar la carga, es decir, encontrar el slice la menor carga
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
                                if  int(j_k_list[temp_idSlice][3]) < self.threshold_load and lat_req_vehicle <= int(j_k_list[temp_idSlice][1]):                                                    
                                    #print("Posible 2")
                                    jk_target_LLC_menor_carga = jk_target_menor_carga
                
            # Verificar si se esta acercando (rssi_t - rssi_t_1 = es mayor que cero)
            #elif (j_k_list[jk_source][5] - j_k_list[jk_source][4]) > 0:
            #    print("No Traspaso")
            elif  j_k_list[jk_source][4] == j_k_list[jk_source][5]:
                #print("1.4 Sin desicion - Carro quieto")
                pass
            else:
                #print("1.5 Sin desicion - Mejorando senal")
                pass                                

        # Segunda opcion de traspaso, dado que existe carga alta en el slice actual
        elif int(j_k_list[jk_source][3]) > self.threshold_load:
            # Evaluar la load y rssi para seleccionar el slice_jk objetivo 
            # 1. Evaluar la carga, es decir, encontrar el slice la menor carga
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
                    
                    #if  lat_req_vehicle <= int(j_k_list[temp_idSlice][1]):
                    if  lat_req_vehicle <= int(j_k_list[temp_idSlice][1]) and int(j_k_list[temp_idSlice][3]) < self.threshold_load:
                        jk_target_LLC_menor_carga = jk_target_menor_carga                                  
                        
                        #t_temp_idSlice = str(temp_idSlice)
                        #temp_j = t_temp_idSlice[:-1]
                        #temp_k = t_temp_idSlice[-1:]
                        #if temp_j == j_source:                                    
                        
                        #if temp_idSlice//10 == j_source:
                        #    break            
        else:
            #print("0. Mantener conexion %s" % jk_source)
            pass

        if jk_target_menor_carga != None:
            MAC_jk_target_menor_carga = j_k_list[jk_target_menor_carga][0]
        if jk_target_LLC_menor_carga != None:
            MAC_jk_target_LLC_menor_carga = j_k_list[jk_target_LLC_menor_carga][0]
        
        self.actuator(j_source,k_source,jk_target_menor_carga,jk_target_LLC_menor_carga,id_vehicle,mac_vehicle,jk_source,MAC_jk_target_menor_carga,MAC_jk_target_LLC_menor_carga)


    ########################## Actuator ##############################################
    def actuator(self,j_source,k_source,jk_target_menor_carga,jk_target_LLC_menor_carga,id_vehicle,mac_vehicle,jk_source,MAC_jk_target_menor_carga,MAC_jk_target_LLC_menor_carga):

        if jk_target_menor_carga == None:
            #print("1.0 Mantener conexion %s" % jk_source)
            pass
        elif jk_target_LLC_menor_carga != None and jk_target_LLC_menor_carga != jk_source:
            print("Car%s - 1.1 HM of %s to %s" % (id_vehicle,jk_source,jk_target_LLC_menor_carga))

            thread_HM = Thread(target=self.handover_process, args=(j_source,k_source,MAC_jk_target_LLC_menor_carga,id_vehicle,mac_vehicle,), daemon=True)
            thread_HM.start()
            self.HM_state[id_vehicle] ='1'

        elif jk_target_LLC_menor_carga != jk_target_menor_carga and jk_target_menor_carga != jk_source:
            print("Car%s - 1.2 HM of %s to %s" % (id_vehicle,jk_source,jk_target_menor_carga))

            thread_HM = Thread(target=self.handover_process, args=(j_source,k_source,MAC_jk_target_menor_carga,id_vehicle,mac_vehicle,), daemon=True)
            thread_HM.start()
            self.HM_state[id_vehicle] ='1'
        else:
            #print("1.3 Remain connected %s" % jk_source)
            pass


    def handover_process(self,j_source,k_source,mac_target,id_vehicle,mac_vehicle):
        j_target = int(mac_target[-5:-3],16) - self.n_Vehicles + 1
        k_target = int(mac_target[15:],16)

        os.system('%s car%s wpa_cli -i car%s-wlan0 set_network 0 bssid %s > /dev/null 2>&1' % (self.mn_wifi_dir,id_vehicle,id_vehicle,mac_target))
        cmd_t = ["%s car%s wpa_cli -i car%s-wlan0 roam %s" % (self.mn_wifi_dir,id_vehicle,id_vehicle,mac_target)]
        res_roam = subprocess.Popen(cmd_t, stdout=subprocess.PIPE, shell=True)
        (out_t, err_t) = res_roam.communicate()
        
        out_t_t= str(out_t)
        if out_t_t.find("OK") > - 1:
            time.sleep(0.6)
            time_start_completion_phase = self.routing_configuration(j_target,k_target,id_vehicle)
            os.system('%s gnb%s hostapd_cli -i gnb%s-wlan1-%s disassociate %s > /dev/null 2>&1' % (self.mn_wifi_dir, j_source, j_source,str(k_source-1),mac_vehicle))
            self.time_completion_phase[id_vehicle] =  time.time() - time_start_completion_phase
        else:
            print("Car%s - Error Traspaso a [%s,%s] %s  -- log_wpa borrado" % (id_vehicle,j_target,k_target,mac_target))
            # Se borra el contenido del archivo del traspaso realizado
            with open('/home/mininet/v2x-slicing/single/ryu/log_wpa/car%s-wlan0.log' % (id_vehicle),'w') as file2: pass
        self.HM_state[id_vehicle] ='0' 

    def routing_configuration(self,j_target,k_target,id_vehicle):
        time_start_completion_phase = time.time()
        os.system('%s car%s ifconfig car%s-wlan0 10.%s.%s.%s netmask 255.255.255.0 > /dev/null 2>&1' % (self.mn_wifi_dir,id_vehicle,id_vehicle,j_target,k_target,int(id_vehicle)+100))
        os.system('%s car%s ip route add 10.%s.0.0/16 dev car%s-wlan0 > /dev/null 2>&1' % (self.mn_wifi_dir,id_vehicle,j_target,id_vehicle))
        os.system('%s car%s ip route add 192.168.0.0/24 dev car%s-wlan0 > /dev/null 2>&1' % (self.mn_wifi_dir,id_vehicle,id_vehicle))
        return time_start_completion_phase 