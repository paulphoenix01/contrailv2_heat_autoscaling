import json, requests

### Get TokenID ###
def get_appformix_token():
	data={'UserName':'admin','Password':'contrail123','AuthType': 'openstack'}
	req = requests.post(url='http://192.168.250.3:9000/appformix/controller/v2.0/auth_credentials',headers={'Content-Type':'application/json'},data=json.dumps(data))
	resp = req.json()
	appformix_token = str(resp['Token']['tokenId'])
	return appformix_token

### Copy AppFormix Token here ###
#appformix_token = "95a2c794-a419-11e8-b163-0242ac120005"
#print appformix_token

# maps names used in scripts to image names used in your openstack.  vsrx is used an example VNF.
vnf_info = { 'image_name': 'vsrx_firewall', 'public_network': 'public_vn', \
             'left': { 'network': 'vn1', 'local-port': 'ge-0/0/0', 'remote-port': 'eth0', 'vm-name': 'vm-1' }, \
             'right': { 'network': 'vn2', 'local-port': 'ge-0/0/1', 'remote-port': 'eth0', 'vm-name': 'vm-2' }, \
             'OIDList': ['jnxJsSPUMonitoringMIB'] \
           }

pod_images = { 'cirros': 'cirros', 'kali': 'kali-cli', 'ubuntu': 'ubuntu', 'vnf': vnf_info }

## Changed in appformix_auth = openstack (old was =appformix)
rest_info = { 'appformix_token': get_appformix_token(), 'appformix_auth': 'openstack', 'alarm_json_file': 'alarm.json', \
               'alarm_url': 'http://192.168.250.3:9000/appformix/controller/v2.0/alarms', \
               'alarm_task_url': 'http://192.168.250.3:9000/appformix/controller/v2.0/task/', \
               'alarm_notification_url' : 'http://192.168.250.3:9000/appformix/controller/v2.0/alarms/notifications', \
               'notification_url' : 'http://192.168.250.3:9000/appformix/controller/v2.0/notifications',\
               'device_url': 'http://192.168.250.3:9000/appformix/v1.0/network_device_definition', \
               'device_task_url': 'http://192.168.250.3:9000/appformix/v1.0/task/' \
            }

NetworkDevice_v2 = { \
  "ConnectionInfo": [ \
    { \
    'remote_interface_name': vnf_info['right']['remote-port'], \
    'local_interface_name': vnf_info['right']['local-port'], \
    'remote_system_id': vnf_info['right']['vm-name'] \
    }, \
    {  \
    'remote_interface_name': vnf_info['left']['remote-port'], \
    'local_interface_name': vnf_info['left']['local-port'], \
    'remote_system_id': vnf_info['left']['vm-name'] \
   }],\
  "Name": "",\
  "NetworkDeviceId": "",\
  "ManagementIp": "",\
  "Source": ['user.snmp'],\
  "ChassisType": "coreswitch",\
  "MetaData": {\
    "NetworkDeviceId": "",\
    "SnmpConfig": {\
      "Community": "public",\
      "Version": "2c",\
      "OIDList": vnf_info['OIDList'] \
    }\
  },\
  "Description": ""\
}


NetworkDevice = { \
        'MetaData': { \
          'SnmpConfig': { \
            'Version': '2c', \
            'Community': 'public', \
            'OIDList': vnf_info['OIDList'] \
            } \
        }, \
        'ManagementIp': '', \
        'Name': '', \
        'Source': 'user.snmp', \
        'NetworkDeviceId': '', \
        'ChassisType': 'coreswitch', \
        'ConnectionInfo': [ \
          { \
            'remote_interface_name': vnf_info['right']['remote-port'], \
            'local_interface_name': vnf_info['right']['local-port'], \
            'remote_system_id': vnf_info['right']['vm-name'] \
          }, \
          { \
            'remote_interface_name': vnf_info['left']['remote-port'], \
            'local_interface_name': vnf_info['left']['local-port'], \
            'remote_system_id': vnf_info['left']['vm-name'] \
          } \
        ] \
}

# 'Name' of alarm as in test_fw_alarm
# 'NetworkDeviceId' of vnf as in test_fw 
# 'EventRuleId' of alarm as in TEST_FW_SESSION_ALARM 
EventRules = [ \
    { \
      'EventRule': { \
        'ProcessSetMonitorId': '', \
        'IntervalDuration': '10s', \
        'Severity': 'warning', \
        'Module': 'alarms', \
        'DatastoreId': '', \
        'Status': 'enabled', \
        'AggregateId': '', \
        'IntervalCount': 1, \
        'EventRuleType': 'static', \
        'IntervalsWithException': 1, \
        'ApplicationId': '', \
        'NetworkId': '', \
        'Name': '',  # 'Name' of alarm as in test_fw_alarm \
        'ProjectId': '', \
        'DisplayEvent': True, \
        'ComparisonFunction': 'above', \
        'EventRuleScope': 'network_device', \
        'AggregationFunction': 'average', \
        'NetworkDeviceId': '', 	# 'NetworkDeviceId' of vnf as in test_fw \
        'EventRuleId': '', 	# 'EventRuleId' of alarm as in TEST_FW_SESSION_ALARM \
        'MetricType': 'jnxJsSPUMonitoringCurrentFlowSession', \
        'CreatedBy': 'user', \
        'Threshold': 150, \
        'Mode': 'alert' \
      } \
    } \
]
