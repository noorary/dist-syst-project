from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import loads

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("hotelreservation.events")
transaction_logger = ds_logging.get_transaction_logger("hotelreservation")

def book_hotel(xml_hotel_request):

    event_logger.info("hotel request data:")
    event_logger.info(xml_hotel_request)

    request_id = "FIX ME"
    reservation_OK = False
    status_msg = "Success" if reservation_OK else "Failure"
    transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
    return reservation_OK

validator_server = SimpleXMLRPCServer(('localhost', 8002), logRequests=True)

validator_server.register_function(book_hotel, 'book_hotel')

event_logger.info("Hotel server is ready to accept requests.")
validator_server.serve_forever()