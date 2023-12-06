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
