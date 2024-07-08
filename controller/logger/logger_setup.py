import logging
from datetime import datetime
import os

def setup_logger(name, level=logging.INFO):
        
    """Function setup as many loggers as you want"""
    # Create logs directory if it doesn't exist
    script_dir = os.path.dirname(__file__)
    log_dir =os.path.abspath(os.path.join(script_dir, '..', 'logs'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a custom logger
    logger = logging.getLogger(name)
    
    # Set the log level
    logger.setLevel(level)
    
    # Create a handler that rotates every day
    #log_file = datetime.now().strftime('log-rsi-%Y%m%d.log')
    log_file = os.path.join(log_dir, datetime.now().strftime('log-rsi-%Y%m%d.log'))
    try:
        file_handler = logging.FileHandler(log_file)
    except Exception as e:
        print(f"Failed to create log file handler: {e}")
        raise

    # Set the log level for the file handler
    file_handler.setLevel(level)
    
    # Create a formatter and add it to the file handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add the file handler to the logger
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger('my_logger')
