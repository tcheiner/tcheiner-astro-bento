
import logging

# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Set global logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(),  # Log to the console
    ],
)

# Create a logger instance
logger = logging.getLogger("my_app")  # Use a unique name for your app logger
