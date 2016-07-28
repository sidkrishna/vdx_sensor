import requests
import xmltodict
from dicttoxml import dicttoxml
from distutils.util import strtobool
import ast

def setup_session(username, password):
    s = requests.Session()
    s.auth = (username, password)
    s.headers.update({"Accept": "application/vnd.configuration.resource+xml"})
    return s

def poll_device(base_url, session):
    interfaces = []

    def do_poll(payload={}, url="/vdx-1.xml", _has_more=True):
        try:
            _url = base_url + url
            _r = session.post(_url, data=payload, timeout=30)
        except requests.exceptions.RequestException as e:
            raise e

        content = xmltodict.parse(_r.content)

        if 'interface' in content['output']:
            interfaces.extend(content['output']['interface'])

        _has_more = strtobool(content['output']['has-more'])
        if _has_more:
            last_interface = content['output']['interface'][-1]
            payload = {
                'get-interface-detail': {
                    'last-rcvd-interface': {
                        'interface-type': last_interface['interface-type'],
                        'interface-name': last_interface['interface-name']
                    }
                }
            }
            do_poll(dicttoxml(payload), "/vdx-2.xml", False)

    do_poll()
    return interfaces

output = poll_device('http://localhost:8888', setup_session('admin', 'password'))

for interface in output:
    if 'hardware-type' in interface:
        if interface['if-state'] == 'up' and interface['line-protocol-state'] == 'up':
            print interface
