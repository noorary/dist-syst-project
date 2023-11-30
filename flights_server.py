from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import loads

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("flightreservation.events")
transaction_logger = ds_logging.get_transaction_logger("flightreservation")

def book_flights(request_id, departure_request, return_request):


    event_logger.info("flight request data:")
    event_logger.info(departure_request)
    event_logger.info(return_request)

    reservation_OK = False
    status_msg = "Success" if reservation_OK else "Failure"
    transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
    return reservation_OK

validator_server = SimpleXMLRPCServer(('localhost', 8001), logRequests=True)

validator_server.register_function(book_flights, 'book_flights')

event_logger.info("Flights server is ready to accept requests.")
validator_server.serve_forever()