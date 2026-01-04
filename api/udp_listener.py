"""Background UDP listener used for development.

This module exposes `start_udp_listener_in_thread` which starts a daemon
thread that binds a UDP socket and writes incoming messages to a log file.
The AppConfig in `api.apps` starts this automatically when `manage.py runserver`
is used (and only in the runserver child process to avoid duplicate starts).
"""
from datetime import datetime
from pathlib import Path
import threading
import socket
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def start_udp_listener_in_thread(ip: str = '0.0.0.0', port: int = 12345, bufsize: int = 1024, logfile: str | None = None):
    """Start a background daemon thread that listens for UDP datagrams.

    The thread appends UTF-8 messages to `esp32_log.txt` by default (under
    `settings.BASE_DIR` if available) and logs events via the Django logger.
    Returns the Thread object (already started).
    """

    if logfile is None:
        if hasattr(settings, 'BASE_DIR') and settings.BASE_DIR:
            logfile_path = Path(settings.BASE_DIR) / 'esp32_log.txt'
        else:
            logfile_path = Path('esp32_log.txt')
    else:
        logfile_path = Path(logfile)

    logfile_path.parent.mkdir(parents=True, exist_ok=True)

    def _run():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((ip, port))
        except Exception:
            logger.exception('Failed to bind UDP socket to %s:%s', ip, port)
            return

        logger.info('UDP listener started on %s:%s', ip, port)

        try:
            with logfile_path.open('a', encoding='utf-8') as f:
                while True:
                    try:
                        data, addr = sock.recvfrom(bufsize)
                    except OSError:
                        # Socket closed or interrupted
                        break

                    ts = datetime.utcnow().isoformat() + 'Z'
                    try:
                        message = data.decode('utf-8')
                        line = f"{ts} {addr[0]}:{addr[1]} {message}\n"
                        logger.info('Received from %s: %s', addr, message)
                        f.write(line)
                        f.flush()
                    except UnicodeDecodeError:
                        logger.info('Received non-text data from %s', addr)
                        hexpreview = data[:64].hex()
                        f.write(f"{ts} {addr[0]}:{addr[1]} <binary:{hexpreview}>\n")
                        f.flush()
        except Exception:
            logger.exception('UDP listener terminated unexpectedly')
        finally:
            try:
                sock.close()
            except Exception:
                pass

    t = threading.Thread(target=_run, daemon=True, name='udp_listener')
    t.start()
    return t
