# DSS_Bridge
#
# Identify available DSS boards
# Facilitate OSC command control
# 12/23/20
# P. Barton

import os, re, serial, time
import rumps

rumps.debug_mode(True)

class DSSBridgeApp(object):
	def __init__(self):
		self.app = rumps.App("DSS Bridge")
		self.app.icon = "Audium_Logo.png"
		self.app.title = "DSS?"
		self.find_DSS_button = rumps.MenuItem(title="Find DSS...", callback=self.find_DSS)
		self.DSS_button = rumps.MenuItem(title="-", callback=None)
		self.app.menu = [self.DSS_button, self.find_DSS_button]
		self.find_DSS()

	def find_DSS(self, *etc):
		# todo: keep track of: dev, DSS_ID, state, time queried, last request
		DSS_IDs = []
		device_names = os.listdir("/dev")
		r = re.compile("tty.usbmodem.*")  # tty. or cu. (?)
		port_names = [m.group(0) for m in map(r.match, device_names) if m is not None]

		for port_name in port_names:
			s = serial.Serial(port=("/dev/" + port_name), baudrate=57600, dsrdtr=True, timeout=1)
			time.sleep(0.2)
			s.write(b'?\n')  # request DSS_ID from this port
			DSS_ID = s.readline().decode()
			print(DSS_ID)
			DSS_IDs.append(DSS_ID)
			# s.write((DSS_ID+"\n").encode())  # request output states from DSS with this DSS_ID
			# DSS_State = s.readline()
			s.close()

		if DSS_IDs:
			self.DSS_button.title = ' '.join(sorted(DSS_IDs))
			self.app.title = "DSS"
		else:
			self.DSS_button.title = '-'
			self.app.title = "DSS?"

	def run(self):
		self.app.run()
		

if __name__ == '__main__':
	app = DSSBridgeApp()
	app.run()
