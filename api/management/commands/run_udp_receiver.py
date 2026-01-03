from django.core.management.base import BaseCommand, CommandError
from datetime import datetime
from pathlib import Path
import socket
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run UDP receiver to listen for ESP32 messages and append to a log file."

    def add_arguments(self, parser):
        parser.add_argument('--ip', default='0.0.0.0', help='IP to bind to (default: 0.0.0.0)')
        parser.add_argument('--port', type=int, default=12345, help='UDP port to bind to (default: 12345)')
        parser.add_argument('--buffer', type=int, default=1024, help='Receive buffer size in bytes (default: 1024)')
        parser.add_argument('--logfile', default=None, help='Path to log file (default: <project root>/esp32_log.txt)')

    def handle(self, *args, **options):
        ip = options['ip']
        port = options['port']
        bufsize = options['buffer']
        logfile = options['logfile']

        # Default logfile path: project BASE_DIR if available, otherwise current working dir
        if logfile is None:
            if hasattr(settings, 'BASE_DIR') and settings.BASE_DIR:
                logfile = Path(settings.BASE_DIR) / 'esp32_log.txt'
            else:
                logfile = Path('esp32_log.txt')
        else:
            logfile = Path(logfile)

        logfile.parent.mkdir(parents=True, exist_ok=True)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((ip, port))
        except Exception as e:
            raise CommandError(f"Failed to bind UDP socket to {ip}:{port}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Server started! Listening on {ip}:{port}"))
        self.stdout.write("Waiting for ESP32... (Ctrl-C to stop)")

        try:
            with logfile.open('a', encoding='utf-8') as f:
                while True:
                    data, addr = sock.recvfrom(bufsize)
                    ts = datetime.utcnow().isoformat() + 'Z'
                    try:
                        message = data.decode('utf-8')
                        line = f"{ts} {addr[0]}:{addr[1]} {message}\n"
                        self.stdout.write(f"Received from {addr}: {message}")
                        f.write(line)
                        f.flush()
                    except UnicodeDecodeError:
                        self.stdout.write(f"Received non-text data from {addr}")
                        # Log as hex for debugging
                        try:
                            hexpreview = data[:64].hex()
                            f.write(f"{ts} {addr[0]}:{addr[1]} <binary:{hexpreview}>\n")
                            f.flush()
                        except Exception:
                            pass
        except KeyboardInterrupt:
            self.stdout.write("\nServer stopped by user.")
        finally:
            sock.close()
