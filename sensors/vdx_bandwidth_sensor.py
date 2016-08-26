from vdx_base_sensor import VDXBaseSensor
import xmltodict
from distutils.util import strtobool
from dicttoxml import dicttoxml
import ast
import pickle
import yaml

__all__ = [
    'VDXBandwidthSensor'
]

class VDXBandwidthSensor(VDXBaseSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        poll_interval = config['sensor_bandwidth'].get('poll_interval', 30)
        super(VDXBandwidthSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._logger = self._sensor_service.get_logger(__name__)

    def poll(self):
        
        with open('/opt/stackstorm/packs/vdx_sensor/config.yaml', 'r') as f:
            config = yaml.load(f)
            active = 0
            active = int(config['sensor_bandwidth']['active_passive'])
            f.close()
        
        self._logger.info("############# Bandwidth Sensor active: %d ################" %(active))  
        
        if active == 0:
            self._logger.info("############# RETURNING SINCE SENSOR IS PASSIVE ################")
            return

        self._logger.info("############# Bandwidth Sensor Polling ################")

        data = self._poll_device()

	interfaces = {}
        for interface in data:
            if 'hardware-type' in interface:
                if interface['if-state'] == 'up' and interface['line-protocol-state'] == 'up':
                    interfaces[interface['interface-name']] = \
                    {
                     'tx_octets': interface['ifHCOutOctets'],
                     'rx_octets': interface['ifHCInOctets']
                    }
        

        prev_bw_metrics = self._get_metrics()
        if prev_bw_metrics is None:
            self._logger.info("############ prev_bw_metrics is None #################")
            prev_bw_metrics = {}

        bw_metrics = {}

        for interface_name, interface_stats in interfaces.iteritems():
            interface_exists_in_prev = 0

            if interface_name in prev_bw_metrics:
                interface_exists_in_prev = 1

            latest_tx_max_mbps = 0
            latest_rx_max_mbps = 0

            if interface_exists_in_prev:
                latest_tx_mbps = (float(float(int(interface_stats['tx_octets']) - int(prev_bw_metrics[interface_name]['tx_last_octets']))/self._poll_interval)/(1000**2))*8
                if latest_tx_mbps > float(prev_bw_metrics[interface_name]['tx_max_mbps']):
                    latest_tx_max_mbps = latest_tx_mbps
                else:
                    latest_tx_max_mbps = prev_bw_metrics[interface_name]['tx_max_mbps']
                
                latest_rx_mbps = (float(float(int(interface_stats['rx_octets']) - int(prev_bw_metrics[interface_name]['rx_last_octets']))/self._poll_interval)/(1000**2))*8
                if latest_rx_mbps > prev_bw_metrics[interface_name]['rx_max_mbps']:
                    latest_rx_max_mbps = latest_rx_mbps
                else:
                    latest_rx_max_mbps = prev_bw_metrics[interface_name]['rx_max_mbps'] 

            bw_metrics[interface_name] = {}
            bw_metrics[interface_name]['tx_last_octets'] = interface_stats['tx_octets']
            bw_metrics[interface_name]['tx_max_mbps'] = latest_tx_max_mbps 
            bw_metrics[interface_name]['rx_last_octets'] = interface_stats['rx_octets']
            bw_metrics[interface_name]['rx_max_mbps'] = latest_rx_max_mbps

            self._logger.info("############## Interface: %s" %(interface_name))
            self._logger.info("############## tx_last_octets: %d" %(int(bw_metrics[interface_name]['tx_last_octets'])))
            self._logger.info("############## tx_max_mbps: %f" %(float(bw_metrics[interface_name]['tx_max_mbps'])))
            self._logger.info("############## rx_last_octets: %d" %(int(bw_metrics[interface_name]['rx_last_octets'])))
            self._logger.info("############## rx_max_mbps: %f" %(float(bw_metrics[interface_name]['rx_max_mbps'])))

        self._set_metrics(bw_metrics)
        with open('/opt/stackstorm/packs/vdx_sensor/max_bw_db.txt', 'wb') as f:
            pickle.dump(bw_metrics, f)
            f.close()

    def _set_metrics(self, metrics):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='metrics', value=metrics)

    def _get_metrics(self):
        if hasattr(self._sensor_service, 'get_value'):
            metrics = self._sensor_service.get_value(name='metrics')
            if metrics:
                return ast.literal_eval(metrics)
