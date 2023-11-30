from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import loads
import json
import os

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("flightreservation.events")
transaction_logger = ds_logging.get_transaction_logger("flightreservation")

# --- flight data ---
event_logger.info("Loading flight data")
flights_data_file = "flightNodeData/flights_data_primary.json"

if os.path.exists(flights_data_file):
    event_logger.info("Flight data file exists")
    with open(flights_data_file, "r") as file:
        flights_data = json.load(file)
else:
    event_logger.info("Flight data file does not exist")
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
# --- end flight data ---

# --- hotel data ---
event_logger.info("Loading hotel data")
hotel_data_file = "flightNodeData/hotel_data_secondary.json"

if os.path.exists(hotel_data_file):
    event_logger.info("Hotel data file exists")
    with open(hotel_data_file, "r") as file:
        hotel_data = json.load(file)
else:
    event_logger.info("Hotel data file does not exist")
    hotel_data = {
        "Hotel 1": {"reserved_weeks": [], "free_weeks": list(range(1, 53))},
        "Hotel 2": {"reserved_weeks": [], "free_weeks": list(range(1, 53))},
        "Hotel 3": {"reserved_weeks": [], "free_weeks": list(range(1, 53))},
    }

event_logger.info("Hotel data loaded")

def save_hotel_data():
    with open(hotel_data_file, "w") as file:
        json.dump(hotel_data, file)
# --- end hotel data ---

def handle_request(hotel_request, departure_request, return_request, request_id):

    event_logger.info("hotel request data:")
    event_logger.info(hotel_request)

    event_logger.info("flight request data:")
    event_logger.info(departure_request)
    event_logger.info(return_request)

    hotel_name = hotel_request.get('name', '')
    week_number = hotel_request.get('week', '')

    event_logger.info("hotel name: %s" %(hotel_name))
    event_logger.info("week number: %s" %(week_number))

    hotel_reservation_OK, hotel_status_msg = book_hotel(hotel_name, week_number)
    event_logger.info("hotel reservation status: %s" %(hotel_status_msg))
    flight_reservation_OK, flight_status_msg = book_flights(departure_request, return_request)
    event_logger.info("flight reservation status: %s" %(flight_status_msg))
    reservation_OK = hotel_reservation_OK and flight_reservation_OK
    status_msg = hotel_status_msg + " & " + flight_status_msg
    event_logger.info("reservation status: %s" %(status_msg))

    transaction_logger.info("id=%s, status=%s" %(request_id, reservation_OK))

    return reservation_OK


def book_hotel(hotel_name, week_number):

    hotel_reservation_OK = False
    status_msg = ''

    if hotel_name in hotel_data:
        week_number = int(week_number)
        if week_number in hotel_data[hotel_name]["free_weeks"]:
            hotel_data[hotel_name]["free_weeks"].remove(week_number)
            hotel_data[hotel_name]["reserved_weeks"].append(week_number)
            hotel_reservation_OK = True
            status_msg = "Success"
            save_hotel_data()
        else:
            status_msg = "Hotel is already booked for this week"
            hotel_reservation_OK = False
    else:
        status_msg = "Hotel does not exist"
        hotel_reservation_OK = False
    
    return hotel_reservation_OK, status_msg

def book_flights(departure_request, return_request):
    event_logger.info('departure request:')
    event_logger.info(departure_request)
    event_logger.info('return request:')
    event_logger.info(return_request)

    flights_reservation_OK = False
    status_msg = ''

    departure_flight_number = departure_request.get('flight_number', '')
    return_flight_number = return_request.get('flight_number', '')
    event_logger.info("departure flight number: %s" %(departure_flight_number))
    event_logger.info("return flight number: %s" %(return_flight_number))

    if any(flight["flight_number"] == departure_flight_number for flight in flights_data["flights"]) and any(flight["flight_number"] == return_flight_number for flight in flights_data["flights"]):
        departure_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
        return_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)

        if int(departure_flight["reserved_seats"]) < int(departure_flight["total_seats"]):
            departure_flight["reserved_seats"] += 1
            save_flight_data()
        else:
            status_msg = "Failure: departure flight is fully booked"
            flights_reservation_OK = False
            return flights_reservation_OK

        if return_flight["reserved_seats"] < return_flight["total_seats"]:
            return_flight["reserved_seats"] += 1
            save_flight_data()
        else:
            status_msg = "Failure: return flight is fully booked"
            flights_reservation_OK = False
            return flights_reservation_OK

        flights_reservation_OK = True
        status_msg = "Success" if flights_reservation_OK else "Failure"
        return flights_reservation_OK, status_msg
    
    else:
        status_msg = "Failure: flight does not exist"
        flights_reservation_OK = False
        return flights_reservation_OK, status_msg
    
# start server
validator_server = SimpleXMLRPCServer(('localhost', 8001), logRequests=True)

validator_server.register_function(handle_request, 'handle_request')

event_logger.info("Flights server is ready to accept requests.")
validator_server.serve_forever()