#! /usr/bin/env python
import json
import requests
import sys
import time
import vnf_data
import utils
from pprint import pprint
import traceback

auth_token = vnf_data.rest_info['appformix_token']
auth_type = vnf_data.rest_info['appformix_auth']
url = vnf_data.rest_info['device_url']
task_url = vnf_data.rest_info['device_task_url']
HEADERS = {'content-type': 'application/json'}
HEADERS['X-Auth-Token'] = auth_token
HEADERS['X-Auth-Type'] = auth_type

def get_interface_id(name):
    return name.replace('.', '_').replace('$', '_')

def delete_single_network_device(device_id):
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    try:
        resp = requests.delete(url=url + "/{0}".format(device_id), data=None,
                               headers=HEADERS, verify=False)
        if resp.status_code != 200:
            print ('Delete failed to network_device_definition {}: {}'.
                    format(url, resp.text))
            return False
        task_id = json.loads(resp.text).get('task_id')
        utils.poll_for_task_state(task_url, task_id)
    except Exception as e:
        print 'Exception in deleting the network_device config {}'.format(e)
        return False
    print 'Successfully deleted Network Device - {}'.format(device_id)
    return True


def post_single_network_device(data):
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    try:
        #print "/POST DATA: \n%s\n####\n" %data
        resp = requests.post(url=url, data=data,
                             headers=HEADERS, verify=False)
        if resp.status_code != 200:
            rjson = resp.json()
            if ('already exists' in  rjson['message']):
              print 'Device exists in AppFormix'
              return True
            print ('Post fail to network_device_definition {}: {}'.  format(url, resp.text))
            return False
        task_id = json.loads(resp.text).get('task_id')
        utils.poll_for_task_state(task_url, task_id)
    except Exception as e:
        traceback.print_exc()
        print 'Exception in post the network_device config {}'.format(e)
        return False
    print 'Successfully added Network Device'
    return True

def add_device(profile):
  device = vnf_data.NetworkDevice
  device['Name'] = profile['name']
  device['NetworkDeviceId'] = profile['name']
  device['ManagementIp'] = profile['interfaces']['public_vn'][0]['addr']
  interface_list = []
  device_id = device['NetworkDeviceId']
  source = device.get('Source', 'user.snmp')
  config_data = \
      {'ChassisType': device['ChassisType'],
       'NetworkDeviceId': device_id,
       'Name': device['Name'],
       'NodeType': 'physical-router',
       'Description': "",
       "Source": source,
       "ManagementIp": device["ManagementIp"],
       'ConnectionInfo': device['ConnectionInfo'],
       'MetaData': device['MetaData']}
  if device.get('AgentBaseUrl'):
      config_data['AgentBaseUrl'] = device['AgentBaseUrl']
  for entry in config_data['ConnectionInfo']:
      entry['type'] = ''
      entry['local_interface_index'] = entry['local_interface_name']
      entry['remote_interface_index'] = entry['remote_interface_name']
      interface_obj = {'InterfaceName': entry['local_interface_name'],
                       'InterfaceId':
                       get_interface_id(entry['local_interface_name'])}
      interface_list.append(interface_obj)

  config_data['InterfaceList'] = interface_list
  json_data = json.dumps(config_data)
  s = post_single_network_device(json_data)
  print 'Processed {}: post status - {}'.format(device_id, s)

def delete_device(profile):
  device = vnf_data.NetworkDevice
  device['NetworkDeviceId'] = profile['name']
  device_id = device['NetworkDeviceId']
  s = delete_single_network_device(device_id)
  print 'Processed {}: del status - {}'.format(device_id, s)
