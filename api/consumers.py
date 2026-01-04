import logging
from datetime import datetime
from pathlib import Path
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class ESP32Consumer(AsyncWebsocketConsumer):
    """Simple WebSocket consumer that logs incoming text messages to esp32_log.txt

    URL (example): ws://<host>/ws/esp32/
    """

    async def connect(self):
        await self.accept()
        logger.info('WebSocket connection accepted from %s', self.scope.get('client'))

    async def disconnect(self, close_code):
        logger.info('WebSocket disconnected: %s', close_code)

    async def receive(self, text_data=None, bytes_data=None):
        ts = datetime.utcnow().isoformat() + 'Z'

        if text_data is None and bytes_data is None:
            return

        # Choose logfile path
        if hasattr(settings, 'BASE_DIR') and settings.BASE_DIR:
            logfile_path = Path(settings.BASE_DIR) / 'esp32_log.txt'
        else:
            logfile_path = Path('esp32_log.txt')

        try:
            logfile_path.parent.mkdir(parents=True, exist_ok=True)
            with logfile_path.open('a', encoding='utf-8') as f:
                if text_data is not None:
                    client = self.scope.get('client')
                    client_addr = f"{client[0]}:{client[1]}" if client else 'unknown'
                    line = f"{ts} {client_addr} {text_data}\n"
                    logger.info('WS Received from %s: %s', client_addr, text_data)
                    f.write(line)
                    f.flush()
                else:
                    # write binary preview
                    hexpreview = bytes_data[:64].hex()
                    client = self.scope.get('client')
                    client_addr = f"{client[0]}:{client[1]}" if client else 'unknown'
                    f.write(f"{ts} {client_addr} <binary:{hexpreview}>\n")
                    f.flush()
        except Exception:
            logger.exception('Failed to log WebSocket message')

        # Optional: echo back a short acknowledgement
        try:
            await self.send(text_data='ACK')
        except Exception:
            logger.exception('Failed to send ACK')
