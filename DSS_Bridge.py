# DSS_Bridge
#
# Identify available DSS boards
# Facilitate OSC command control
# 12/23/20
# P. Barton

import os, re, serial, time
import rumps

rumps.debug_mode(True)

import socket 
from pythonosc.udp_client import SimpleUDPClient

ip = socket.gethostbyname(socket.gethostname())
port = 8000

client = SimpleUDPClient(ip, port)  # Create client

client.send_message("/some/address", 123)   # Send float message
client.send_message("/some/address", [1, 2., "hello"])  # Send message with int, float and string

# todo: add listener to /dev for ttyusbmodem changes and store serial numbers of arduinos. lightweight polling?

class DSSBridgeApp(object):
	def __init__(self):
		self.app = rumps.App("DSS Bridge")
		self.app.icon = "Audium_Logo_Question.png"
		self.app.title = ""
		self.find_DSS_button = rumps.MenuItem(title="Find DSS...", callback=self.find_DSS)
		self.DSS_button = rumps.MenuItem(title="-", callback=None)
		self.app.menu = [self.DSS_button, self.find_DSS_button]
		self.find_DSS()

	def find_DSS(self, *etc):
		# todo: keep track of: dev, DSS_ID, state, time queried, last request
		DSS_IDs = []
		device_names = os.listdir("/dev")
		r = re.compile("cu.usbmodem.*")  # tty. doesn't give you exclusive access (cu. does)
		port_names = [m.group(0) for m in map(r.match, device_names) if m is not None]

		for port_name in port_names:
			try:
				s = serial.Serial(port=("/dev/" + port_name), baudrate=57600, dsrdtr=True, timeout=1)
			except serial.SerialException: 
				rumps.alert(title="Audium DSS Bridge", message="Could not open Serial Port:\n\n /dev/"+port_name, icon_path="Audium_Logo_Question.png")
				pass
				break 
			time.sleep(0.2)
			s.write(b'?\n')  # request DSS_ID from this port
			DSS_ID = s.readline().decode()
			print(DSS_ID)
			DSS_IDs.append(DSS_ID)
			# s.write((DSS_ID+"\n").encode())  # request output states from DSS with this DSS_ID
			# DSS_State = s.readline()
			s.close()

		if DSS_IDs:
			self.DSS_button.title = "DSS Online: " + ' '.join(sorted(DSS_IDs))
			# self.app.title = "DSS"
			self.app.icon = "Audium_Logo.png"
		else:
			self.DSS_button.title = '-'
			# self.app.title = "DSS?"
			self.app.icon = "Audium_Logo_Question.png"
			rumps.alert(title="Audium DSS Bridge", message="No DSS Found", icon_path="Audium_Logo_Question.png")

	def run(self):
		self.app.run()
		

if __name__ == '__main__':
	DSSapp = DSSBridgeApp()
	DSSapp.run()
