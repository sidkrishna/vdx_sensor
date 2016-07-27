# ST2 VDX Sensor Integration Pack

Pack containing VDX Sensors.

## Manual Installation

Please install manually the first time. Reason being `setup_virtualenv` doesn't work remotely for some reason. Need to investigate.

```
cp -R ./vdx_sensor /opt/stackstorm/packs
st2 run packs.setup_virtualenv packs=vdx_sensor
st2 run packs.load register=all
st2 run packs.restart_component servicename=st2sensorcontainer
```

## Configuration

* ``username`` - VDX Username.
* ``password`` - VDX Password.
* ``base_url`` - VDX Base URL, typically `http://<VDX_IP_ADDRESS>/rest`.

## Sensors

### VDXInterfaceSensor

This sensor uses the VDX REST API to monitor various interface metrics.

## Testing

There is a test_vdx directory where if you run `python server.py` it will serve static files that are canned responses typically sent by the VDX. This is for testing only and relies on changing code within the sensor.   
