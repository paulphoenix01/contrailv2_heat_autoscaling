export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
export OS_PROJECT_NAME=admin
export OS_TENANT_NAME=admin
export OS_USERNAME=admin
export OS_PASSWORD=contrail123
export OS_AUTH_URL=http://192.168.250.1:35357/v3
export OS_INTERFACE=internal
export OS_IDENTITY_API_VERSION=3
export OS_BAREMETAL_API_VERSION=1.29
heat stack-update stack1 --template-file service_instance_scaling.yaml --environment service_instance_scaling.env
sleep 10
python fix_pt.py
sleep 30
python fix_pt.py
