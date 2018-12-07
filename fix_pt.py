import requests
from pprint import pprint
from random import randint

#Get Auth Token
data = {"auth":{"passwordCredentials":{"username": "admin", "password": "contrail123"},"tenantName": "admin"}}
req = requests.post('http://192.168.250.1:5000/v2.0/tokens',json=data,headers={'Content-type': 'application/json'}).json()
token  = req['access']['token']['id']

req = requests.get('http://192.168.250.1:8082/port-tuples', headers={'X-Auth-Token': token}).json()
all_pt = req['port-tuples']



def reapply_port_tuple(pt_uuid, pt_href):
        ref_update_url = 'http://192.168.250.1:8082/ref-update'
        req = requests.get(pt_href, headers={'X-Auth-Token': token}).json()
        pt_fq_name = req['port-tuple']['fq_name']
        ### /ref-update body: ref-type = port-tuple = pt-uuid, type = vmi = vmi-uuid
        req_body_list = []

        #pprint(req)
        ### If none vmi_refs, delete port_tuple
        if 'virtual_machine_interface_back_refs' not in req['port-tuple']:
                req = requests.delete(pt_href, headers={'X-Auth-Token': token})
                print "\t ... Deleted invalid port-tuple"
                return
        ### Get vmi_uuid from refs
        vmi_refs = req['port-tuple']['virtual_machine_interface_back_refs']
        for ref in vmi_refs:
                req_body = {'ref-type': 'port-tuple', 'ref-uuid': pt_uuid, 'operation': 'DELETE', 'type': 'virtual-machine-interface', 'uuid': '' }
                req_body['uuid'] = ref['uuid']
                #print req_body
                req_body_list.append(req_body)

        ### Delete all refs to this port tuple
        for req_body in req_body_list:
                req = requests.post(ref_update_url, headers={'X-Auth-Token': token, 'Content-type': 'application/json'}, json=req_body)
                #print "\t ... Deleted Port-tuple VMIs ref: %s" % (req_body['uuid'])

        ### Delete Port-Tuple
        req = requests.delete(pt_href, headers={'X-Auth-Token': token})
        print "\t >>> Deleted Port-tuple"

        ### Create new port-tuple
        pt_fq_name[-1] = 'port-tuple' + str(randint(0, 1000))
        req_body = {'port-tuple': {'parent_type': 'service-instance', 'fq_name': pt_fq_name} }
        req = {}
        try:
                req = requests.post('http://192.168.250.1:8082/port-tuples', headers={'X-Auth-Token': token, 'Content-type': 'application/json'}, json=req_body)
                req = req.json()
        except:
                print "Exception during creating new port-tuple...."
                print req.status_code
                print req.text
                return

        new_pt_uuid = req['port-tuple']['uuid']
        print "\t >>> Created new Port-Tuple"

        ### Add same refs back
        for req_body in req_body_list:
                req_body['operation'] = 'ADD'
                req_body['ref-uuid'] = new_pt_uuid
                req = requests.post(ref_update_url, headers={'X-Auth-Token': token, 'Content-type': 'application/json'}, json=req_body)
                #print "\t ... Added Port-tuple VMIs ref: %s" % (req_body['uuid'])


for pt in all_pt:
        ### Re-apply port-tuple port reference (management, left, right)
        print "Reconfiguring port-tuple: %s  ..." % (pt['uuid'])
        reapply_port_tuple(pt['uuid'], pt['href'])
        print "\t ... Done"



