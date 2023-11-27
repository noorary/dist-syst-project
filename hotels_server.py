from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import loads
import json
import os

import xml.etree.ElementTree as ET

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("hotelreservation.events")
transaction_logger = ds_logging.get_transaction_logger("hotelreservation")

hotel_data_file = "hotel_data.json"

if os.path.exists(hotel_data_file):
    with open(hotel_data_file, "r") as file:
        hotel_data = json.load(file)
else:
    hotel_data = {
        "Hotel 1": {"reserved_weeks": [], "free_weeks": list(range(1, 53))},
        "Hotel 2": {"reserved_weeks": [], "free_weeks": list(range(1, 53))},
        "Hotel 3": {"reserved_weeks": [], "free_weeks": list(range(1, 53))},
    }

def save_hotel_data():
    with open(hotel_data_file, "w") as file:
        json.dump(hotel_data, file)  

def book_hotel(hotel_request, request_id):

    hotel_name = hotel_request.get('name', '')
    week_number = hotel_request.get('week', '')

    event_logger.info("hotel request data:")
    event_logger.info(hotel_request)

    reservation_OK = False
    status_msg = ''

    if hotel_name in hotel_data:
        week_number = int(week_number)
        if week_number in hotel_data[hotel_name]["free_weeks"]:
            hotel_data[hotel_name]["free_weeks"].remove(week_number)
            hotel_data[hotel_name]["reserved_weeks"].append(week_number)
            reservation_OK = True
            status_msg = "Success"
            save_hotel_data()
        else:
            status_msg = "Failure: hotel is already booked for this week"
            reservation_OK = False
    else:
        status_msg = "Failure: hotel does not exist"
        reservation_OK = False

    transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
    return reservation_OK

def parse_xml_request(xml_request, element_name):

    root = ET.fromstring(xml_request)
    element = root.find(f".//member[name='{element_name}']/value/struct")

    element_details = {}
    for member in element.findall('member'):
        name = member.find('name').text
        value = member.find('value')
        if value.text is None: 
            for child in value:
                value = child.text
                break
        else:
            value = value.text
        element_details[name] = value

    event_logger.info(element_details)
    return element_details

validator_server = SimpleXMLRPCServer(('localhost', 8002), logRequests=True)

validator_server.register_function(book_hotel, 'book_hotel')

event_logger.info("Hotel server is ready to accept requests.")
validator_server.serve_forever()