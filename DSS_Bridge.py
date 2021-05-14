# DSS_Bridge
#
# Identify available DSS boards
# Facilitate OSC command control
# P. Barton
#
# * makes the assumption that all /dev/cu.usbmodem* are DSS (Arduino Nano Every)
# see setup.py for application building instructions

import os, re, serial, time, glob
import rumps

rumps.debug_mode(False)

import socket 
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import threading


# todo: add listener to /dev for ttyusbmodem changes and store serial numbers of arduinos. lightweight polling?



class DSSBridgeApp(object):
	def __init__(self):
		self.app = rumps.App("DSS Bridge")
		self.app.icon = "Audium_Logo_Question.png"
		self.app.title = ""
		self.find_DSS_button = rumps.MenuItem(title="Find DSS...", callback=self.find_DSS)
		self.DSS_button = rumps.MenuItem(title="NO DSS Online", callback=None)
		self.app.menu = [self.DSS_button, self.find_DSS_button]
		
		self.DSS = {}  # todo: collapse this into SerialPorts
		self.SerialPorts = {}  # serial.Serial objects (open ports)
		# self.find_DSS() # now auto-checking this


	def find_DSS(self, *etc):
		# todo: keep track of: dev, DSS_ID, state, time queried, last request
		DSS_IDs = []
		port_names = glob.glob("/dev/cu.usbmodem*")
		# if set(possible_port_names) != set(self.port_names):
		# 	self.port_names = possible_port_names

		for port in self.SerialPorts.values():
			port.close()

		for port_name in port_names:
			try:
				s = serial.Serial(port=(port_name), baudrate=1000000, dsrdtr=True, timeout=1)
			except serial.SerialException: 
				rumps.alert(title="Audium DSS Bridge", message="Could not open Serial Port:\n\n" + port_name, 
					icon_path="Audium_Logo_Question.png")
				pass
				continue 
			time.sleep(0.2)
			s.write(b'?\n')  # request DSS_ID from this port
			DSS_ID = s.readline().decode()  # contains e.g. "A\r\n"
			DSS_IDs.append(DSS_ID[0])
			s.close()

		if DSS_IDs:
			self.DSS_button.title = "DSS Online: " + ' '.join(sorted(DSS_IDs))
			self.app.icon = "Audium_Logo.png"
			self.DSS = dict(zip(DSS_IDs, port_names))
			for DSS_ID in DSS_IDs:
				self.SerialPorts[DSS_ID] = serial.Serial(port=(self.DSS[DSS_ID]), baudrate=1000000, dsrdtr=True, timeout=1)
		else:
			self.DSS_button.title = 'No DSS Online'
			self.app.icon = "Audium_Logo_Question.png"
			self.DSS = {}
			# rumps.alert(title="Audium DSS Bridge", message="No DSS Found", 
				# icon_path="Audium_Logo_Question.png")

	def run(self):
		self.app.run()

def rotate(s, n):
    return s[n:] + s[:n]

def filter_handler(address, *args):
    print("OSC Message Received: " + f"{address}: {args}")

def DSS_handler(address, *args):
	DSSapp.find_DSS()
	time.sleep(0.5)
	if DSSapp.DSS:
		client.send_message("/DSS", sorted(DSSapp.DSS.keys())) 
	else:
		client.send_message("/DSS", "?")

