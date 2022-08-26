#!/usr/bin/python

import logging
import os, sys, subprocess
import time

csv_test_2 = "/home/mininet/v2x-slicing/single/ryu/data-log/test_2_802_11_rsna.csv"


latency_slice_app = (50,20,10)

with open(csv_test_2,'r') as file:
    for linea in file.readlines():
        valores=linea.split(",")

        #HM_type = valores[0]
        #id_car = valores[1]
        #lat_req_car = valores[2]
        #gNB_slice_source = valores[3]
        #gNB_slice_target = valores[4]
        
        latency_compliance = 'n'
        if str(valores[0]) != "802.11_rsna":        
            if  int(valores[2]) >= latency_slice_app[int(valores[4][15:],16)-1]:
                latency_compliance = 'y'
            else:
                pass

            with open('/home/mininet/v2x-slicing/single/ryu/data-log/test_3.csv','a') as file:
                file.write('%s,%s,%s,%s,%s,%s,\n' % (valores[0],valores[1],valores[2],valores[3],valores[4],latency_compliance))
        