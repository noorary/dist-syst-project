from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import loads
import json
import os

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("flightreservation.events")
transaction_logger = ds_logging.get_transaction_logger("flightreservation")

flights_data_file = "flights_data.json"

if os.path.exists(flights_data_file):
    with open(flights_data_file, "r") as file:
        flights_data = json.load(file)
else:
    flights_data = {
        "flights": [
            {
                "flight_number": "ABC123",
                "company": "Airline A",
                "date": "2023-12-01",
                "total_seats": 100,
                "reserved_seats": 20
            },
            {
                "flight_number": "XYZ789",
                "company": "Airline B",
                "date": "2023-12-05",
                "total_seats": 120,
                "reserved_seats": 15
            },
            {
                "flight_number": "123XYZ",
                "company": "Airline C",
                "date": "2023-12-10",
                "total_seats": 80,
                "reserved_seats": 5
            }
        ]
    }

def save_flight_data():
    with open(flights_data_file, "w") as file:
        json.dump(flights_data, file)


def book_flights(departure_request, return_request, request_id):

    event_logger.info("flight request data:")
    event_logger.info(departure_request)
    event_logger.info(return_request)

    reservation_OK = False
    status_msg = ''

    departure_flight_number = departure_request.get('flight_number', '')
    return_flight_number = return_request.get('flight_number', '')

    if any(flight["flight_number"] == departure_flight_number for flight in flights_data["flights"]) and any(flight["flight_number"] == return_flight_number for flight in flights_data["flights"]):
        departure_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
        return_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)

        if int(departure_flight["reserved_seats"]) < int(departure_flight["total_seats"]):
            departure_flight["reserved_seats"] += 1
            save_flight_data()
        else:
            status_msg = "Failure: departure flight is fully booked"
            reservation_OK = False
            transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
            return reservation_OK

        if return_flight["reserved_seats"] < return_flight["total_seats"]:
            return_flight["reserved_seats"] += 1
            save_flight_data()
        else:
            status_msg = "Failure: return flight is fully booked"
            reservation_OK = False
            transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
            return reservation_OK

        reservation_OK = True
        status_msg = "Success" if reservation_OK else "Failure"
        transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
        return reservation_OK
    
    else:
        status_msg = "Failure: flight does not exist"
        reservation_OK = False
        transaction_logger.info("id=%s, status=%s" %(request_id, status_msg))
        return reservation_OK

validator_server = SimpleXMLRPCServer(('localhost', 8001), logRequests=True)

validator_server.register_function(book_flights, 'book_flights')

event_logger.info("Flights server is ready to accept requests.")
validator_server.serve_forever()