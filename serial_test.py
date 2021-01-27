import glob, serial, time
from ttictoc import tic,toc


port_names = glob.glob("/dev/cu.usbmodem*")
# time.sleep(2)
print("opening port")
# tic()
s = serial.Serial(port=port_names[0], baudrate=1000000, dsrdtr=True, timeout=1)
# print(toc())
# s.flush()
# s.flushInput()
# s.flushOutput() 
time.sleep(0.1)

tic()
for i in range(10000):
	s.write(b'?\n')
	a = s.readline()
	# print(a)
print(toc())

s.close()	