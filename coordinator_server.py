from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
from xmlrpc.client import loads
import random

import xml.etree.ElementTree as ET

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("coordinator.events")
transaction_logger = ds_logging.get_transaction_logger("coordinator")

def get_request_id(xml_request):
    root = ET.fromstring(xml_request)
    value = root.find(f".//member[name='id']/value")
    return value[0].text


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

def send_booking_request(xml_request):
    
    event_logger.info('coordinator starting')

    request_data, method = loads(xml_request)

    event_logger.info('parsing request data')

    request_id = get_request_id(xml_request)
    transaction_logger.info("id=%s, status=Received" %(request_id))
    departure_flight = parse_xml_request(xml_request, 'departure_flight')
    returning_flight = parse_xml_request(xml_request, 'returning_flight')
    hotel = parse_xml_request(xml_request, 'hotel')

    event_logger.info('parsing done, sending request to server')

    flights_server = ServerProxy('http://localhost:8001')
    hotels_server = ServerProxy('http://localhost:8002')

    # choose used server randomly to mock load balancing between servers for demo purposes
    servers = [flights_server, hotels_server]
    chosen_server = random.choice(servers)
    event_logger.info('chosen server: %s'%(chosen_server))
    result = chosen_server.handle_request(hotel, departure_flight, returning_flight, request_id)

    event_logger.info('event=request, response=%s'%(result))

    reservation_OK = result

    status_msg = "Success" if reservation_OK else "Failure"
    transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
    return status_msg
    
coordinator_server = SimpleXMLRPCServer(('localhost', 8000), logRequests=True)

coordinator_server.register_function(send_booking_request, 'send_booking_request')

event_logger.info("Coordinator server is ready to accept requests.")
coordinator_server.serve_forever()