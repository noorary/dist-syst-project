from xmlrpc.client import ServerProxy
from xmlrpc.client import dumps
import argparse

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

def generate_random_id():
    return random.randint(100, 9999)

def get_request_data(user_input):
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
    return request_data


def send_request(proxy_url, xml_request):
    logger = ds_logging.get_event_logger("client")
    logger.info("Starting server on URL: %s" %(proxy_url))
    coordinator_server = ServerProxy(proxy_url)

    result = coordinator_server.send_booking_request(xml_request)
    msg = f"Result from coordinator server: {result}"

    logger.info(msg)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Client script for the booking system")
    
    parser.add_argument("-H", "--host", type=str, default="localhost", help="Host name (default: localhost)")
    parser.add_argument("-P", "--port", type=int, default=8000, help="Port number (default: 8000)")
    return parser.parse_args()

def main():
    ## user input to request 
    user_input = get_user_input()
    request_data = get_request_data(user_input)
    xml_request = dumps((request_data,), methodname='booking_request')
    ## Which host to connect 
    args = parse_arguments()
    proxy_url = "http://%s:%i" %(args.host, args.port)
    send_request(proxy_url, xml_request)

if __name__ == "__main__":
    main()