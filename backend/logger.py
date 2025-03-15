import logging
import os
import sys
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure the logger
def setup_logger(name):
    # Create a custom logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler(f'logs/spotify_chat_{datetime.now().strftime("%Y%m%d")}.log')
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.INFO)
    
    # Create formatters and add them to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger 