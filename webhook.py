#!/usr/bin/python -u

"""
Very simple HTTP server in python.

Usage::
    ./dummy-web-server.py [<port>]

Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost

"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
from pprint import pprint
from sys import argv
import json, os, sys, time,yaml
###


alert_threshold = 150


#Basic HTTP Request Handler
class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write("<html><body><h1>hi!</h1></body></html>")

    def do_HEAD(self):
        self._set_headers()
    
    #Handle /POST from Appformix    
    def do_POST(self):
        self._set_headers()
        post_data = self.rfile.read(int(self.headers['Content-Length']) ) 
	data = json.loads(post_data)
	#pprint(data)
	self.wfile.write("Alarmed Received")        
	handle_alarm(data)

def get_current_number_instance():
	with open("service_instance_scaling.env") as f:
		for line in f:
			if "service_instance_number" in line:
				line = (line.rstrip()).split(' ')
				number = line[-1]
				return int(number)

#current_max_instance = 1
alarmed_instance = ''

def handle_alarm(data):
        alarm = data['status']
	pprint(alarm)
        alarm_network_device_id = alarm['entityId']

        alarm_state = alarm['state']

        if alarm_state == '':
                print "Test Alarm. ACK TEST"
                return True
	if alarm_state == 'disabled':
		print "Alarm is processed .. Nothing to do"  	
		return True	

	### Handle data here . . . ###
	desc = data['status']['description']
	desc = desc[desc.find("{"):]
	desc = desc.replace("u'","'").replace("'",'"')
	jdesc = yaml.load(json.dumps(desc))
	jdesc = json.loads(jdesc)	
	## End handle data .. ##
	

	network_device_id = jdesc['NetworkDeviceId']
        alert_value = jdesc['single']['sample_value']
	alert_status = jdesc['single']['status']

	print "Alert %s! - Instance %s - Current_Session is: %s" %(alert_status, network_device_id, alert_value)
	
	global alarmed_instance
	number_of_instance = get_current_number_instance()
	#Scale Out
	if int(alert_value) >= alert_threshold and alert_status == 'active' and number_of_instance == 1:
		print "Scaling out from 1->2 firewall service instance.."
		alarmed_instance = alarm_network_device_id
		update_heat(2)

	#Scale in
	elif int(alert_value) < alert_threshold and alert_status == 'inactive' and number_of_instance == 2 and alarmed_instance == alarm_network_device_id:
		print "Scaling in from 2->1 firewall service instance.."
		print "\t Waiting 5 minute for things to settle down ... "
		time.sleep(300)
		alarmed_instance = ''
		update_heat(1)

	else:
		print "Alarm is processed .. Nothing to do"

	number_of_instance = get_current_number_instance()
	print "--- Current Firewall Instances: %s ---\n" % (str(number_of_instance))


### Update service_instance_number in ENV file ###
def update_env_file(number):
	with open("service_instance_scaling.env", 'r') as f:
		lines = f.readlines()
	with open("service_instance_scaling.env", 'w') as f:
		for line in lines:
			if 'service_instance_number' in line:
				line = "  service_instance_number : %s\n\n" %(str(number))
			f.write(line)
	print "\tUpdated env file -> number of instance: %s" %(number)
	
def update_heat(number):
	global current_max_instance 
	current_max_instance = int(number)
	update_env_file(int(number))
	
	#Cmd to run Heatscript for updating service instance
	cmd = './update_heat.sh'

	print "\tUpdating heatscript to change number of service instance"
	os.system(cmd)

	time.sleep(15)
	print "\t... Done!\n"

		

## Run HTTP server
def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    try:
    	httpd = server_class(server_address, handler_class)
    	print 'Starting httpd...'
    	httpd.serve_forever()
    except Exception as e:
	print e
	print "Some exception .. Ignoring"
	pass

if __name__ == "__main__":
    ### Run on default port 9999 ###
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run(port=int(9999))
