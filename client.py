from xmlrpc.client import ServerProxy
from xmlrpc.client import dumps

import utils.ds_logging as ds_logging

request_data_placeholder = {
    'id': 123,
    'departure_flight': {
        'date': '2023-11-15',
        'time': '10.00',
        'company': 'Airline A'
    },
    'returning_flight': {
        'date': '2023-11-20',
        'time': '14.30',
        'flight_number': 'AB1234',
        'company': 'Airline B'
    },
    'hotel': {
        'from_date': '2023-11-15',
        'to_date': '2023-11-20',
        'name': 'Example Hotel',
        'address': 'Example Street, Paradise City'
    }
}

xml_request = dumps((request_data_placeholder,), methodname='booking_request')

def send_request():
    logger = ds_logging.get_event_logger("client")
    coordinator_server = ServerProxy('http://localhost:8000')

    result = coordinator_server.send_booking_request(xml_request)
    msg = f"Result from coordinator server: {result}"

    logger.info(msg)


send_request()