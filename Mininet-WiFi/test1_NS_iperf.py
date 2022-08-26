'!/usr/bin/env python2.7'

import logging
import os, sys
import collections
from threading import Thread, Event 
from time import sleep

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
MODULE_PATH_2 = "/home/mininet/v2x-slicing/single/ryu/lib/python2.7/site-packages/scapy"
sys.path.append(os.path.dirname(os.path.expanduser(MODULE_PATH_2)))
from scapy.all import *
#from scapy import *
import time

"""
La red tiene 3 servidores, y cada gNB tiene 3 slices

slice Non-V2N = 10 Mbps --- gNB{J}-wlan1-1  --- 192.168.0.220 --- 10.{J}.1.{id_car+100}  --- iperf port 5001
slice V2N-1   = 25 Mbps --- gNB{J}-wlan1-2  --- 192.168.0.221 --- 10.{J}.2.{id_car+100}  --- iperf port 5002
slice V2N-2   = 30 Mbps --- gNB{J}-wlan1-3  --- 192.168.0.222 --- 10.{J}.3.{id_car+100}  --- iperf port 5003
"""

# [Non-V2N, V2N-1, V2N-2]
bw_Apps = (10,25,35) # [bw Mbps]

path_Mininet_WiFi = "/home/mininet/mininet-wifi/util/m"
path_data_log = "/home/mininet/v2x-slicing/single/ryu/data-log"
filter_bw = "| grep % | grep -Po '[0-9.]*(?= Mbits/sec)'"
id_car = int(sys.argv[1])
n_iperfs = int(sys.argv[2])
ip_car = ""
j=0
k=0
ip_v2n=0
bw_ref=0
error=0

if ip_car == "":
	cmd2 = ["%s car%s ifconfig car%s-wlan0 | grep 'inet ' | awk -F'[: ]+' '{ print $3 }'" 
			% (path_Mininet_WiFi,id_car,id_car)]
	address2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(out2, err2) = address2.communicate()
	ip_car = str(out2).split('\n')[0][2:-3]
	j = int(ip_car.split('.')[1])
	k = int(ip_car.split('.')[2])
	ip_v2n = k - 1

	if k==1:
		bw_ref = bw_Apps[0]
	elif k==2:
		bw_ref = bw_Apps[1]
	elif k==3:
		bw_ref = bw_Apps[2]
	else
		bw_ref = 0


while n_iperfs < 100:
	cmd1 = ["%s car%s iperf -p 500%s -t 5 -c 192.168.0.22%s -u -b54M %s"	% (path_Mininet_WiFi,id_car,k,ip_v2n,filter_bw)]
	address1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(out1, err1) = address1.communicate()
	bw_iperf = str(out1).split('\n')[0][2:-3]
	#bw_iperf = str(out1).split('\n')[0]
	print(str(n) + " - slice "+str(j)+str(k)+" - " + str(out1) + " - "+ bw_iperf)

	# Error
	error = (abs(bw_iperf - bw_ref))/bw_ref

	# car,j,k,bw_iperf,bw_ref,error
	os.system("echo 'car%s,%s,%s,%s,%s,%s' >> %s/cars_iperf.csv"% (id_car,j,k,bw_iperf,bw_ref,error,path_data_log))
	sleep(2)
	n_iperfs = n_iperfs + 1