# DSS_Bridge
#
# Identify available DSS boards
# Facilitate OSC command control
# 12/23/20
# P. Barton
#
# * makes the assumption that all /dev/cu.usbmodem* are DSS (Arduino Nano Every)

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
	myDSS_ID = address[-1]
	s = DSSapp.SerialPorts[myDSS_ID]
	if len(args) > 0:
		for arg in args:
			if arg == "reset":
				s.write((myDSS_ID + '+\n').encode())
				time.sleep(0.2) # fixed 0.1 s Arduino delay after EEPROM readout
				s.readline()  # dummy read (todo: turn off echo in arduino?)
			elif arg == "clear":
				s.write('-\n'.encode())
				s.readline()  # dummy read (todo: turn off echo in arduino?)
			elif isinstance(arg, float): # incoming float 0.0:5.0 for LVURDJ, WTPHCE
				if arg == 0.0:
					#       1234567812345678123456781234567812345678123456781234567812345678 (64b)
					spkr = '1000000000000000100000000000000010000000000000001000000000000000'
				elif arg == 1.0:
					spkr = '0100000000000000010000000000000001000000000000000100000000000000'
				elif arg == 2.0:
					spkr = '0010000000000000001000000000000000100000000000000010000000000000'
				elif arg == 3.0:
					spkr = '0001000000000000000100000000000000010000000000000001000000000000'
				elif arg == 4.0:
					spkr = '0000100000000000000010000000000000001000000000000000100000000000'
				elif arg == 5.0:
					spkr = '0000010000000000000001000000000000000100000000000000010000000000'

				s.write((myDSS_ID + spkr + "\n").encode())
				# print("PLUGIN: " + myDSS_ID + spkr)
			elif isinstance(arg, int):
				s.write((myDSS_ID + ("%02d" % arg) + "\n").encode())  # toggle output state of one switch
				# print((myDSS_ID + ("%02d" % arg) + "\n").encode())
				# no readline here (removed from Arduino code for speed)
	else: # poll outputs if no args		
		s.write((myDSS_ID + "\n").encode())  # request all output states from DSS
		DSS_State = s.readline().decode().strip()
		# print("   MAX: " + DSS_State)
		client.send_message("/DSS/" + myDSS_ID, DSS_State[-64:])  # Send DSS output state (remove leading char)

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


