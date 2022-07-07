from base64 import b64encode
import logging
from queue import Queue
import socket
import threading
from pyubx2 import UBXReader, RTCM3_PROTOCOL

# Timeout in seconds before stopping ntrip connection
TIMEOUT = 10
USERAGENT = "openexcavator NTRIP client"
NTRIP_VERSION = 2.0

class NTRIPClient(threading.Thread):

    def __init__(self, config, queue: Queue):
        """
        Initialize the ntrip client.
        """
        super().__init__(daemon=True)
        self.queue = queue
        self.update_config(config)
        
    def update_config(self, config):
        self.server = config["ntrip_host"]
        self.port = int(config["ntrip_port"])
        self.mountpoint = config["ntrip_mountpoint"]
        self.user = config["ntrip_user"]
        self.password = config["ntrip_password"]

    def run(self):
        """
        Opens socket to NTRIP server and reads incoming data.
        """
        if self.server == "" or self.port == 0 or self.mountpoint == "":
            logging.warning("NTRIP client not configured...")
            return
        
        # Configuration is valid, now start ntrip connection
        self.running = True
        try:
            with socket.socket() as sock:
                sock.connect((self.server, self.port))
                b64encoded_user = b64encode(f"{self.user}:{self.password}".encode("utf-8")).decode("utf-8")
                sock.sendall((
                    f"GET /{self.mountpoint} HTTP/1.1\r\n"
                    + f"User-Agent: {USERAGENT}\r\n"
                    + f"Authorization: Basic {b64encoded_user}\r\n"
                    + f"Ntrip-Version: Ntrip/{NTRIP_VERSION}\r\n"
                ).encode("utf-8"))
                sock.settimeout(TIMEOUT)
                
                # UBXreader will wrap socket as SocketStream
                ubr = UBXReader(
                    sock,
                    protfilter=RTCM3_PROTOCOL,
                    #quitonerror=ERR_IGNORE,
                    bufsize=4096,
                )
                
                logging.info("NTRIP client connected to %s:%d/%s", self.server, self.port, self.mountpoint)
                
                while self.running:
                    raw_data, parsed_data = ubr.read()
                    if raw_data is not None:
                        self.queue.put((raw_data, parsed_data))
                    # TODO: sending gga to ntrip server
                    # if self._gga_interval:
                    #     self._send_GGA()
        except (
            socket.gaierror,
            ConnectionRefusedError,
            ConnectionAbortedError,
            ConnectionResetError,
            BrokenPipeError,
            TimeoutError,
        ) as err:
            self.running = False
            print(err)
            
    def stop(self):
        """Set property to stop thread"""
        self.running = False