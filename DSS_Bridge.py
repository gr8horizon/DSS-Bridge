# DSS_Bridge
#
# Identify available DSS boards
# Facilitate OSC command control
# P. Barton
#
# * makes the assumption that all /dev/cu.usbmodem* are DSS (Arduino Nano Every)
# see setup.py for application building instructions
#
# requires: python3.9 (download from python.org)
#   pip3 install rumps pyserial python-osc remi

import os, re, serial, time, glob
import numpy as np
import rumps

rumps.debug_mode(False)

import socket 
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import threading

import remi

# class WebApp(remi.App, DSSapp):
# 	def __init__(self, *args):
# 		super(WebApp, self).__init__(*args)

# 	def main(self):
# 		# DSSapp.find_DSS()
# 		verticalContainer = remi.gui.Container(width=540, margin='0px auto', style={'display': 'block', 'overflow': 'hidden'})
# 		self.lbl = remi.gui.Label(DSSApp.show_state(), width=200, height=30, margin='10px')
# 		verticalContainer.append([self.lbl])
# 		return verticalContainer

# 		# DSSapp.find_DSS()

# 	# def set_lbl(value):
# 		# change the value?

class DSSBridgeApp(object):
	def __init__(self):
		self.app = rumps.App("DSS Bridge")
		self.app.icon = "Audium_Logo_Question.png"
		self.app.title = ""
		# self.log = rumps.Window(message="", title="OSC Log", default_text="", ok="OK", cancel="Clear", dimensions=(300,400))
		self.find_DSS_button = rumps.MenuItem(title="Find DSS...", callback=self.find_DSS)
		self.DSS_button = rumps.MenuItem(title="NO DSS Online", callback=None)
		self.log_button = rumps.MenuItem(title="Log", callback=self.show_log)
		self.reset_button = rumps.MenuItem(title="Reset DSS", callback=self.reset_DSS)
		self.state_button = rumps.MenuItem(title="State", callback=self.show_state)
		self.app.menu = [self.DSS_button, self.find_DSS_button, self.reset_button, self.state_button]
		self.lastOSCaddress = None
		self.lastOSCargs = []
		
		self.DSS = {}  # todo: collapse this into SerialPorts
		self.SerialPorts = {}  # serial.Serial objects (open ports)


	def show_state(self, *etc):

		for id in sorted(self.DSS):
			s = DSSapp.SerialPorts[id]
			s.write((id + "\n").encode())  # request all output states from DSS
			state_bin = s.readline().decode().strip()
			state_bin_bool = [a == '1' for a in state_bin]
			lut_A = np.array([i for i in 'LVURDE--------- LVURDE--------- LVURDE--------- LVURDE----------'])
			lut_B = np.array([i for i in 'WPHTCJ--------- WPHTCJ--------- WPHTCJ--------- WPHTCJ----------'])
			state_str = f'{id}: {state_bin}'
			if id == 'A':
				# lut_A[~state_bin_bool] = '-'
				lut_A[np.invert(state_bin_bool)] = ' '
				print(f'A: {"".join(lut_A)}')
				# print(f'A: {"".join(state_bin)}')
				# print(f'A: {"".join(lut_A[state_bin_bool])}')
			if id == 'B':
				lut_B[np.invert(state_bin_bool)] = ' '
				print(f'B: {"".join(lut_B)}')
				# print(f'B: {"".join(lut_B[state_bin_bool])}')

			# print(state_str)
		print()
		return state_str

	def reset_DSS(self, *etc):
		for id in self.DSS:
			s = DSSapp.SerialPorts[id]
			s.write((id + '+\n').encode())
			time.sleep(0.2) # fixed 0.1 s Arduino delay after EEPROM readout
			s.readline()  # dummy read (todo: turn off echo in arduino?)
			print(id + ' reset')

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
			# print(DSS_ID[0])
			DSS_IDs.append(DSS_ID[0])
			s.close()
			#self.log.default_text += port_name + "\n"
			print(f'{DSS_ID[0]} found at {port_name}')

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
	# I want to send '/DSS ALV BH XHC'

	bank_A_spkr_ids = ['L','V','U','R','D','E']
	bank_B_spkr_ids = ['W','P','H','T','C','J']

	for spkr_bank in args:
		if spkr_bank[0] == 'A':
			for spkr in spkr_bank[0][1:]:
				# switch A - find match in list of speakers
				print(spkr)
				


	# DSSapp.find_DSS()
	# time.sleep(0.5)
	# if DSSapp.DSS:
	# 	client.send_message("/DSS", sorted(DSSapp.DSS.keys())) 
	# else:
	# 	client.send_message("/DSS", "?")

