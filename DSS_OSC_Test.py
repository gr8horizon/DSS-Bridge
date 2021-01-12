import time, random 
from pythonosc.udp_client import SimpleUDPClient


client_port = 1337  # into DSS_Bridge
client = SimpleUDPClient("127.0.0.1", client_port)  

for i in range(10000):
	time.sleep(0.005)
	client.send_message("/DSS/A", random.randint(0,63))  
	client.send_message("/DSS/B", random.randint(0,63)) 
	client.send_message("/DSS/X", random.randint(0,63)) 