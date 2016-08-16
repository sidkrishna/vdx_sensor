from vdx_base_sensor import VDXBaseSensor
import xmltodict
from distutils.util import strtobool
from dicttoxml import dicttoxml
import ast

__all__ = [
    'VDXMacSensor'
]

class VDXMacSensor(VDXBaseSensor):
    def __init__(self, sensor_service, config=None, poll_interval=None):
        poll_interval = config['sensor_mac'].get('poll_interval', 30)
        super(VDXMacSensor, self).__init__(sensor_service=sensor_service,
                                                  config=config,
                                                  poll_interval=poll_interval)
        self._new_mac_trigger_ref = 'vdx_sensor.matched_new_mac'
        self._mac_move_trigger_ref = 'vdx_sensor.matched_mac_move'
        self._logger = self._sensor_service.get_logger(__name__)

    def poll(self):
        self._logger.info("MAC Sensor Polling")
        mac_addresses = self._poll_device()
        prev_mac_addresses = self._get_mac_addresses()
        self._set_mac_addresses(mac_addresses)
        if prev_mac_addresses is not None:
            self._do_delta(prev_mac_addresses, mac_addresses)

    def _poll_device(self):
        mac_addresses = {}

        def _do_poll(parent, payload={}):
            _url = self._connection.get_operational_url('get-mac-address-table')
            _r = self._connection.perform_post(_url, payload)

            content = xmltodict.parse(_r.content)

            if 'mac-address-table' in content['output']:
                for mac_entry in content['output']['mac-address-table']:
                    mac_addresses[mac_entry['mac-address']] = {
                        'vlan_id': mac_entry['vlanid'],
                        'mac_type': mac_entry['mac-type'],
                        'mac_state': mac_entry['mac-state'],
                        'forwarding_interface': {
                            'interface_type': mac_entry['forwarding-interface']['interface-type'],
                            'interface_name': mac_entry['forwarding-interface']['interface-name']
                        }
                    }
            _has_more = strtobool(content['output']['has-more'])
            if _has_more:
                last_interface = content['output']['mac-address-table'][-1]
                payload = {
                    'get-interface-detail': {
                        'last-rcvd-interface': {
                            'interface-type': last_interface['forwarding-interface']['interface-type'],
                            'interface-name': last_interface['forwarding-interface']['interface-name']
                        }
                    }
                }
                _do_poll(parent, dicttoxml(payload, root=False, attr_type=False))

        _do_poll(self)
        return mac_addresses


    def _set_mac_addresses(self, mac_addresses):
        if hasattr(self._sensor_service, 'set_value'):
            self._sensor_service.set_value(name='vdx_mac_sensor', value=mac_addresses)

    def _get_mac_addresses(self):
        if hasattr(self._sensor_service, 'get_value'):
            mac_addresses = self._sensor_service.get_value(name='vdx_mac_sensor')
            if mac_addresses:
                return ast.literal_eval(mac_addresses)

    def _do_delta(self, prev_mac_addresses, mac_addresses):
        self._logger.debug("Previous MAC Addresses are: %s" %(prev_mac_addresses))
        self._logger.debug("Current MAC Addresses are: %s" %(mac_addresses))
        for mac_address, mac_info in mac_addresses.iteritems():
            if mac_address in prev_mac_addresses:
                if mac_info['forwarding_interface']['interface_name'] != prev_mac_addresses[mac_address]['forwarding_interface']['interface_name']:
                    self._dispatch_new_mac_trigger(mac_address, mac_info, prev_mac_addresses[mac_address])
            else:
                self._dispatch_new_mac_trigger(mac_address, mac_info)

    def _dispatch_new_mac_trigger(self, mac_address, mac_info):
        trigger = self._new_mac_trigger_ref
        payload = {
            'mac_address': mac_address,
            'mac_type': mac_info['mac_type'],
            'vlan_id': mac_info['vlan_id'],
            'forwarding_interface_type': mac_info['forwarding_interface']['interface_type'],
            'forwarding_interface_name': mac_info['forwarding_interface']['interface_name'],
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)

    def _dispatch_mac_move_trigger(self, mac_address, mac_info, prev_mac_info):
        trigger = self._mac_move_trigger_ref
        payload = {
            'mac_address': mac_address,
            'mac_type': mac_info['mac_type'],
            'vlan_id': mac_info['vlan_id'],
            'old_forwarding_interface_type': prev_mac_info['forwarding_interface']['interface_type'],
            'old_forwarding_interface_name': prev_mac_info['forwarding_interface']['interface_name'],
            'new_forwarding_interface_type': mac_info['forwarding_interface']['interface_type'],
            'new_forwarding_interface_name': mac_info['forwarding_interface']['interface_name'],
        }
        self._sensor_service.dispatch(trigger=trigger, payload=payload)
