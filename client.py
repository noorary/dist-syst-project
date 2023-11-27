from xmlrpc.client import ServerProxy
from xmlrpc.client import dumps

import utils.ds_logging as ds_logging

import random

def get_user_input():
    week = input("Enter hotel week: ")
    name = input("Enter hotel name: ")
    departure_flight_number = input("Enter departure flight number: ")
    returning_flight_number = input("Enter returning flight number: ")

    return {
        'week': week,
        'name': name,
        'departure_flight_number': departure_flight_number,
        'returning_flight_number': returning_flight_number,
    }

user_input = get_user_input()


def generate_random_id():
    return random.randint(100, 9999)


request_data = {
    'id': generate_random_id(),
    'hotel': {
        'week': user_input['week'],
        'name': user_input['name'],
    },
    'departure_flight': {
        'flight_number': user_input['departure_flight_number'],
    },
    'returning_flight': {
        'flight_number': user_input['returning_flight_number'],
    }
}

xml_request = dumps((request_data,), methodname='booking_request')

def send_request():
    logger = ds_logging.get_event_logger("client")
    coordinator_server = ServerProxy('http://localhost:8000')

    result = coordinator_server.send_booking_request(xml_request)
    msg = f"Result from coordinator server: {result}"

    logger.info(msg)


send_request()