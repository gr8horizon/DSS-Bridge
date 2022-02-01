# DSS_Bridge
#
# Identify available DSS boards
# Facilitate OSC command control
# P. Barton
#
# * makes the assumption that all /dev/cu.usbmodem* are DSS (Arduino Nano Every)
# see setup.py for application building instructions
#
# requires: python3.9, rumps, pyserial, python-osc

import os, re, serial, time, glob
import rumps

rumps.debug_mode(False)

import socket 
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import threading


class DSSBridgeApp(object):
	def __init__(self):
		self.app = rumps.App("DSS Bridge")
		self.app.icon = "Audium_Logo_Question.png"
		self.app.title = ""
		self.log = rumps.Window(message="", title="OSC Log", default_text="", ok="OK", cancel="Clear", dimensions=(300,400))
		self.find_DSS_button = rumps.MenuItem(title="Find DSS... (not auto-watching)", callback=self.find_DSS)
		self.DSS_button = rumps.MenuItem(title="NO DSS Online", callback=None)
		self.log_button = rumps.MenuItem(title="Log", callback=self.show_log)
		self.app.menu = [self.DSS_button, self.find_DSS_button, self.log_button]

		
		self.DSS = {}  # todo: collapse this into SerialPorts
		self.SerialPorts = {}  # serial.Serial objects (open ports)

	def show_log(self, *etc):
		log_response = self.log.run()
		if log_response.clicked == 0:  # cancel button
			self.log.default_text = ""

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
				#rumps.alert(title="Audium DSS Bridge", message="Could not open Serial Port:\n\n" + port_name, 
				#	icon_path="Audium_Logo_Question.png")
				pass
				continue 
			time.sleep(0.2)
			s.write(b'?\n')  # request DSS_ID from this port
			DSS_ID = s.readline().decode()  # contains e.g. "A\r\n"
			if not DSS_ID:
				s.close()
				print('ignored: ' + port_name)
				continue
			print(DSS_ID[0])
			DSS_IDs.append(DSS_ID[0])
			s.close()
			#self.log.default_text += port_name + "\n"
			print('opened: ' + port_name)

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
	# TODO: uncomment when we're comfortable with logging... (e.g. dual Max Metro 100 fails)
	# DSSapp.log.default_text += "DSS/*: " + address + ", {}".format(args) + "\n"

	s4 = ('1' + '0' * 15) * 4
	myDSS_ID = address[-1]
	#print(myDSS_ID)
	#print(len(args))
	#print(args)
	s = DSSapp.SerialPorts[myDSS_ID]
	if myDSS_ID == 'X':
		if len(args) == 4:
			spkr = [0] * 64
			if args[0] == 1:  # Hanging
				spkr[0:6] = [1] * 6
			if args[1] == 1:  # Wall
				spkr[16:22] = [1] * 6
			if args[2] == 1:  # Floor
				spkr[32:36] = [1] * 4
				spkr[48:50] = [1] * 2
			if args[3] == 1:  # Center
				spkr[36:38] = [1] * 2
				spkr[50:54] = [1] * 4
			spkr = ''.join(str(x) for x in spkr)
			s.write((myDSS_ID + spkr + "\n").encode())

	if len(args) == 6:
		# binary state of 6 speakers in a quadrant: repeated 4 times
		s6 = ''.join(str(arg) for arg in args)
		s.write((myDSS_ID + (s6 + '0' * 10) * 4 + "\n").encode())
		#print((myDSS_ID + (s6 + '0' * 10) * 4 + "\n"))
	elif len(args) == 2:
		# /DSS/A 16 0 --> A160
		s.write((myDSS_ID + ("%02d" % args[0]) + str(args[1]) + "\n").encode())

	elif len(args) == 1:
		arg = args[0]
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
		#  	s.write((myDSS_ID + ("%02d" % arg) + "\n").encode())  # toggle output state of one switch
			# print((myDSS_ID + ("%02d" % arg) + "\n").encode())
	#else: # poll outputs if no args		
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


def ALS_handler(address, *args):
	"""Handles OSC Messages: "/ALS/level"
	"""
	# *** check if L exists first
	s = DSSapp.SerialPorts['L']
	#f address.split('/')[2]
	# lvl = int(args[0] * 255.0)
	s.write(("!" + '%(lvl)03d' % {"lvl": args[0]}  + "\n").encode())
	print("OSC ALS Message Received: " + str(args[0]))


def dev_watcher():
	while True: 
		time.sleep(1)  # too fast? maybe 5 s
		dev_names = glob.glob("/dev/cu.usbmodem*")
		#print(set(dev_names).difference(set(DSSapp.DSS.values())))
		if set(dev_names) != set(DSSapp.DSS.values()):
			print("devices different... attempting to re-find")
			DSSapp.find_DSS()


if __name__ == '__main__':
	DSSapp = DSSBridgeApp()
	DSSapp.find_DSS()

	# print(set(DSSapp.DSS.values()))
	localip = socket.gethostbyname(socket.gethostname())

	#---- OSC ----
	dispatcher = Dispatcher()
	dispatcher.map("/DSS", DSS_handler)
	dispatcher.map("/DSS/*", DSS_switcher_handler)
	dispatcher.map("/ALS/level", ALS_handler) # Audium Lighting System
	# dispatcher.map("/obj/*", obj_handler) # sound object
	dispatcher.set_default_handler(print)
	
	# IPAD?

	server_port_PLUGIN = 1337  # OSC-Receive (into DSS_Bridge)
	server_PLUGIN = ThreadingOSCUDPServer((localip, server_port_PLUGIN), dispatcher)
	server_thread_PLUGIN = threading.Thread(target=server_PLUGIN.serve_forever)
	server_thread_PLUGIN.start()

	server_port_MAX = 1336  # OSC-Receive (into DSS_Bridge)
	server_MAX = ThreadingOSCUDPServer((localip, server_port_MAX), dispatcher)
	server_thread_MAX = threading.Thread(target=server_MAX.serve_forever)
	server_thread_MAX.start()

	server_port_QLAB = 1335  # OSC-Receive (into DSS_Bridge)
	server_QLAB = ThreadingOSCUDPServer((localip, server_port_QLAB), dispatcher)
	server_thread_QLAB = threading.Thread(target=server_QLAB.serve_forever)
	server_thread_QLAB.start()

	client_port = 1338  # OSC-Send (out of DSS_Bridge)
	client = SimpleUDPClient("192.168.42.255", client_port)  # .255 = Broadcast to 192.168.42.*
	client._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	
	#--------------

	# todo: think about what to do when we lose all or 1 or gain an additional one.
	# disabled until we can figure out how to deal with Metro and changing /dev names
	#devwatcher_thread = threading.Thread(target=dev_watcher)
	#devwatcher_thread.start()

	DSSapp.run()
	

