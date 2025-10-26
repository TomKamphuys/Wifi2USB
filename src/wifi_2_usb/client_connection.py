from abc import ABC, abstractmethod
import time

from loguru import logger
from grbl_streamer import GrblStreamer


class IClientConnection(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        pass

    def receive(self) -> str:
        pass

    def close(self) -> None:
        pass


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
        grbl_streamer.cnect('/dev/ttyUSB0', 115200)
        time.sleep(3)
        grbl_streamer.incremental_streaming = True
        self._grbl_streamer = grbl_streamer
        logger.info('GrblStreamerClientConnection: Connected')

    def send(self, message: str) -> None:
        logger.info(f'GrblStreamerClientConnection: Sending message: {message}')
        self._grbl_streamer.send_immediately(message)

    def receive(self):
        message = self._received_message
        self._received_message = ''
        return message

    def close(self) -> None:
        self._grbl_streamer.disconnect()