def DSS_switcher_handler(address, *args):
	"""Handles OSC Messages: "/DSS/*"

	"""
	# TODO: uncomment when we're comfortable with logging... (e.g. dual Max Metro 100 fails)
	# DSSapp.log.default_text += "DSS/*: " + address + ", {}".format(args) + "\n"
	# if address == DSSapp.lastOSCaddress and set(args) == set(DSSapp.lastOSCargs):
		# return

	z_map = [ 3, 30, 13,  8,  2, 10, 14, 15, 35, 12, 11,  9,  5, -1,  0,  7,  1, -1, 34, 33, 29, 28, 19, 20, 24, 16, 17, 27, 23, 25, 26, 22, 21, 32,31, 18]

	DSSapp.lastOSCaddress = address
	DSSapp.lastOSCargs = args

	s4 = ('1' + '0' * 15) * 4
	myDSS_ID = address[-1]
	# print(myDSS_ID)
	# print(len(args))
	# print(args)
	s = DSSapp.SerialPorts[myDSS_ID]
	if myDSS_ID == 'X':
		# print(arg for arg in args)
		if len(args) == 4:
			spkr = [0] * 64
			if int(args[0]) == 1:  # Hanging
				spkr[0:6] = [1] * 6
			if int(args[1]) == 1:  # Wall
				spkr[16:22] = [1] * 6
			if int(args[2]) == 1:  # Floor
				spkr[32:36] = [1] * 4
				spkr[48:50] = [1] * 2
			if int(args[3]) == 1:  # Center
				spkr[36:38] = [1] * 2
				spkr[50:54] = [1] * 4
			spkr = ''.join(str(x) for x in spkr)
			s.write((myDSS_ID + spkr + "\n").encode())
			print((myDSS_ID + spkr + "\n"))

		if len(args) == 10: # 6 speakers first, then 4 groups
			spkr = [0] * 64
			print(args)
			if int(args[6]) == 1:  # Hanging
				spkr[0:6] = args[0:6]
			if int(args[7]) == 1:  # Wall
				spkr[16:22] = args[0:6]
			if int(args[8]) == 1:  # Floor
				spkr[32:36] = args[0:4]   # TODO: Is this the right mapping(?)
				spkr[48:50] = args[4:6]
			if int(args[9]) == 1:  # Center
				spkr[36:38] = args[4:6]
				spkr[50:54] = args[0:4]
			spkr = ''.join(str(x) for x in spkr)
			s.write((myDSS_ID + spkr + "\n").encode())
			print((myDSS_ID + spkr + "\n"))

	if len(args) == 6:
		# binary state of 6 speakers in a quadrant: repeated 4 times
		s6 = ''.join(str(int(arg)) for arg in args)
		s.write((myDSS_ID + (s6 + '0' * 10) * 4 + "\n").encode())
		print((myDSS_ID + (s6 + '0' * 10) * 4 + "\n"))
	
	elif len(args) == 2:
		# /DSS/A 16 0 --> A160
		# z_map = [4,31,14,9,3,11,15,16,36,13,12,10,6,?,1,8,2,x,35,34,30,29,20,21,25,17,18,28,24,26,27,23,22,33,32,19] # 7 missing, 5(from H3?)   [base-1!!]
		if myDSS_ID == 'Z':
			s.write((myDSS_ID + ("%02d" % z_map[args[0]]) + str(args[1]) + "\n").encode())
			print((myDSS_ID + ("%02d" % z_map[args[0]]) + str(args[1]) + "\n"))
		else:
			s.write((myDSS_ID + ("%02d" % args[0]) + str(args[1]) + "\n").encode())
			print((myDSS_ID + ("%02d" % args[0]) + str(args[1]) + "\n"))

	elif len(args) == 1:
		arg = args[0]
		if arg == "reset":
			s.write((myDSS_ID + '+\n').encode())
			time.sleep(0.2) # fixed 0.1 s Arduino delay after EEPROM readout
			s.readline()  # dummy read (todo: turn off echo in arduino?)
			print(myDSS_ID + ' reset\n')
		elif arg == "clear":
			s.write('-\n'.encode())
			s.readline()  # dummy read (todo: turn off echo in arduino?)
		elif isinstance(arg, float): # incoming float 0.0:5.0 for LVURDE, WTPHCJ
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
	s.write((f'!{args[0]:03d}\n').encode())
	print("OSC ALS Level Message Received: " + str(args[0]))
	#client.send_message("/5/battery2", (args[0] - 30) / 225.0)

# TODO: only need one ALS_Handler
def ALS_fade_handler(address, *args):
	"""Handles OSC Messages: "/ALS/fade"
	"""
	s = DSSapp.SerialPorts['L']
	s.write((f'{args[0]:+03d}\n').encode())
	print(f'OSC ALS Fade Message Received: {args[0]:+03d}')


def dev_watcher():
	while True: 
		time.sleep(1)  # too fast? maybe 5 s
		dev_names = glob.glob("/dev/cu.usbmodem*")
		#print(set(dev_names).difference(set(DSSapp.DSS.values())))
		if set(dev_names) != set(DSSapp.DSS.values()):
			print("devices different... attempting to re-find")
			DSSapp.find_DSS()


if __name__ == '__main__':

	host_ipaddresses = {
		'AudiumsacStudio' : '192.168.42.90',
		'Audiums-Mini' : '192.168.42.100',
		'Stans-MBP' : '192.168.42.67'
		}
	hostname = socket.gethostname()
	localip = host_ipaddresses[hostname] # localip = "127.0.0.1" fails (known issue)
	# print(hostname)
	print(f'Local IP: {localip}')

	DSSapp = DSSBridgeApp()
	DSSapp.find_DSS()

	# print(set(DSSapp.DSS.values()))
	
	#---- OSC ----
	dispatcher = Dispatcher()
	dispatcher.map("/DSS", DSS_handler)
	dispatcher.map("/DSS/*", DSS_switcher_handler)
	dispatcher.map("/ALS/level", ALS_handler) # Audium Lighting System
	dispatcher.map("/ALS/fade", ALS_fade_handler) # Audium Lighting System
	dispatcher.map("/obj/*", obj_handler) # sound object
	dispatcher.set_default_handler(print)
	
	# IPAD?

	# TODO: MSG User when TOO many threads are spawned!!!
	
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
	# enabled again 5/6/22
	devwatcher_thread = threading.Thread(target=dev_watcher)
	devwatcher_thread.start()

	# print(DSSapp.show_state())
	# remi.start(WebApp, debug=True, address='0.0.0.0', port=8081, start_browser=True, multiple_instance=True)

	DSSapp.run()
	

