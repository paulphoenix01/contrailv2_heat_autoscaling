#! /usr/bin/env python
import requests
requests.packages.urllib3.disable_warnings()
import json
import sys
import time
import utils
import vnf_data

auth_token = vnf_data.rest_info['appformix_token']
auth_type = vnf_data.rest_info['appformix_auth']

alarm_url = vnf_data.rest_info['alarm_url']
notification_url = vnf_data.rest_info['notification_url']
alarm_notification_url = vnf_data.rest_info['alarm_notification_url']
task_url = vnf_data.rest_info['alarm_task_url']

HEADERS = {'content-type': 'application/json'}
HEADERS['X-Auth-Token'] = auth_token
HEADERS['X-Auth-Type'] = auth_type

def post_alarm(data):
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    try:
        resp = requests.post(url=alarm_url, data=data, headers=HEADERS, verify=False)
        if resp.status_code != 200:
            rjson = resp.json()
            if ('already exists' in  rjson['message']):
              print '... Alarm already exists in AppFormix'
              return True
            print ('Post fail to alarms {}: {}'.  format(alarm_url, resp.text))
            return False
        task_id = json.loads(resp.text).get('task_id')
        utils.poll_for_task_state(task_url, task_id)
    except Exception as e:
        print 'Exception in post the alarm rule {}'.format(e)
        return False
    print '... Successfully added alarm'
    return True

def remove_alarm(data):
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    try:
        durl = alarm_url + '/' + data
        resp = requests.delete(url=durl, headers=HEADERS, verify=False)
        if resp.status_code != 200:
            print ('Post fail to alarms {}: {}'.  format(durl, resp.text))
            return False
        task_id = json.loads(resp.text).get('task_id')
        utils.poll_for_task_state(task_url, task_id)
    except Exception as e:
        print '... Exception in remove the alarm rule {}'.format(e)
        return False
    print '... Successfully deleted alarm'
    return True

### ADD Custom Nofitication ###
def create_custom_notify():
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    data = {
  	"NotificationEndpoint": "http://192.168.250.4:9999",
  	"NotificationSystemType": "Custom_Notifier",
  	"ServiceKey": "webhook-service",
  	"Verify": "False",
  	"ServiceName": "webhook-service"
	}
    try:
        resp = requests.post(url=notification_url, headers=HEADERS, data=json.dumps(data), verify=False)
	if resp.status_code != 200:
		rjson = resp.json()
               	if ('already exists' in  rjson['message']):
               		print 'Alarm exists in AppFormix'
              		return True
		print ('Post fail to add Notification Service {}: {}'.  format(notification_url, resp.text))
		return False
	time.sleep(3)
	print "... Successfully added Custom Notification Service"
	return 'webhook-service'
    except Exception as e:
        print '... Exception in Adding custom notification service {}'.format(e)
        return False	


def get_custom_notify():
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    try:
	url = notification_url + '/webhook-service'
        resp = requests.get(url=url, headers=HEADERS,verify=False)
	#print resp.status_code
	if resp.status_code == 404:
		create_custom_notify()

	### Custom Service exists ###
        elif resp.status_code == 200:
		rjson = resp.json()
		#print rjson
		if rjson['ServiceKeyUser']['ServiceKey'] == 'webhook-service':
			return 'webhook-service'
    except Exception as e:
        print 'Exception in Getting custom notification service {}'.format(e)
        return False
      
def link_alarm_and_notification(event_rule_id):
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    data = { 
  	"EventRuleId": event_rule_id,
  	"ServiceKey": 'webhook-service'
	}
    url = alarm_notification_url
    resp = requests.post(url=url, headers=HEADERS, data=json.dumps(data), verify=False)
    if resp.status_code != 200:
        #print data
	rjson = resp.json()
        if ('already exists' in  rjson['message']):
        	print 'Alarm exists in AppFormix'
                return True
        print ('Post fail to link Notification Service {}: {}'.  format(url, resp.text))
        return False
    print "... Added Notification service to alarm"
    return True

def unlink_alarm_and_notification(event_rule_id):
    HEADERS['X-Auth-Token'] = vnf_data.get_appformix_token()
    
    url = alarm_notification_url
    resp = requests.get(url=url, headers=HEADERS, verify=False)
    rjson = resp.json()

    links = rjson['ServiceKeyEventRuleProfile']
    link_id = ''
    for item in links:
    	if item['ServiceKeyEventRule']['EventRuleId'] == event_rule_id:
		link_id = item['ServiceKeyEventRule']['Id']
		continue

    delete_url = ''
    if link_id != '':
	delete_url = url + '/' + link_id
	resp = requests.get(url=delete_url, headers=HEADERS, verify=False)
    else:
	print "Id of notification_alarm is invalid: %s" %(link_id)

    if resp.status_code != 200:
        rjson = resp.json()
        print ('DELETE fail to unlink Notification Service {}: {}'.  format(delete_url, resp.text))
        return False
    
    print "... Removed link between Notification and alarm"
    return True
 


def add_alarm(device_name):
  notify_id = get_custom_notify()
  for e in vnf_data.EventRules:
    alarm_name = device_name + '_alarm'
    alarm_id = alarm_name.upper()

    e['EventRule']['Name'] = alarm_name
    e['EventRule']['NetworkDeviceId'] = device_name 
    e['EventRule']['EventRuleId'] = alarm_id
    json_data = json.dumps(e['EventRule'])
    s = post_alarm(json_data)

    #IF custom service already exists -> Add notification to alarm
    if notify_id == 'webhook-service':
	link_alarm_and_notification(alarm_id)
    else:
        link_alarm_and_notification(alarm_id)
	print "Couldn'd find notify_id: %s ... ignoring" %(notify_id)


def delete_alarm(device_name):
  for e in vnf_data.EventRules:
    alarm_name = device_name + '_alarm'

    e['EventRule']['Name'] = alarm_name
    e['EventRule']['NetworkDeviceId'] = device_name 
    e['EventRule']['EventRuleId'] = alarm_name.upper()
    json_data = json.dumps(e['EventRule'])
    unlink_alarm_and_notification(e['EventRule']['EventRuleId'])
    s = remove_alarm(e['EventRule']['EventRuleId'])
    

