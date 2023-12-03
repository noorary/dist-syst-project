from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy, loads
import json
import os

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("hotelreservation.events")
transaction_logger = ds_logging.get_transaction_logger("hotelreservation")

# TODO add flight data to state array and logic for committing flights
# --- state array ---
state_array = [
    {"request_id": "0",
     "status": "placeholder",
     "hotel": {"name": "Hotel Name Placeholder", "week_number": "1"}}
]

def update_state_array(request_id, hotel_info, new_state, state_array):
    for item in state_array:
        if item['request_id'] == request_id:
            item['state'] = new_state
            item['hotel'] = hotel_info
            break
    else:
        state_array.append({"request_id": request_id, "state": new_state, "hotel": hotel_info})

def contains_hotel_week(state_array, hotel_name, week_number):
    for item in state_array:
        hotel_info = item.get('hotel')
        if hotel_info and hotel_info.get('name') == hotel_name and hotel_info.get('week') == week_number:
            return True
    return False

# --- hotel data ---
event_logger.info("Loading hotel data")
hotel_data_file = "hotelsNodeData/hotel_data_primary.json"

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

# --- flight data ---
event_logger.info("Loading flight data")
flights_data_file = "hotelsNodeData/flights_data_secondary.json"

if os.path.exists(flights_data_file):
    event_logger.info("Flight data file exists")
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
# --- end flight data ---

def prepare_commit(hotel_request, departure_request, return_request, request_id):
    hotel_name = hotel_request.get('name', '')
    week_number = hotel_request.get('week', '')
    event_logger.info("hotel name: %s" %(hotel_name))
    event_logger.info("week number: %s" %(week_number))

    departure_flight_number = departure_request.get('flight_number', '')
    return_flight_number = return_request.get('flight_number', '')
    event_logger.info("departure flight number: %s" %(departure_flight_number))
    event_logger.info("return flight number: %s" %(return_flight_number))

    hotel_committed = commit_book_hotel(hotel_name, week_number)
    flights_committed = commit_book_flights(departure_flight_number, return_flight_number)

    # TODO should also check that the state array does not have the to be reserved data already in processing state
    if not(hotel_committed and flights_committed):
        return False

    hotel_info = {"name": hotel_name, "week_number": week_number}
    update_state_array(request_id, hotel_info, "processing", state_array)
    return True

def commit(hotel_request, departure_request, return_request, request_id):
    hotel_name = hotel_request.get('name', '')
    week_number = hotel_request.get('week', '')
    event_logger.info("hotel name: %s" %(hotel_name))
    event_logger.info("week number: %s" %(week_number))

    departure_flight_number = departure_request.get('flight_number', '')
    return_flight_number = return_request.get('flight_number', '')
    event_logger.info("departure flight number: %s" %(departure_flight_number))
    event_logger.info("return flight number: %s" %(return_flight_number))

    hotel_reservation_OK, hotel_status_msg = book_hotel(hotel_name, week_number)
    event_logger.info("hotel reservation status: %s" %(hotel_status_msg))
    flight_reservation_OK, flight_status_msg = book_flights(departure_request, return_request)
    event_logger.info("flight reservation status: %s" %(flight_status_msg))
    reservation_OK = hotel_reservation_OK and flight_reservation_OK

    if not(reservation_OK):
        return False

    hotel_info = {"name": hotel_name, "week_number": week_number}
    update_state_array(request_id, hotel_info, "done", state_array)
    return True

def abort(hotel_request, departure_request, return_request, request_id):
    # TODO should remove reservations from file if it was already updated
    cancel_hotel(hotel_request)
    cancel_flights(departure_request, return_request)
    hotel_info = {"name": '', "week_number": ''}
    update_state_array(request_id, hotel_info, "aborted", state_array)
    return True

