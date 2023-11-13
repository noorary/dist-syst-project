from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import loads

def book_hotel(xml_hotel_request):

    print("hotel request data:")
    print(xml_hotel_request)

    return False

validator_server = SimpleXMLRPCServer(('localhost', 8002), logRequests=True)

validator_server.register_function(book_hotel, 'book_hotel')

print("Hotel server is ready to accept requests.")
validator_server.serve_forever()