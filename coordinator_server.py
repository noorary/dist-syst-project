from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
from xmlrpc.client import loads
import random
import argparse
import time
import socket

import xml.etree.ElementTree as ET

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("coordinator.events")
transaction_logger = ds_logging.get_transaction_logger("coordinator")

def get_request_id(xml_request):
    root = ET.fromstring(xml_request)
    value = root.find(f".//member[name='id']/value")
    return value[0].text

def send_prepare_to_participant(participant, request_id):
    return participant.prepare_commit(request_id)

def send_commit_to_participant(participant, request_id):
    return participant.commit(request_id)

def send_abort_to_participant(participant, request_id):
    return participant.abort(request_id)


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

    # STEP 1: coordinator node parses the request and sends it to randomly selected participant node
    # let's assume that hotels node got selected

    # choose used server randomly to mock load balancing between servers for demo purposes
    servers = [flights_server, hotels_server]
    # chosen_server = random.choice(servers)

    chosen_server = hotels_server
    event_logger.info('chosen server: %s'%(chosen_server))
    result = chosen_server.handle_request(hotel, departure_flight, returning_flight, request_id)
    event_logger.info('event=request, response=%s'%(result))

    #timer for waiting response
    # start_time = time.time()
    # while True:
    #     result = chosen_server.handle_request(hotel, departure_flight, returning_flight, request_id)
    #     event_logger.info('event=request, response=%s'%(result))

    #     #if return is false or time out, stop waiting and continue
    #     time_now = time.time()
    #     if not result or time_now - start_time >= 90:
    #         #Try another server
    #         for node in servers:
    #             if node != chosen_server:
    #                 start_time2 = time.time()
    #                 while True:
    #                     result2 = node.handle_request(hotel, departure_flight, returning_flight, request_id)
    #                     event_logger.info('event=request, response=%s'%(result))
    #                     time_now2 = time.time()
    #                     if not result2 or time_now2 - start_time2 >= 90:
    #                         status_msg = "Failure"
    #                         return False
    #                     else:
    #                         status_msg = "Success"
    #                         break
    #     #if response returned true, break out of the loop and continue
    #     else:
    #         status_msg = "Success"
    #         break

    reservation_OK = result
    status_msg = "Success" if reservation_OK else "Failure"
    transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
    return status_msg


def parse_arguments():
    parser = argparse.ArgumentParser(description="Coordinator server for The Booking System")

    parser.add_argument("-H", "--host", type=str, default="localhost", help="Host name (default: localhost)")
    parser.add_argument("-P", "--port", type=int, default=8000, help="Port number (default: 8000)")
    return parser.parse_args()

def discover_nodes():
    UDP_IP = "255.255.255.255"
    UDP_PORT = 12345
    event_logger.info("Reservation node discovery started")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", UDP_PORT))
    server_socket.settimeout(5)
    hosts = {}
    while len(hosts) < 2:
        try:
            data, addr = server_socket.recvfrom(1024)
            event_logger.info(f"Received message from {addr}: {data.decode()}")
            hosts[addr] = data.decode()
            if  len(hosts) < 2:
                acknowledgment_message = "Keep waiting for another node"
            else:
                node_messages = ";".join(hosts.values())
                acknowledgment_message = "OK: " + node_messages
                for ip in hosts.keys():
                    server_socket.sendto(acknowledgment_message.encode(), ip)
        except socket.timeout:
            pass



def main():
    args = parse_arguments()
    host = args.host
    port = args.port

    discover_nodes()

    coordinator_server = SimpleXMLRPCServer((host, port), logRequests=True)

    coordinator_server.register_function(send_booking_request, 'send_booking_request')

    event_logger.info("Starting server on host: %s, port: %s" %(host, port))
    event_logger.info("Coordinator server is ready to accept requests.")
    coordinator_server.serve_forever()

if __name__ == "__main__":
    main()
