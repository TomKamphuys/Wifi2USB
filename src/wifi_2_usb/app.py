import asyncio
import sys
import socket
from abc import ABC, abstractmethod
import time

from loguru import logger
from websockets.asyncio.server import serve
from grbl_streamer import GrblStreamer

# Configure loguru with file rotation at 10MB
logger.remove()  # Remove default handler
logger.add(
    "wifi2usb.log",
    rotation="10 MB",
    retention=3,  # Keep 3 rotated files
    level="DEBUG"
)
logger.add(sys.stderr, level="ERROR")  # Keep errors in stderr


# Global GRBL connection - created once when server starts
grbl_connection = None

class IClientConnection(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        pass

    @abstractmethod
    def receive(self):
        pass

    @abstractmethod
    def close(self) -> None:
        pass

def is_port_available(port):
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except OSError:
        return False


def find_available_port(preferred_port, max_attempts=10):
    """Find an available port, starting with the preferred port."""
    for i in range(max_attempts):
        port = preferred_port + i
        if is_port_available(port):
            return port
    return None


async def handler(websocket):
    """Handle websocket connections and relay messages to/from GRBL."""
    global grbl_connection
    
    if grbl_connection is None:
        logger.error("GRBL connection not initialized")
        await websocket.close(1011, "GRBL connection unavailable")
        return
    
    try:
        async for message in websocket:
            logger.info(f"Received from websocket: {message.rstrip('\n')}")
            
            # Send message to GrblStreamer
            grbl_connection.send(message)
            
            # Wait for and get response from GrblStreamer
            # Poll for response since receive() is synchronous
            response = None
            for _ in range(10000):  # Try for up to 1 second
                response = grbl_connection.receive()
                if response:
                    break
                await asyncio.sleep(0.01)
            
            # Send response back to websocket client
            if response:
                logger.info(f"Sending to websocket: {response.rstrip('\n')}")
                await websocket.send(response)
            else:
                logger.warning("No response received from GrblStreamer")
    except Exception as e:
        logger.error(f"Error in websocket handler: {e}")
    finally:
        logger.info("Websocket connection closed")


async def main():
    global grbl_connection
    
    # Initialize GRBL connection once at startup
    try:
        logger.info("Initializing GRBL connection...")
        grbl_connection = GrblStreamerClientConnection()
        logger.info("GRBL connection established successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize GRBL connection: {e}")
        sys.exit(1)
    
    # Find an available port
    preferred_port = 8001
    available_port = find_available_port(preferred_port)
    
    if available_port is None:
        logger.critical(f"Could not find an available port starting from {preferred_port}")
        logger.critical(f"Please close other applications or manually specify a different port")
        if grbl_connection:
            grbl_connection.close()
        sys.exit(1)
    
    if available_port != preferred_port:
        logger.warning(f"Port {preferred_port} is in use. Using port {available_port} instead.")
    
    try:
        # Start websocket server
        async with serve(handler, "", available_port) as server:
            logger.info(f"WebSocket server started on port {available_port}")
            logger.info(f"Connect to: ws://localhost:{available_port}")
            await server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Clean up GRBL connection on shutdown
        if grbl_connection:
            logger.info("Closing GRBL connection...")
            grbl_connection.close()
            logger.info("GRBL connection closed")

class GrblStreamerClientConnection(IClientConnection):
    def _on_grbl_event(self, event, *data) -> None:
        if event == "on_rx_buffer_percent":
            self._received_message = 'ok'
        args = []
        for d in data:
            args.append(str(d))
        logger.debug("MY CALLBACK: event={} data={}".format(event.ljust(30), ", ".join(args)))

    def __init__(self) -> None: 
        self._received_message = ''
        grbl_streamer = GrblStreamer(self._on_grbl_event)
        grbl_streamer.setup_logging()
        grbl_streamer.cnect('/dev/GRBLUSB', 115200)
        time.sleep(3)
        grbl_streamer.incremental_streaming = True
        self._grbl_streamer = grbl_streamer
        logger.info('GrblStreamerClientConnection: Connected')

    def send(self, message: str) -> None:
        logger.info(f'GrblStreamerClientConnection: Sending message: {message.rstrip('\n')}')
        self._grbl_streamer.send_immediately(message)

    def receive(self):
        message = self._received_message
        self._received_message = ''
        return message

    def close(self) -> None:
        self._grbl_streamer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
