import logging
from config import LOG_PATH

def logger():
    # Create and configure logger
    logging.basicConfig(filename=LOG_PATH /'logs.log',
                    format='%(asctime)s %(message)s',
                    filemode='w') 
    # Creating an object
    logger = logging.getLogger() 
    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)
    return logger
 