def DSS_switcher_handler(address, *args):
	"""Handles OSC Messages: "/DSS/*"

	"""
	s4 = ('1' + '0' * 15) * 4
	myDSS_ID = address[-1]
	#print(myDSS_ID)
	#print(len(args))
	#print(args)
	s = DSSapp.SerialPorts[myDSS_ID]
	if s == 'X':
		if len(args) == 4:
			if args[0] == 1:
				s = '1'*6 + '0'*10
			else:
				s = '0'*16
			if args[1] == 1:
				s = s + '1'*6 + '0'*10
			else:
				s = s + '0'*16
			# if args[2] == 1:
			# 	s = s + 
			# *** finish this

	if len(args) == 6:
		s6 = ''.join(str(arg) for arg in args)
		s.write((myDSS_ID + (s6 + '0' * 10) * 4 + "\n").encode())
		print((myDSS_ID + (s6 + '0' * 10) * 4 + "\n"))
	elif len(args) == 1:
		# for arg in args:
			if arg == "reset":
				s.write((myDSS_ID + '+\n').encode())
				time.sleep(0.2) # fixed 0.1 s Arduino delay after EEPROM readout
				s.readline()  # dummy read (todo: turn off echo in arduino?)
			elif arg == "clear":
				s.write('-\n'.encode())
				s.readline()  # dummy read (todo: turn off echo in arduino?)
			elif isinstance(arg, float): # incoming float 0.0:5.0 for LVURDJ, WTPHCE
				spkr = s4[-int(arg):] + s4[:-int(arg)] # rotate s4 by arg
				s.write((myDSS_ID + spkr + "\n").encode())
				#print("PLUGIN: " + myDSS_ID + spkr)
			# elif isinstance(arg, int):
			# 	s.write((myDSS_ID + ("%02d" % arg) + "\n").encode())  # toggle output state of one switch
				# print((myDSS_ID + ("%02d" % arg) + "\n").encode())
	else: # poll outputs if no args		
		s.write((myDSS_ID + "\n").encode())  # request all output states from DSS
		DSS_State = s.readline().decode().strip()
		# print("   MAX: " + DSS_State)
		client.send_message("/DSS/" + myDSS_ID, DSS_State[-64:])  # Send DSS output state (remove leading char)

def obj_handler(address, *args):
	"""Handles OSC Messages: "/obj/*"
	*** just who is sending this here?
		DAW's go directly to MAX
		iPAD and controllers go directly to DAW
	"""
	myObj_ID = address.split('/')[2]  # /obj/i
	myAddress = address.split('/')[3]  # /obj/i/sub
	if myAdress == "sub":
		print('*')

	print("OSC OBJ Message Received: " + f"{address.split('/')[2]}: {args}")
	print(myAddress)

def dev_watcher():
	while True:
		time.sleep(1)  # too fast? maybe 5 s
		if set(glob.glob("/dev/cu.usbmodem*")) != set(DSSapp.DSS.values()):
			DSSapp.find_DSS()


if __name__ == '__main__':
	DSSapp = DSSBridgeApp()
	# print(set(DSSapp.DSS.values()))

	#---- OSC ----
	dispatcher = Dispatcher()
	dispatcher.map("/DSS", DSS_handler)
	dispatcher.map("/DSS/*", DSS_switcher_handler)
	dispatcher.map("/obj/*", obj_handler) # sound object
	dispatcher.set_default_handler(print)
	
	# IPAD?

	server_port_PLUGIN = 1337  # OSC-Receive (into DSS_Bridge)
	server_PLUGIN = ThreadingOSCUDPServer(("192.168.42.68", server_port_PLUGIN), dispatcher)
	server_thread_PLUGIN = threading.Thread(target=server_PLUGIN.serve_forever)
	server_thread_PLUGIN.start()

	server_port_MAX = 1336  # OSC-Receive (into DSS_Bridge)
	server_MAX = ThreadingOSCUDPServer(("192.168.42.68", server_port_MAX), dispatcher)
	server_thread_MAX = threading.Thread(target=server_MAX.serve_forever)
	server_thread_MAX.start()

	client_port = 1338  # OSC-Send (out of DSS_Bridge)
	client = SimpleUDPClient("192.168.42.255", client_port)  # .255 = Broadcast to 192.168.42.*
	client._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	
	#--------------

	# todo: think about what to do when we lose all or 1 or gain an additional one.
	devwatcher_thread = threading.Thread(target=dev_watcher)
	devwatcher_thread.start()

	DSSapp.run()


