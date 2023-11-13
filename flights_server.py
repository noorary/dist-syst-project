from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import loads

def book_flights(departure_request, return_request):
    print('starting flights server')
    # departure_data, method = loads(departure_request)
    # return_data, method = loads(return_request)

    print("flight request data:")
    print(departure_request)
    print(return_request)

    return True

validator_server = SimpleXMLRPCServer(('localhost', 8001), logRequests=True)

validator_server.register_function(book_flights, 'book_flights')

print("Flights server is ready to accept requests.")
validator_server.serve_forever()