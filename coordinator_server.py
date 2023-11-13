from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
from xmlrpc.client import loads

import xml.etree.ElementTree as ET

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

    print(element_details)

    return element_details

def send_booking_request(xml_request):
    print('coordinator starting')

    request_data, method = loads(xml_request)

    print('parsing request data')

    departure_flight = parse_xml_request(xml_request, 'departure_flight')
    returning_flight = parse_xml_request(xml_request, 'returning_flight')
    hotel = parse_xml_request(xml_request, 'hotel')

    print('parsing done, sending requests to servers')

    flights_server = ServerProxy('http://localhost:8001')
    hotels_server = ServerProxy('http://localhost:8002')

    flights_result = flights_server.book_flights(departure_flight, returning_flight)
    print('request to flight ok')
    hotels_result = hotels_server.book_hotel(hotel)
    print('request to hotel ok')

    if flights_result and hotels_result:
        return "Success"
    else:
        return "Failure"

coordinator_server = SimpleXMLRPCServer(('localhost', 8000), logRequests=True)

coordinator_server.register_function(send_booking_request, 'send_booking_request')

print("Coordinator server is ready to accept requests.")
coordinator_server.serve_forever()