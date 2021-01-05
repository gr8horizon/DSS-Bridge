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

rumps.debug_mode(True)

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
		self.DSS_button = rumps.MenuItem(title="-", callback=None)
		self.app.menu = [self.DSS_button, self.find_DSS_button]
		self.DSS = [];
		self.find_DSS()
		print(self.DSS)


	def find_DSS(self, *etc):
		# todo: keep track of: dev, DSS_ID, state, time queried, last request
		DSS_IDs = []
		port_names = glob.glob("/dev/cu.usbmodem*")

		for port_name in port_names:
			try:
				s = serial.Serial(port=(port_name), baudrate=57600, dsrdtr=True, timeout=1)
			except serial.SerialException: 
				rumps.alert(title="Audium DSS Bridge", 
					message="Could not open Serial Port:\n\n" + port_name, 
					icon_path="Audium_Logo_Question.png")
				pass
				continue 
			time.sleep(0.2)
			s.write(b'?\n')  # request DSS_ID from this port
			DSS_ID = s.readline().decode()  # contains e.g. "A\r\n"
			print(DSS_ID)
			DSS_IDs.append(DSS_ID[0])
			# s.write((DSS_ID+"\n").encode())  # request output states from DSS with this DSS_ID
			# DSS_State = s.readline()
			s.close()

		if DSS_IDs:
			self.DSS_button.title = "DSS Online: " + ' '.join(sorted(DSS_IDs))
			self.app.icon = "Audium_Logo.png"
			self.DSS = dict(zip(DSS_IDs, port_names))
			# print(self.DSS)
		else:
			self.DSS_button.title = '-'
			self.app.icon = "Audium_Logo_Question.png"
			rumps.alert(title="Audium DSS Bridge", 
				message="No DSS Found", 
				icon_path="Audium_Logo_Question.png")

	def run(self):
		self.app.run()


def filter_handler(address, *args):
    print("OSC Message Received: " + f"{address}: {args}")

def DSS_handler(address, *args):
	client.send_message("/DSS", sorted(DSSapp.DSS.keys())) 

def DSS_switcher_handler(address, *args):
	myDSS_ID = address[-1]
	s = serial.Serial(port=DSSapp.DSS[myDSS_ID], baudrate=57600, dsrdtr=True, timeout=1)

	if len(args) > 0:
		for arg in args:
			s.write((myDSS_ID + ("%02d" % arg) + "\n").encode())  # toggle output state of one switch	
			s.readline()  # dummy read (todo: turn off echo in arduino)

	s.write((myDSS_ID + "\n").encode())  # request all output states from DSS
	DSS_State = s.readline().decode()
	client.send_message("/DSS/" + myDSS_ID, DSS_State)  # Send DSS output state
	s.close()


if __name__ == '__main__':
	dispatcher = Dispatcher()
	dispatcher.map("/DSS", DSS_handler)
	dispatcher.map("/DSS/*", DSS_switcher_handler)
	dispatcher.set_default_handler(print)

	server_port = 1337  # OSC-Receive (into DSS_Bridge)
	client_port = 1338  # OSC-Send (out of DSS_Bridge)
	
	server = ThreadingOSCUDPServer(("127.0.0.1", server_port), dispatcher)
	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.start()

	client = SimpleUDPClient("127.0.0.1", client_port)  # Create client

	DSSapp = DSSBridgeApp()
	DSSapp.run()


