#!/usr/bin/env python

import yaml

with open('/opt/stackstorm/packs/vdx_sensor/config.yaml', 'r') as f:
     config = yaml.load(f)
     active = 0
     active = int(config['sensor_bandwidth']['active_passive'])
     if active:
         print "active"
     else:
         print "passive"
         
          

