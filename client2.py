import random
from xmlrpc.client import dumps
from xmlrpc.client import ServerProxy
import utils.ds_logging as ds_logging

# USED ONLY FOR DEV TESTING

request_data_placeholder = {
    'id': random.randint(100, 9999),
    'departure_flight': {
        'date': '2023-11-15',
        'time': '10.00',
        'flight_number': 'ABC123',
        'company': 'Airline A'
    },
    'returning_flight': {
        'date': '2023-11-20',
        'time': '14.30',
        'flight_number': '123XYZ',
        'company': 'Airline B'
    },
    'hotel': {
        'name': 'Hotel 3',
        'week': '30'
    }
}

xml_request = dumps((request_data_placeholder,), methodname='booking_request')

def send_request():
    coordinator_server = ServerProxy('http://localhost:8000')

    result = coordinator_server.send_booking_request(xml_request)

    print(f"Result from coordinator server: {result}")


send_request()

def send_request():
    logger = ds_logging.get_event_logger("client")