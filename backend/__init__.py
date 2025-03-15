# Empty __init__.py file to make the directory a package 
import logging

# Configure basic logging settings for the whole package
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
) 