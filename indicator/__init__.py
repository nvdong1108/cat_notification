import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from logger.logger_setup import logger
#from ..logger.logger_setup import logger

logger.info('This is an info message from file1')