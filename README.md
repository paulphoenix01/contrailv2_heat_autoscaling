## Auto-Scaling Heat Templates for ContrailV2 (Contrail v5.0)

Run on your config node
```
git clone https://github.com/paulphoenix01/contrailv2_heat_autoscaling
cd contrailv2_heat_autoscaling
source /etc/kolla/admin-openrc.sh
```

Edit the flavor/image name to fit your setup.
```
vim service_instance_scaling.env
  service_template_properties_image_name: 'vsrx-nonat'
  […]
  service_template_properties_flavor: 'small'
```

Create heat-stack
```
heat stack-create stack1 --template-file service_instance_scaling.yaml --environment service_instance_scaling.env
```

Wait 30seconds . . . "heat stack-list" should shows complete
```

[root@nugget-cfg contrailv2_heat_autoscaling]# openstack stack list
+--------------------------------------+------------+----------------------------------+-----------------+----------------------+--------------+
| ID                                   | Stack Name | Project                          | Stack Status    | Creation Time        | Updated Time |
+--------------------------------------+------------+----------------------------------+-----------------+----------------------+--------------+
| 5cd265fb-5b80-4fde-9dfb-2a49f7592200 | stack1     | 9d2b3dcb77ea48428844556c75302f95 | CREATE_COMPLETE | 2018-07-23T06:25:07Z | None         |
+--------------------------------------+------------+----------------------------------+-----------------+----------------------+--------------+
```

To scale-out/in you can edit 'service_instance_number' and run heat-update
```
#vim service_instance_scaling.yaml
## Edit service_instance_number

heat stack-update stack1 --template-file service_instance_scaling.yaml --environment service_instance_scaling.env
```

