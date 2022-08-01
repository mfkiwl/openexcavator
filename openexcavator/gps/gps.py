from collections import deque
import datetime
import logging
from queue import Queue
from typing import Callable

from gps.ntrip_client import NTRIPClient


class GPSHandler:
    def __init__(self, config):
        self.threads = []
        self.__data_func = self.__parse_data_func(config)

    def get_data(self):
        """
        Get the current GPS data.
        :returns: dict with: ts, lat, lng, speed, acc, alt, fix
        """
        return self.__data_func()

    def __parse_data_func(self, config) -> Callable:
        """
        Parse a GPS data function with no parameters and and return it.
        :returns: function that return dict with gps data.
        """
        if config["gps_type"] == "Reach":
            from reach.gps import ReachGPS

            gps_queue = deque(maxlen=1)
            reach_gps = ReachGPS(config["gps_host"], int(config["gps_port"]), gps_queue)
            reach_gps.start()
            self.threads.append(reach_gps)
            return lambda: gps_queue[-1]

        if config["gps_type"] == "Simulator":
            # from gps.simulator import SimulatorGPS
            #
            # simulator_gps = SimulatorGPS(config["gps_host"], int(config["gps_port"]))
            # return lambda: simulator_gps.get_data()
            return NotImplementedError

        if config["gps_type"] == "FIXED":
            return lambda: {
                "ts": datetime.datetime.utcnow(),
                "lat": 0,
                "lng": 0,
                "speed": 0,
                "acc": 0,
                "alt": 0,
                "fix": 3,
            }

        if config["gps_type"] == "UBX":
            from gps.ubx import UBX

            gps_queue = deque(maxlen=1)
            ntrip_queue = Queue()
            ntrip_client = NTRIPClient(config, ntrip_queue)
            ntrip_client.start()
            ubx_gps = UBX(gps_queue, ntrip_queue=ntrip_queue)
            ubx_gps.start()
            self.threads.append(ubx_gps)
            return lambda: gps_queue[-1]

        return NotImplementedError

    def disconnect_source(self):
        for thread in self.threads:
            if hasattr(thread, "disconnect_source"):
                thread.disconnect_source()

    def stop(self):
        """Stop GPS threads if they are running."""
        if len(self.threads) == 0:
            return

        for thread in self.threads:
            thread.stop()
        self.threads = []
        logging.info("GPS threads stopped")
        return True
