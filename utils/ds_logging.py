import logging
from logging.handlers import RotatingFileHandler

def get_event_logger(logger_name):
    # Init root and own logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(logger_name)
    logger.propagate = False

    ## Events to output stream
    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    return logger


def get_transaction_logger(logger_name):
    # Init root and own logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(logger_name)
    logger.propagate = False

    ## transactions to output stream and file 
    ## Stream to console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    ## File 
    log_file = "%s_transactions.log" %(logger_name)
    max_bytes = 10 * 1024 * 1024  # 10 MB
    backup_count = 3
    file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)

    formatter = logging.Formatter("%(asctime)s - TRANSACTION - %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger