source admin-rc.sh
heat stack-update stack1 --template-file service_instance_scaling.yaml --environment service_instance_scaling.env
