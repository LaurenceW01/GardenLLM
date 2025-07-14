import logging
from ai_and_sheets_core import initialize_sheet
import os
from dotenv import load_dotenv
import multiprocessing
import signal
import sys
import socket
import time
import traceback
from web import app

# Set up logging with a cleaner format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Create logger instance
logger = logging.getLogger(__name__)

# Reduce logging from other libraries
logging.getLogger('googleapiclient').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('google.auth').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Verify OpenAI API key is loaded
openai_key = os.getenv('OPENAI_API_KEY')
if not openai_key:
    logger.error("No OpenAI API key found in environment!")
else:
    logger.info("OpenAI API key loaded successfully")

# Verify OpenWeather API key is loaded
weather_key = os.getenv('OPENWEATHER_API_KEY')
if not weather_key:
    logger.error("No OpenWeather API key found in environment!")
else:
    logger.info("OpenWeather API key loaded successfully")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

def find_available_port(start_port=5000, max_attempts=10):
    port = start_port
    while port < (start_port + max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"No available ports found between {start_port} and {start_port + max_attempts}")

def run_server():
    pid = os.getpid()
    logger.info(f"Server process started with PID: {pid}")
    
    try:
        port = find_available_port()
        logger.info(f"Using port: {port}")
        
        # Use Flask's built-in development server for WSGI
        app.run(
            host="127.0.0.1",
            port=port,
            debug=False
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def main():
    try:
        main_pid = os.getpid()
        logger.info(f"Main process started with PID: {main_pid}")
        
        # Initialize the sheet first
        logger.info("Initializing sheet...")
        initialize_sheet(start_cli=False)
        logger.info("Sheet initialization complete")

        # Start the server process
        logger.info("Starting server...")
        server_process = multiprocessing.Process(target=run_server)
        server_process.start()
        logger.info(f"Server process ID: {server_process.pid}")

        # Wait a bit for the server to initialize
        time.sleep(2)

        # Weather forecast functionality removed - not needed for web server
        logger.info("Weather forecast display skipped - web server mode")

        try:
            server_process.join()
        except KeyboardInterrupt:
            logger.info("\nShutting down server...")
            server_process.terminate()
            server_process.join(timeout=5)
            if server_process.is_alive():
                logger.warning("Server process did not terminate gracefully, forcing...")
                server_process.kill()
            sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main() 