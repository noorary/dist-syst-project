from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy, loads
import json
import os
import time
import socket
import argparse

import utils.ds_logging as ds_logging

event_logger = ds_logging.get_event_logger("hotelreservation.events")
transaction_logger = ds_logging.get_transaction_logger("hotelreservation")

# TODO add flight data to state array and logic for committing flights
# --- state array ---
# placeholder just shows the data format
state_array = [
    {"request_id": "0",
     "status": "placeholder",
     "hotel": {"name": "Hotel Name Placeholder", "week_number": "1"},
     "flights": {"flight_number": "Flight Number Placeholder", "free_seats_after_reservation": "1"}}
]

def update_state_array(request_id, hotel_info, d_flight_info, r_flight_info, new_state, state_array):
    for item in state_array:
        if item['request_id'] == request_id:
            item['state'] = new_state
            
            if hotel_info:
                item['hotel'] = hotel_info
            
            if d_flight_info or r_flight_info:
                item['flights'] = {"departure": d_flight_info, "return": r_flight_info}
            
            break
    else:
        state_array.append({
            "request_id": request_id,
            "state": new_state,
            "hotel": hotel_info if hotel_info else {},
            "flights": {"departure": d_flight_info, "return": r_flight_info} if d_flight_info or r_flight_info else {}
        })

def contains_hotel_week(state_array, hotel_name, week_number):
    # this is important only when state is processing. If it is done or aborted, then the data in file can be assumed to be updated correctly.
    for item in state_array:
        hotel_info = item.get('hotel')
        if hotel_info and hotel_info.get('name') == hotel_name and hotel_info.get('week') == week_number:
            if (item.get('state') == "processing"):
                return True             
    return False

