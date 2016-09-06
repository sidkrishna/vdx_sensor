from vdx_base_sensor import VDXBaseSensor
import xmltodict
from distutils.util import strtobool
from dicttoxml import dicttoxml
import ast
import pickle

__all__ = [
    'VDXUtilisationSensor'
]

class VDXUtilisationSensor(VDXBaseSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        poll_interval = config['sensor_bandwidth'].get('poll_interval', 30)
        super(VDXUtilisationSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._trigger_ref = 'vdx_sensor.matched_utilisation_threshold'
        self._logger = self._sensor_service.get_logger(__name__)
        self._polls = 0

    def poll(self):
        
        self._logger.info("############# Utilization Sensor Polling ################")
        try: 
            with open('/opt/stackstorm/packs/vdx_sensor/max_bw_db.txt', 'rb') as f:
                max_bw_db = pickle.load(f)
                f.close()
        except IOError:
            self._logger.info("############# COULD NOT OPEN MAX BW DB--- RETURNING!! ################")
            return
        


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
        

        prev_util_metrics = self._get_metrics()
        if prev_util_metrics is None:
            self._logger.info("############ prev_metrics is None #################")
            prev_util_metrics = {}

        util_metrics = {}

        for interface_name, interface_stats in interfaces.iteritems():
            interface_exists_in_prev = 0

            if interface_name in prev_util_metrics:
                interface_exists_in_prev = 1

            if interface_exists_in_prev:
                latest_tx_mbps = (float(float(int(interface_stats['tx_octets']) - int(prev_util_metrics[interface_name]['tx_last_octets']))/self._poll_interval)/(1000**2))*8
                latest_rx_mbps = (float(float(int(interface_stats['rx_octets']) - int(prev_util_metrics[interface_name]['rx_last_octets']))/self._poll_interval)/(1000**2))*8

                self._logger.info("############## UTIL Interface: %s" %(interface_name))
                self._logger.info("############## UTIL latest_tx_mbps: %f" %(latest_tx_mbps))
                self._logger.info("############## UTIL latest_rx_mbps: %f" %(latest_rx_mbps))
                
                if interface_name in max_bw_db:
                    tx_threshold = float((1 + (float(self._config['sensor_utilisation']['tx_threshold'])/100)))*(float(max_bw_db[interface_name]['tx_max_mbps'])) 
                    rx_threshold = float((1 + (float(self._config['sensor_utilisation']['rx_threshold'])/100)))*(float(max_bw_db[interface_name]['rx_max_mbps'])) 

                    self._logger.info("############## UTIL tx_threshold: %f" %(tx_threshold))
                    self._logger.info("############## UTIL rx_threshold: %f" %(rx_threshold))
                    
                    if latest_tx_mbps > tx_threshold \
                    or latest_rx_mbps > rx_threshold:
                        self._logger.info("############## UTIL DISPATCHING TRIGGER FOR Interface: %s" %(interface_name))
                        self._dispatch_trigger(interface_name,
                            latest_tx_mbps,
                            tx_threshold,
                            latest_rx_mbps,
                            rx_threshold)

            util_metrics[interface_name] = {}
            util_metrics[interface_name]['tx_last_octets'] = interface_stats['tx_octets']
            util_metrics[interface_name]['rx_last_octets'] = interface_stats['rx_octets']

        self._set_metrics(util_metrics)

    def _set_metrics(self, metrics):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='metrics', value=metrics)

    def _get_metrics(self):
        if hasattr(self._sensor_service, 'get_value'):
            metrics = self._sensor_service.get_value(name='metrics')
            if metrics:
                return ast.literal_eval(metrics)

    def _dispatch_trigger(self, interface_name, tx, tx_threshold, rx, rx_threshold):
        trigger = self._trigger_ref
        payload = {
            'interface_name': interface_name,
            'tx_mbps': round(tx,2),
            'tx_threshold': round(tx_threshold,2),
            'rx_mbps': round(rx,2),
            'rx_threshold': round(rx_threshold,2)
        }
        self._logger.info("############# INSIDE UTIL DISPATH TRIGGER FUCNTION ################")
        self._logger.info("############## trigger REF: %s" %(trigger)) 
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
