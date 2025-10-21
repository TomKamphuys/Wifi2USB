#!/usr/bin/env python

import asyncio
import sys
import socket

from websockets.asyncio.server import serve
from client_connection import GrblStreamerClientConnection


# Global GRBL connection - created once when server starts
grbl_connection = None


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
        print("ERROR: GRBL connection not initialized", file=sys.stderr)
        await websocket.close(1011, "GRBL connection unavailable")
        return
    
    try:
        async for message in websocket:
            print(f"Received from websocket: {message}")
            
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
                print(f"Sending to websocket: {response}")
                await websocket.send(response)
            else:
                print("No response received from GrblStreamer")
    except Exception as e:
        print(f"Error in websocket handler: {e}", file=sys.stderr)
    finally:
        print("Websocket connection closed")


async def main():
    global grbl_connection
    
    # Initialize GRBL connection once at startup
    try:
        print("Initializing GRBL connection...")
        grbl_connection = GrblStreamerClientConnection()
        print("GRBL connection established successfully")
    except Exception as e:
        print(f"FATAL: Failed to initialize GRBL connection: {e}", file=sys.stderr)
        print("Please ensure:")
        print("  1. COM5 is the correct port")
        print("  2. No other application is using COM5")
        print("  3. You have permissions to access the serial port")
        print("  4. The GRBL device is connected and powered on")
        sys.exit(1)
    
    # Find an available port
    preferred_port = 8001
    available_port = find_available_port(preferred_port)
    
    if available_port is None:
        print(f"FATAL: Could not find an available port starting from {preferred_port}", file=sys.stderr)
        print(f"Please close other applications or manually specify a different port")
        if grbl_connection:
            grbl_connection.close()
        sys.exit(1)
    
    if available_port != preferred_port:
        print(f"WARNING: Port {preferred_port} is in use. Using port {available_port} instead.")
    
    try:
        # Start websocket server
        async with serve(handler, "", available_port) as server:
            print(f"WebSocket server started on port {available_port}")
            print(f"Connect to: ws://localhost:{available_port}")
            await server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"ERROR: Server error: {e}", file=sys.stderr)
    finally:
        # Clean up GRBL connection on shutdown
        if grbl_connection:
            print("Closing GRBL connection...")
            grbl_connection.close()
            print("GRBL connection closed")


if __name__ == "__main__":
    asyncio.run(main())