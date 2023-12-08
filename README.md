# Distributed Systems course project repository, autumn 2023

[Course page](https://studies.helsinki.fi/kurssit/toteutus/hy-opt-cur-2324-b8ec1422-835b-4bdb-bd2c-25df506de0f8)

## First version can be run as follows


**NOTE** It is critical to start coordinator server first. Otherwise node discovery do not work
--- 
1. run `python3 coordinator_server.py`
2. run `python3 flights_server.py`
3. run `python3 hotels_server.py`
4. when all three servers are running, you can test code by running client `python3 client.py`

## Logging practicalities

There is two loggers available:
- Event logger for events, print outs etc
- Transaction logger for "official" state of the system

Get event logger with statement ```event_logger = ds_logging.get_event_logger("coordinator.events")```. And use with ```event_logger.info("This is log message")```.

Transaction logger logs messages to console and file. Get transaction logger with ```transaction_logger = ds_logging.get_transaction_logger("coordinator")```. That creates log file in same director with name ```<LOGGER_NAME>_transactions.log```. 

## How run this in cs.helsinki.fi servers

- coordinator will run on server svm-11.cs.helsinki.fi (128.214.11.91)
- hotels reservation will run on server svm-11-2.cs.helsinki.fi (128.214.9.25)
- flights reservation will run on server svm-11-3.helsinki.fi (128.214.9.26)
- client can run any of the nodes 

That configuration requires following changes in code level:
- coordinator [flights_server](https://github.com/noorary/dist-syst-project/blob/main/coordinator_server.py#L67) and [hotels_serve](https://github.com/noorary/dist-syst-project/blob/main/coordinator_server.py#L68) needs to point correct server IP and port (use 8000)
- hotels [reservation secondary](https://github.com/noorary/dist-syst-project/blob/main/hotels_server.py#L192) needs to point to correct server IP and port (use 8000)
- flights [reservation secondary](https://github.com/noorary/dist-syst-project/blob/main/flights_server.py#L193) needs to point to correct server IP and port (use 8000)
- [client2 needs to point](https://github.com/noorary/dist-syst-project/blob/main/client2.py#L31) to coordinator server IP and port. For [client](https://github.com/noorary/dist-syst-project/blob/main/client.py) server IP and port can be given as command line arguments using -H for host and -P for port.

After changes nodes can be started on each server with commands 
- coordinator `python3 coordinator_server.py -H 128.214.11.91 -P 8000`
- hotels reservation `python3 hotels_server.py -H 128.214.9.25 -P8000`
- flights reservation `python3 hotels_server.py -H 128.214.9.26 -P 8000`

If system is run some where else needed code changes are same and just IPs are different.  