def handle_request(hotel_request, departure_request, return_request, request_id):
    
    flights_server = ServerProxy('http://localhost:8001')
    
    event_logger.info("hotel request data:")
    event_logger.info(hotel_request)

    event_logger.info("flight request data:")
    event_logger.info(departure_request)
    event_logger.info(return_request)

    hotel_name = hotel_request.get('name', '')
    week_number = hotel_request.get('week', '')
    event_logger.info("hotel name: %s" %(hotel_name))
    event_logger.info("week number: %s" %(week_number))

    departure_flight_number = departure_request.get('flight_number', '')
    return_flight_number = return_request.get('flight_number', '')
    event_logger.info("departure flight number: %s" %(departure_flight_number))
    event_logger.info("return flight number: %s" %(return_flight_number))

    # STEP 2: hotels node sends prepare commit request to flights node

    flights_server_prepared  = flights_server.prepare_commit(hotel_request, departure_request, return_request, request_id)
    event_logger.info("flights server prepared: %s" %(flights_server_prepared))
    
    # STEP 4: if flights node can't commit, abort reservation in both nodes
    # and return False to coordinator node
    if not flights_server_prepared:
        abort(hotel_request, departure_request, return_request, request_id)
        flights_server.abort(hotel_request, departure_request, return_request, request_id)
        return False
    
    # STEP 5: if flights node committed, hotels node will write processing data to it's state array 

    hotel_info = {"name": hotel_name, "week_number": week_number}
    update_state_array(request_id, hotel_info, "processing", state_array)

    # STEP 6: hotels node will try to commit the reservation
    hotel_reservation_OK, hotel_status_msg = book_hotel(hotel_name, week_number)
    event_logger.info("hotel reservation status: %s" %(hotel_status_msg))
    flight_reservation_OK, flight_status_msg = book_flights(departure_request, return_request)
    event_logger.info("flight reservation status: %s" %(flight_status_msg))
    reservation_OK = hotel_reservation_OK and flight_reservation_OK
    
    # STEP 7: if hotels node can't commit, abort reservation in both nodes
    if not(reservation_OK):
        abort(hotel_request, departure_request, return_request, request_id)
        flights_server.abort(hotel_request, departure_request, return_request, request_id)
        return False

    # STEP 8: if hotels node committed, hotels node will ask flights node to also commit
    flights_server_committed = flights_server.commit(hotel_request, departure_request, return_request, request_id)
    
    # STEP 10: if flights node can't commit, abort reservation in both nodes
    if not flights_server_committed:
        abort(hotel_request, departure_request, return_request, request_id)
        flights_server.abort(hotel_request, departure_request, return_request, request_id)
        return False

    # STEP 11: if flights node committed, hotels node will write done data to it's state array and return true to coordinator node
    status_msg = hotel_status_msg + " & " + flight_status_msg
    event_logger.info("reservation status: %s" %(status_msg))

    transaction_logger.info("id=%s, status=%s" %(request_id, reservation_OK))

    hotel_info = {"name": '', "week_number": ''}
    update_state_array(request_id, hotel_info, "done", state_array)

    return reservation_OK

def commit_book_hotel(hotel_name, week_number):

    hotel_reservation_can_be_made = False

    if hotel_name in hotel_data:
        week_number = int(week_number)
        if week_number in hotel_data[hotel_name]["free_weeks"]:
            hotel_data[hotel_name]["free_weeks"].remove(week_number)
            hotel_data[hotel_name]["reserved_weeks"].append(week_number)
            hotel_reservation_can_be_made = True
        else:
            hotel_reservation_can_be_made = False
    else:
        hotel_reservation_can_be_made = False
    
    return hotel_reservation_can_be_made

def commit_book_flights(departure_flight_number, return_flight_number):

    flights_reservation_can_be_made = False

    if any(flight["flight_number"] == departure_flight_number for flight in flights_data["flights"]) and any(flight["flight_number"] == return_flight_number for flight in flights_data["flights"]):
        departure_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
        return_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)

        if int(departure_flight["reserved_seats"]) < int(departure_flight["total_seats"]):
            departure_flight["reserved_seats"] += 1
        else:
            flights_reservation_can_be_made = False
            return flights_reservation_can_be_made

        if return_flight["reserved_seats"] < return_flight["total_seats"]:
            return_flight["reserved_seats"] += 1
        else:
            flights_reservation_can_be_made = False
            return flights_reservation_can_be_made

        flights_reservation_can_be_made = True
        return flights_reservation_can_be_made
    
    else:
        flights_reservation_can_be_made = False
        return flights_reservation_can_be_made

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

def cancel_hotel(hotel_request):
    hotel_name = hotel_request.get("name", "")
    week_number = hotel_request.get("week", "")
            
    hotel_data[hotel_name]["free_weeks"].append(week_number)
    hotel_data[hotel_name]["reserved_weeks"].remove(week_number)
    save_hotel_data()

def book_flights(departure_flight_number, return_flight_number):

    flights_reservation_OK = False
    status_msg = ''

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

def cancel_flights(departure_request, return_request):
    departure_flight_number = departure_request.get("flight_number", "")
    return_flight_number = return_request.get("flight_number", "")

    departure_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
    return_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)

    departure_flight["reserved_seats"] -= 1
    return_flight["reserved_seats"] -= 1
    save_flight_data()


# start server
hotel_server = SimpleXMLRPCServer(('localhost', 8002), logRequests=True)

hotel_server.register_function(handle_request, 'handle_request')
hotel_server.register_function(prepare_commit, 'prepare_commit')
hotel_server.register_function(commit, 'commit')
hotel_server.register_function(abort, 'abort')

event_logger.info("Hotel server is ready to accept requests.")
hotel_server.serve_forever()