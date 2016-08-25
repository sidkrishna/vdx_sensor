#!/usr/bin/env python

import yaml
import sys
import os

os.system("st2 key delete vdx_sensor.VDXBandwidthSensor:metrics")

with open('/opt/stackstorm/packs/vdx_sensor/config.yaml', 'r') as f:
     config = yaml.load(f)
     active = 0
     value = int(sys.argv[1])
     if value:
         active = 1;
     if active:
        config['sensor_bandwidth']['active_passive'] = 1
     else:
        config['sensor_bandwidth']['active_passive'] = 0
     f.close()
        
with open('/opt/stackstorm/packs/vdx_sensor/config.yaml', 'w') as f:
     yaml.dump(config,f, default_flow_style=False)
     f.close()
 
          