def contains_full_flight (state_array, flight_number):
    # this is important only when state is processing. If it is done or aborted, then the data in file can be assumed to be updated correctly.
    for item in state_array:
        flight_info = item.get('flights')
        if flight_info and flight_info.get('flight_number') == flight_number and flight_info.get('free_seats_after_reservation') <= 0:
            if (item.get('state') == "processing"):
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

    hotel_committed = commit_book_hotel(hotel_name, week_number, request_id)
    flights_committed = commit_book_flights(departure_flight_number, return_flight_number, request_id)

    event_logger.info("hotel committed: %s" %(hotel_committed))
    event_logger.info("flights committed: %s" %(flights_committed))

    # TODO should also check that the state array does not have the to be reserved data already in processing state
    if not(hotel_committed and flights_committed):
        return False
    
    if (contains_hotel_week(state_array, hotel_name, week_number)):
        return False
    
    if (contains_full_flight(state_array, departure_flight_number) or contains_full_flight(state_array, return_flight_number)):
        return False

    hotel_info = {"name": hotel_name, "week_number": week_number}
    d_free_seats = next((flight["total_seats"] - flight["reserved_seats"] for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
    d_flight_info = {"flight_number": departure_flight_number, "free_seats_after_reservation": d_free_seats - 1}
    r_free_seats = next((flight["total_seats"] - flight["reserved_seats"] for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)
    r_flight_info = {"flight_number": return_flight_number, "free_seats_after_reservation": r_free_seats - 1}
    update_state_array(request_id, hotel_info, d_flight_info, r_flight_info, "processing", state_array)
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
    flight_reservation_OK, flight_status_msg = book_flights(departure_flight_number, return_flight_number)
    event_logger.info("flight reservation status: %s" %(flight_status_msg))
    reservation_OK = hotel_reservation_OK and flight_reservation_OK

    if not(reservation_OK):
        return False

    update_state_array(request_id, None, None, None, "done", state_array)
    return True

def abort(hotel_request, departure_request, return_request, request_id):
    cancel_hotel(hotel_request)
    cancel_flights(departure_request, return_request)

    update_state_array(request_id, None, None, None, "aborted", state_array)
    return True

def handle_request(hotel_request, departure_request, return_request, request_id):
    
    flights_server = ServerProxy('http://localhost:8001')

    flight_server_is_alive = True
    
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
    #flights_server_prepared  = flights_server.prepare_commit(hotel_request, departure_request, return_request, request_id)
    #event_logger.info("flights server prepared: %s" %(flights_server_prepared))

    flights_server_prepared = False

    try:
        socket.setdefaulttimeout(30)
        flights_server_prepared  = flights_server.prepare_commit(hotel_request, departure_request, return_request, request_id)
        event_logger.info("flights server prepared: %s" %(flights_server_prepared))

        # STEP 4: if flights node can't prepare commit, abort reservation in both nodes
        # and return False to coordinator node
        if not flights_server_prepared:
            abort(hotel_request, departure_request, return_request, request_id)
            flights_server.abort(hotel_request, departure_request, return_request, request_id) if flight_server_is_alive else None
            return False
    except Exception as e:
        event_logger.info("flights server is not responding, continuing without it")
        flight_server_is_alive = False

    # STEP 5: if flights node committed, hotels node will write processing data to it's state array 

    hotel_info = {"name": hotel_name, "week_number": week_number}
    d_free_seats = next((flight["total_seats"] - flight["reserved_seats"] for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
    d_flight_info = {"flight_number": departure_flight_number, "free_seats_after_reservation": d_free_seats - 1}
    r_free_seats = next((flight["total_seats"] - flight["reserved_seats"] for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)
    r_flight_info = {"flight_number": return_flight_number, "free_seats_after_reservation": r_free_seats - 1}
    update_state_array(request_id, hotel_info, d_flight_info, r_flight_info, "processing", state_array)

    # STEP 6: hotels node will try to commit the reservation
    hotel_reservation_OK, hotel_status_msg = book_hotel(hotel_name, week_number)
    event_logger.info("hotel reservation status: %s" %(hotel_status_msg))
    flight_reservation_OK, flight_status_msg = book_flights(departure_flight_number, return_flight_number)
    event_logger.info("flight reservation status: %s" %(flight_status_msg))
    reservation_OK = hotel_reservation_OK and flight_reservation_OK
    
    # STEP 7: if hotels node can't commit, abort reservation in both nodes
    if not(reservation_OK):
        abort(hotel_request, departure_request, return_request, request_id)
        flights_server.abort(hotel_request, departure_request, return_request, request_id) if flight_server_is_alive else None
        update_state_array(request_id, None, None, None, "aborted", state_array)
        return False

    # STEP 8: if hotels node committed, hotels node will ask flights node to also commit
    # if flights server is not alive, skip this step
    if (flight_server_is_alive):    
        flights_server_committed = flights_server.commit(hotel_request, departure_request, return_request, request_id)
        event_logger.info("flights server committed: %s" %(flights_server_committed))
        # STEP 10: if flights node can't commit, abort reservation in both nodes
        if not flights_server_committed:
            abort(hotel_request, departure_request, return_request, request_id)
            flights_server.abort(hotel_request, departure_request, return_request, request_id)
            update_state_array(request_id, None, None, None, "aborted", state_array)
            return False

    # STEP 11: if flights node committed, hotels node will write done data to it's state array and return true to coordinator node
    status_msg = hotel_status_msg + " & " + flight_status_msg
    event_logger.info("reservation status: %s" %(status_msg))

    transaction_logger.info("id=%s, status=%s" %(request_id, reservation_OK))

    hotel_info = {"name": '', "week_number": ''}
    update_state_array(request_id, hotel_info, None, None, "done", state_array)

    update_state_array(request_id, None, None, None, "done", state_array)
    return reservation_OK

def commit_book_hotel(hotel_name, week_number, request_id):

    hotel_reservation_can_be_made = False

    if hotel_name in hotel_data:
        week_number = int(week_number)
        if week_number in hotel_data[hotel_name]["free_weeks"]:
            hotel_info = {"name": hotel_name, "week_number": week_number}
            update_state_array(request_id, hotel_info, None, None, "processing", state_array)
            hotel_reservation_can_be_made = True
        else:
            hotel_reservation_can_be_made = False
    else:
        hotel_reservation_can_be_made = False
    
    return hotel_reservation_can_be_made

def commit_book_flights(departure_flight_number, return_flight_number, request_id):

    flights_reservation_can_be_made = False

    if any(flight["flight_number"] == departure_flight_number for flight in flights_data["flights"]) and any(flight["flight_number"] == return_flight_number for flight in flights_data["flights"]):
        departure_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
        return_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)

        if int(departure_flight["reserved_seats"]) < int(departure_flight["total_seats"]):
            flights_reservation_can_be_made = True
        else:
            flights_reservation_can_be_made = False
            return flights_reservation_can_be_made

        if return_flight["reserved_seats"] < return_flight["total_seats"]:
            flights_reservation_can_be_made = True
        else:
            flights_reservation_can_be_made = False
            return flights_reservation_can_be_made

        flights_reservation_can_be_made = True

        d_free_seats = next((flight["total_seats"] - flight["reserved_seats"] for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
        d_flight_info = {"flight_number": departure_flight_number, "free_seats_after_reservation": d_free_seats - 1}
        r_free_seats = next((flight["total_seats"] - flight["reserved_seats"] for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)
        r_flight_info = {"flight_number": return_flight_number, "free_seats_after_reservation": r_free_seats - 1}
        update_state_array(request_id, None, d_flight_info, r_flight_info, "processing", state_array)
        
        return flights_reservation_can_be_made
    
    else:
        flights_reservation_can_be_made = False
        return flights_reservation_can_be_made
prepare_commit
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
            
    hotel_data[hotel_name]["free_weeks"].append(int(week_number))
    if week_number in hotel_data[hotel_name]["reserved_weeks"]:
        hotel_data[hotel_name]["reserved_weeks"].remove(int(week_number))
    save_hotel_data()

def book_flights(departure_flight_number, return_flight_number):

    flights_reservation_OK = False
    status_msg = ''

    if any(flight["flight_number"] == departure_flight_number for flight in flights_data["flights"]) and any(flight["flight_number"] == return_flight_number for flight in flights_data["flights"]):
        departure_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == departure_flight_number), None)
        return_flight = next((flight for flight in flights_data["flights"] if flight["flight_number"] == return_flight_number), None)

        event_logger.info("departure flight: %s" %(departure_flight))
        event_logger.info("return flight: %s" %(return_flight))

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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Hotel booking server for The Booking System")

    parser.add_argument("-H", "--host", type=str, default="localhost", help="Host name (default: localhost)")
    parser.add_argument("-P", "--port", type=int, default=8002, help="Port number (default: 8002)")
    return parser.parse_args()


def announce_presence(host, port):
    UDP_IP = "255.255.255.255"
    UDP_PORT = 12345
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    keep_trying = True 

    while keep_trying:
        message = "Hotel booking server running. host=%s, port=%s" %(host, port)
        event_logger.info(message)
        client_socket.sendto(message.encode(), (UDP_IP, UDP_PORT))
        acknowledgment, server_address = client_socket.recvfrom(1024)
        if acknowledgment.decode().startswith("OK"):
            break
        event_logger.info("Sleep - Announce presence every 5 seconds")
        time.sleep(5)  # Announce presence every 5 seconds

    _, nodes = acknowledgment.decode().split(":")
    messages = nodes.split(";")
    for msg in messages:
        event_logger.info("Reservation node connected: %s" %(msg))
    


def main():
    # start server
    args = parse_arguments()
    host = args.host
    port = args.port    

    announce_presence(host, port)

    hotel_server = SimpleXMLRPCServer((host, port), logRequests=True)

    hotel_server.register_function(handle_request, 'handle_request')
    hotel_server.register_function(prepare_commit, 'prepare_commit')
    hotel_server.register_function(commit, 'commit')
    hotel_server.register_function(abort, 'abort')

    event_logger.info("Hotel server is ready to accept requests.")
    hotel_server.serve_forever()

if __name__ == "__main__":
    main()