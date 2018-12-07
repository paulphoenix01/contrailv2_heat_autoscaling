#!/usr/bin/python -u

'''
Ali Zaringhalam, Juniper Networks, OpenLab, 2018
'''

import pika, sys, time,json, os, logging
import update_alarm
import update_network_device
import utils

from vnf_data import pod_images
from keystoneauth1.identity import v3
from keystoneauth1 import session
import novaclient.client
import glanceclient.client

import requests
# suppress warning
requests.packages.urllib3.disable_warnings()

global messageno
messageno = 0

auth = v3.Password(auth_url='http://192.168.250.1:35357/v3',
                   username='admin',
                   password='contrail123',
                   project_name='admin',
                   user_domain_id='default',
                   project_domain_name='default')

# sess = session.Session(auth=auth, verify='/path/to/ca.cert')
sess = session.Session(auth=auth, verify=False)

novac = novaclient.client.Client(2, session=sess)
glancec = glanceclient.client.Client('2', session=sess)

auth = v3.Password(auth_url='http://192.168.250.1:35357/v3',
                   username='admin',
                   password='contrail123',
                   project_name='admin',
                   user_domain_id='default',
                   project_domain_name='default')

# sess = session.Session(auth=auth, verify='/path/to/ca.cert')
sess = session.Session(auth=auth, verify=False)

def handle_create(instance_id):
  print ">> Handling Instance_Create Message"
  #Wait for novac to update#
  time.sleep(3)
  servers = novac.servers.list(detailed=True)
  for srv in servers:
    if (instance_id == srv.id):
      image_id = srv.image['id']
      
      if (glancec.images.get(image_id)['name'] == pod_images['vnf']['image_name']):
        print "\t > Detect vSRX creation. Adding Network Devie and Alarm to AppFormix..."
        profile = { 'name': srv.name, 'uuid': srv.id, 'interfaces': srv.addresses }
        utils.pretty(profile)
        update_network_device.add_device(profile)
        update_alarm.add_alarm(srv.name)

def handle_delete(instance_id, instance_name, image_id):
  print ">> Handling Instance_Delete Message"
  if (glancec.images.get(image_id)['name'] == pod_images['vnf']['image_name']):
    print "\t > Detect vSRX Deletion. Deleting Network Devie and Alarm from AppFormix..."
    profile = { 'name': instance_name, 'uuid': instance_id }
    update_alarm.delete_alarm(instance_name)
    update_network_device.delete_device(profile)
  else:
    print "\t > Not service_instance deletion ... Nothing to do"


# Checks to see if existing vnf VMs have been added to AppFormix.  Any uninstalled vnf with the vnf image name will be added to AppFormix.
def init_devices():
  servers = novac.servers.list(detailed=True)
  for srv in servers:
      image_id = srv.image['id']
      if (str(glancec.images.get(image_id)['name']) == pod_images['vnf']['image_name']):
        profile = { 'name': srv.name, 'uuid': srv.id, 'interfaces': srv.addresses }
        utils.pretty(profile)
        update_network_device.add_device(profile)
        update_alarm.add_alarm(srv.name)


def callback(ch, method, properties, body):
  global messageno
  messageno = messageno + 1
  print "\n\n"
  print ("----------------{}th message -----------------\n".format(messageno))
  jbody = json.loads(body)
  jdata = json.loads(jbody['oslo.message'])
  
  #print jdata
  event_type = jdata['event_type']

  print " [x] %r:%r" % (method.routing_key, event_type,)
 
  ## Instance created  ##
  if (event_type == 'compute.instance.create.end'):
    instance_id = jdata['payload']['instance_id']
    handle_create(instance_id)

  ## Instance is starting to be deleted -> delete from AppFormix #
  elif (event_type == 'compute.instance.delete.end'):
    #print jdata['payload']
    instance_id = jdata['payload']['instance_id']
    instance_name = jdata['payload']['display_name']
    image_id = jdata['payload']['image_meta']['base_image_ref']
    handle_delete(instance_id, instance_name, image_id) 

  ch.basic_ack(delivery_tag = method.delivery_tag)


init_devices()

queue_name = 'notifications.info'
parameters = pika.URLParameters('amqp://openstack:contrail123@192.168.250.1:5672/%2F')
connection = pika.BlockingConnection(parameters)

channel = connection.channel()
channel.queue_declare(queue= queue_name)
print ' [*] Waiting for messages. To exit press CTRL+C'
#channel.basic_consume(callback, queue= queue_name, no_ack=True)
channel.basic_consume(callback, queue= queue_name)

channel.start_consuming()

