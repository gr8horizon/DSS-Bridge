# DSS_Bridge
#
# Identify available DSS boards
# Facilitate OSC command control
# 12/23/20
# P. Barton

import os, re, serial, time

# Look for connected Arduino Nano Every's...

device_names = os.listdir("/dev")
r = re.compile("tty.usbmodem.*")  # tty. or cu. (?)
port_names = [m.group(0) for m in map(r.match, device_names) if m is not None]
print("Found {} (candidate?) Digital Speaker Switch (DSS) boards at serial ports:\n".format(len(port_names)))
#print(port_names,"\n")

# Let's ask their names and states...

for port_name in port_names:
	s = serial.Serial(port=("/dev/" + port_name), baudrate=57600, dsrdtr=True, timeout=1)
	time.sleep(0.2)
	#print(s)
	s.write(b'?\n')
	x = s.readline()
	#print(x)
	print(port_name, ":", x.decode())
	s.write((x.decode()+"\n").encode())
	y = s.readline()
	print(y.decode())
	s.close()
	#time.sleep(0.1)
	#print("Closed serial port: {}".format(port_name))